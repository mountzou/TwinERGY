from flask import (Flask, render_template, redirect, url_for, session, request, g, jsonify)
from flask_mysqldb import MySQL
from flask_compress import Compress

from keycloak import KeycloakOpenID

from decodeLoRaPackage import decodeMACPayload

from determineThermalComfort import get_pmv_status, get_pmv_value, get_calibrate_clo_value, \
    get_calibrate_air_speed_value
from determineAirTemperature import get_air_temperature
from determineWellBeing import get_well_being_description
from updatePreferences import updateThermalComfortPreference

from datetime import datetime, timedelta
from urllib.parse import urlparse

import json
import requests
import time

import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
Compress(app)

# Credentials to connect with mySQL TwinERGY UPAT database
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB')

# Initialization of MySQL object for the DB hosted on Heroku
mysql = MySQL(app)

# Configure Keycloak client to authenticate user through TwinERGY Identity Server
keycloak_openid = KeycloakOpenID(server_url='https://auth.tec.etra-id.com/auth/',
    client_id='cdt-twinergy',
    realm_name='TwinERGY',
    client_secret_key="secret")
app.secret_key = 'secret'


@app.before_request
def require_login():
    # Define the allowed routes of a non-authenticated user
    allowed_routes = ['login', 'callback', 'static', 'api_tc', 'ttn-webhook']

    # Define the relative paths that bypass the authentication mechanism
    if request.path == '/api_tc' or request.path == '/ttn-webhook':
        return None

    # Redirect non-authenticated user to the 'login' rout
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect(url_for('login'))


@app.before_request
def before_request():
    g.cur = mysql.connection.cursor()


# A route that implements the user authentication process
@app.route('/login')
def login():
    if urlparse(request.base_url).netloc == '127.0.0.1:5000':
        auth_url = keycloak_openid.auth_url(redirect_uri="http://" + urlparse(request.base_url).netloc + "/callback", scope="openid", state="af0ifjsldkj")
    else:
        auth_url = keycloak_openid.auth_url(redirect_uri="https://" + urlparse(request.base_url).netloc + "/callback", scope="openid", state="af0ifjsldkj")

    return redirect(auth_url)


# A function that implements the access token generation for an authenticated user
@app.route('/callback')
def callback():
    code_token = request.args.get('code')

    access_token = keycloak_openid.token(
        grant_type='authorization_code',
        code=code_token,
        redirect_uri=request.base_url)

    session['userinfo'] = keycloak_openid.userinfo(access_token['access_token'])
    session['username'] = keycloak_openid.userinfo(access_token['access_token'])['preferred_username']
    session['access_token'] = access_token

    return redirect('/')


# A route that implements the logout mechanism
@app.route('/logout')
def logout():
    access_token = session.get('access_token', None)
    keycloak_openid.logout(access_token['refresh_token'])
    session.clear()
    return redirect('/login')


# The route for the dashboard page of the Consumer Digital Twin
@app.route("/")
@app.route("/index/")
def rout():
    # Create a userInfo object with information related to the authenticated user's session
    userinfo = session.get('userinfo', None)

    # Execute SQL query to get the values of air temperature and relative humidity during the last 24 hours
    g.cur.execute('''SELECT COUNT(tc_temperature) FROM user_thermal_comfort WHERE tc_timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 24 HOUR)) AND wearable_id = %s''', (
        userinfo['deviceId'],))
    daily_env = g.cur.fetchall()

    return render_template("index.html") if len(daily_env) > 0 else render_template("index-empty.html")


@app.route("/thermal_comfort/", methods=['GET', 'POST'])
def thermal_comfort():
    # Create a userInfo object with information related to the authenticated user's session
    userinfo = session.get('userinfo', None)

    # Execute SQL query to get the values of air temperature and relative humidity during the last 24 hours
    g.cur.execute('''SELECT * FROM user_thermal_comfort WHERE tc_timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 24 HOUR)) AND wearable_id = %s''', (
        userinfo['deviceId'],))
    daily_env = g.cur.fetchall()

    return render_template("thermal-comfort.html") if len(daily_env) > 0 else render_template("thermal-comfort-empty.html")


@app.route("/preferences/", methods=["GET", "POST"])
def preferences():
    return render_template("preferences.html")


@app.route('/api_tc', methods=['GET'])
def api_tc():
    cur = mysql.connection.cursor()

    # Execute SQL query to get the latest environmental parameters of temperature and humidity
    cur.execute('''SELECT tc_temperature, tc_humidity, wearable_id, gateway_id, tc_timestamp, wb_index, tc_met FROM user_thermal_comfort WHERE tc_timestamp >= UNIX_TIMESTAMP(DATE_ADD(NOW(), INTERVAL -1 MINUTE));''')
    latest_env = cur.fetchall()
    # if len(latest_env) > 0:
        # Create a list of dictionaries using a list comprehension
    data_list = [{'air_temperature': item[0],
                  'globe_temperature': round(item[0] * 0.935,2),
                  'relative_humidity': item[1],
                  'wearable_id': item[2],
                  'gateway_id': item[3],
                  'session_met': item[6],
                  'clothing_insulation': get_calibrate_clo_value(0.8, item[6]),
                  'air_velocity': get_calibrate_air_speed_value(0.1, item[6]),
                  'voc_index': item[5],
                  'voc_index_desc': get_well_being_description(item[5]),
                  'thermal_comfort': get_pmv_value(item[0], 0.935 * item[0], item[1], item[6], 0.8, 0.1),
                  'thermal_comfort_desc': get_pmv_status(get_pmv_value(
                      item[0], 0.935 * item[0], item[1], item[6], 0.8, 0.1)),
                  'timestamp': item[4],
                  } for item in latest_env]
    # else:
    #     data_list = [{'air_temperature': 0,
    #                   'globe_temperature': 0,
    #                   'relative_humidity': 0,
    #                   'wearable_id': 0,
    #                   'gateway_id': 0,
    #                   'session_met': 0,
    #                   'clothing_insulation': 0,
    #                   'air_velocity': 0,
    #                   'voc_index': 0,
    #                   'voc_index_desc': 0,
    #                   'thermal_comfort': 0,
    #                   'thermal_comfort_desc': 0,
    #                   'timestamp': 0,
    #                   }]

        # Create a JSON schema from the list of dictionaries
    json_schema = {'data': data_list}

    return jsonify(json_schema)


@app.route('/api_preferences', methods=['GET'])
def api_preferences():
    cur = mysql.connection.cursor()

    # Execute SQL query to get the latest environmental parameters of temperature and humidity
    cur.execute('''SELECT * FROM load_weight_simos WHERE weight_timestamp >= UNIX_TIMESTAMP(DATE_ADD(NOW(), INTERVAL -1 MINUTE));''')
    load_weights = cur.fetchall()

    return jsonify(0)


@app.route('/ttn-webhook', methods=['POST'])
def handle_ttn_webhook():
    data = request.get_json()

    device_id = data['end_device_ids']['dev_eui']
    gateway_id = data['uplink_message']['rx_metadata'][0]['gateway_ids']['gateway_id']

    re = decodeMACPayload(data["uplink_message"]["frm_payload"])
    tc_temperature, tc_humidity, wb_index, tc_metabolic, tc_timestamp = get_air_temperature(re[0]), re[1], re[2], re[4], \
                                                                        re[3]

    # Connect to the database
    cur = mysql.connection.cursor()

    cur.execute('''SELECT tc_metabolic, tc_timestamp FROM user_thermal_comfort WHERE wearable_id = %s ORDER BY tc_timestamp DESC LIMIT 1''', (
        device_id,))
    previous_metabolic = cur.fetchall()

    p_metabolic, p_time = previous_metabolic[0][0], previous_metabolic[0][1]

    # By the time the device is turned on, the difference between tc_metabolic and p_metabolic will be less than zero
    if (tc_metabolic - p_metabolic) < 0:
        tc_met = 1
    # Calculate the met for the 2nd, 3rd, etc..
    else:
        tc_met = ((tc_metabolic - p_metabolic) * 40) / (tc_timestamp - p_time)
        if tc_met < 1: tc_met = 1

    # Execute SQL INSERT statement
    insert_sql = f"INSERT INTO user_thermal_comfort (tc_temperature, tc_humidity, tc_metabolic, tc_met, tc_timestamp, wearable_id, gateway_id, wb_index) VALUES ({tc_temperature}, {tc_humidity}, {tc_metabolic}, {tc_met}, {tc_timestamp}, '{device_id}', '{gateway_id}', '{wb_index}')"

    cur.execute(insert_sql)

    mysql.connection.commit()

    cur.close()

    return jsonify({'status': 'success'}), 200


# A route that implements an page with information related to the current user's session
@app.route('/account')
def account():
    return render_template('account.html')


# A route that implements an page with information related to the current user's session
@app.route('/helpdesk')
def helpdesk():
    return render_template('helpdesk.html')


# A route that implements an asynchronous call to retrieve data related to the thermal comfort
@app.route('/get_data_thermal_comfort')
def get_data_thermal_comfort():
    userinfo = session.get('userinfo', None)

    cur = mysql.connection.cursor()
    cur.execute('''SELECT tc_temperature, tc_humidity, tc_timestamp, wb_index, tc_met FROM user_thermal_comfort WHERE tc_timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 24 HOUR)) AND wearable_id = %s''', (
        userinfo['deviceId'],))
    thermal_comfort_data = cur.fetchall()

    all_thermal_comfort_data = []

    for row in thermal_comfort_data:
        tc_temperature, tc_humidity, tc_timestamp, wb_index, tc_met = row
        pmv = row + (get_pmv_value(tc_temperature, 0.935 * tc_temperature, tc_humidity, tc_met, 0.8, 0.1),)
        all_thermal_comfort_data.append(pmv)

    return jsonify(tuple(all_thermal_comfort_data))


# A route that implements an asynchronous call to retrieve data related to the thermal comfort
@app.route('/get_data_preferences')
def get_data_preferences():
    userinfo = session.get('userinfo', None)

    g.cur.execute('''
        SELECT user_thermal_level_min, user_thermal_level_max
        FROM user_thermal_preferences
        WHERE wearable_id = %s
        ORDER BY user_thermal_timestamp DESC
        LIMIT 1;
    ''', (userinfo['deviceId'],))
    thermal_preferences = g.cur.fetchone()

    if thermal_preferences is not None:
        user_thermal_level_min, user_thermal_level_max = thermal_preferences

        response = {
            'preferences': [
                {
                    'thermal_comfort_preferences':
                        {
                            'thermal_comfort_min': user_thermal_level_min,
                            'thermal_comfort_max': user_thermal_level_max
                        }
                }
            ]
        }

        return jsonify(response)

    else:

        return jsonify(tuple("1"))


@app.route('/update_preferences', methods=['POST'])
def update_preferences():
    wearable_id = session.get('userinfo', None)['deviceId']

    user_thermal_level_min = request.form.get('user_thermal_level_min')
    user_thermal_level_max = request.form.get('user_thermal_level_max')

    updateThermalComfortPreference(mysql, g.cur, user_thermal_level_min, user_thermal_level_max, wearable_id)

    return jsonify(success=True)


@app.route('/get_data_thermal_comfort_range', methods=['GET'])
def get_data_thermal_comfort_range():
    userinfo = session.get('userinfo', None)
    cur = mysql.connection.cursor()

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not start_date or not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date, '%Y-%m-%d').date() + timedelta(days=1)

    start_timestamp = int(time.mktime(start_date.timetuple()))
    end_timestamp = int(time.mktime(end_date.timetuple()))

    cur.execute('''SELECT tc_temperature, tc_humidity, tc_timestamp, wb_index, tc_met FROM user_thermal_comfort WHERE tc_timestamp >= %s AND tc_timestamp <= %s AND wearable_id = %s''', (
        start_timestamp, end_timestamp, userinfo['deviceId']))
    thermal_comfort_data = cur.fetchall()

    thermal_comfort_list = []

    for row in thermal_comfort_data:
        tc_temperature, tc_humidity, tc_timestamp, wb_index, tc_met = row
        pmv = row + (get_pmv_value(tc_temperature, 0.935 * tc_temperature, tc_humidity, tc_met, 0.8, 0.1),)
        thermal_comfort_list.append(pmv)

    return jsonify(tuple(thermal_comfort_list))


@app.route('/monitor_thermal_comfort_cdmp')
def monitor_thermal_comfort_cdmp():
    headers = {"X-API-TOKEN": '8a3cb21d-be27-466d-a797-54fae21a0d8a'}

    url = "https://twinergy.s5labs.eu/api/query/00bb2745-578a-400f-bcef-da04f3a174d4?pageSize=1000"

    response = requests.get(url, headers=headers)

    response1 = response.json()

    return jsonify(response1)


@app.route('/session', methods=['GET'])
def current_session():
    # Return a json object that includes the session data
    return jsonify(dict(session))


if __name__ == "__main__":
    app.run(debug=True)
