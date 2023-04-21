from flask import (Flask, render_template, redirect, url_for, session, request, g, jsonify)
from flask_mysqldb import MySQL
from flask_compress import Compress

from keycloak import KeycloakOpenID

from decodeLoRaPackage import decodeMACPayload

from determineThermalComfort import get_pmv_status, get_pmv_value, get_calibrate_clo_value, \
    get_calibrate_air_speed_value
from determineAirTemperature import get_air_temperature
from determineWellBeing import get_well_being_description
from updatePreferences import updateThermalComfortPreference, updateTemperaturePreference, updatePrefElectricVehicle, \
    updatePrefWashingMachine, updatePrefDishWasher, updatePrefWaterHeater, updatePrefTumbleDrier

from getPreferences import getThermalComfortPreferences, getTemperaturePreferences, getFlexibleLoadsPreferences

from collections import defaultdict
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
    session['deviceId'] = keycloak_openid.userinfo(access_token['access_token'])['deviceId']

    return redirect('/')


# A route that implements the logout mechanism
@app.route('/logout')
def logout():
    access_token = session.get('access_token', None)
    keycloak_openid.logout(access_token['refresh_token'])
    session.clear()
    return redirect('/login')


# A functions that implements the 'Dashboard' page under the route '/index/, 'dashboard' and '/'
@app.route("/")
@app.route("/index/")
@app.route("/dashboard/")
def rout():
    # Get the wearable ID from the session's object deviceId
    wearable_id = session.get('deviceId', None)
    # Execute SQL query to get the thermal comfort data regarding the specific wearable ID during the last 24 hours
    g.cur.execute('''SELECT COUNT(tc_temperature) FROM user_thermal_comfort WHERE tc_timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 24 HOUR)) AND wearable_id = %s''', (
        wearable_id,))
    # Fetch all records (data) associated with the specific wearable ID during the last 24 hours
    daily_thermal_comfort_data = g.cur.fetchall()

    return render_template("index.html") if len(daily_thermal_comfort_data) > 0 else render_template("index-empty.html")


# A functions that implements the default 'Thermal Comfort' page under the route '/thermal_comfort/'
@app.route("/thermal_comfort/", methods=['GET', 'POST'])
def thermal_comfort():
    # Get the wearable ID from the session's object deviceId
    wearable_id = session.get('deviceId', None)
    # Execute SQL query to get the thermal comfort data regarding the specific wearable ID during the last 24 hours
    g.cur.execute('''SELECT * FROM user_thermal_comfort WHERE tc_timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 24 HOUR)) AND wearable_id = %s''', (
        wearable_id,))
    # Fetch all records (data) associated with the specific wearable ID during the last 24 hours
    daily_thermal_comfort_data = g.cur.fetchall()

    return render_template("thermal-comfort.html") if len(daily_thermal_comfort_data) > 0 else render_template("thermal-comfort-empty.html")


# A functions that implements the 'Preferences' page under the route '/preferences/'
@app.route("/preferences/", methods=["GET", "POST"])
def preferences():
    return render_template("preferences.html")


# A functions that implements the API service that provides consumer's preferences to CDMP under the route 'api_preferences'
@app.route('/api_tc', methods=['GET'])
def api_tc():
    # Execute SQL query to get the latest environmental parameters of temperature and humidity
    g.cur.execute('''SELECT tc_temperature, tc_humidity, wearable_id, gateway_id, tc_timestamp, wb_index, tc_met FROM user_thermal_comfort WHERE tc_timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 24 HOUR));''')
    latest_data = g.cur.fetchall()
    def create_data_dict(data=None):
        if data is None:
            data = [0, 0, 0, 0, 0, 0, 0]
        return {
            'air_temperature': data[0],
            'globe_temperature': round(data[0] * 0.935,2),
            'relative_humidity': data[1],
            'wearable_id': data[2],
            'gateway_id': data[3],
            'session_met': data[6],
            'clothing_insulation': get_calibrate_clo_value(0.8, data[6]) if data[6] != 0 else 0,
            'air_velocity': get_calibrate_air_speed_value(0.1, data[6]) if data[6] != 0 else 0,
            'voc_index': data[5],
            'voc_index_desc': get_well_being_description(data[5]) if data[5] != 0 else 0,
            'thermal_comfort': get_pmv_value(data[0], 0.935* data[0], data[1], data[6], 0.8, 0.1) if data != [0] * 7 else 0,
            'thermal_comfort_desc': get_pmv_status(get_pmv_value(data[0], 0.935* data[0], data[1], data[6], 0.8, 0.1)) if data != [0] * 7 else 0,
            "timestamp": data[4]
            }

    data_list = [create_data_dict(data) for data in latest_data] if latest_data else [create_data_dict()]

    json_schema = {'data': data_list}
    return jsonify(json_schema)


# A functions that implements the API service that provides consumer's preferences to CDMP under the route 'api_preferences'
@app.route('/api_preferences', methods=['GET'])
def api_preferences():
    # Execute SQL query to retrieve consumer's preferences from the UPAT db
    g.cur.execute('''SELECT * FROM load_weight_simos WHERE weight_timestamp >= UNIX_TIMESTAMP(DATE_ADD(NOW(), INTERVAL -1 MINUTE));''')
    load_weights = g.cur.fetchall()

    return jsonify(0)


@app.route('/ttn-webhook', methods=['POST'])
def handle_ttn_webhook():
    data = request.get_json()

    device_id = data['end_device_ids']['dev_eui']
    gateway_id = data['uplink_message']['rx_metadata'][0]['gateway_ids']['gateway_id']

    re = decodeMACPayload(data["uplink_message"]["frm_payload"])
    tc_temperature, tc_humidity, wb_index, tc_metabolic, tc_timestamp = get_air_temperature(re[0]), re[1], re[2], re[4], \
                                                                        re[3]

    g.cur.execute('''SELECT tc_metabolic, tc_timestamp FROM user_thermal_comfort WHERE wearable_id = %s ORDER BY tc_timestamp DESC LIMIT 1''', (
        device_id,))
    previous_metabolic = g.cur.fetchall()

    p_metabolic, p_time = previous_metabolic[0][0], previous_metabolic[0][1]

    # By the time the device is turned on, the difference between tc_metabolic and p_metabolic will be less than zero
    if (tc_metabolic - p_metabolic) < 0:
        tc_met = 1
    # Calculate the met for the 2nd, 3rd, etc..
    else:
        tc_met = ((tc_metabolic - p_metabolic) * 40) / (tc_timestamp - p_time)
        if tc_met < 1: tc_met = 1
        if tc_met >6: tc_met = 6

    # Execute SQL INSERT statement
    insert_sql = f"INSERT INTO user_thermal_comfort (tc_temperature, tc_humidity, tc_metabolic, tc_met, tc_timestamp, wearable_id, gateway_id, wb_index) VALUES ({tc_temperature}, {tc_humidity}, {tc_metabolic}, {tc_met}, {tc_timestamp}, '{device_id}', '{gateway_id}', '{wb_index}')"

    g.cur.execute(insert_sql)

    mysql.connection.commit()

    g.cur.close()

    return jsonify({'status': 'success'}), 200


# A functions that implements the 'Acount' page under the route '/account/'
@app.route('/account/')
def account():
    return render_template('account.html')


# A functions that implements the 'Helpdesk' page under the route '/helpdesk/'
@app.route('/helpdesk')
def helpdesk():
    return render_template('helpdesk.html')


# A route that implements an asynchronous call to retrieve data related to the thermal comfort
@app.route('/get_data_thermal_comfort/')
def get_data_thermal_comfort():
    query = """
        SELECT tc_temperature, tc_humidity, tc_timestamp, wb_index, tc_met
        FROM user_thermal_comfort
        WHERE tc_timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 24 HOUR))
        AND wearable_id = %s
        LIMIT 10
    """
    with g.cur as cur:
        cur.execute(query, (session.get('userinfo', None)['deviceId'],))
        thermal_comfort_data = cur.fetchall()

    daily_thermal_comfort_data = [(tc_temperature, tc_humidity, tc_timestamp, wb_index, tc_met,
                                   get_pmv_value(tc_temperature, 0.935 * tc_temperature, tc_humidity, tc_met, 0.8, 0.1))
                                  for tc_temperature, tc_humidity, tc_timestamp, wb_index, tc_met in
                                  thermal_comfort_data]

    return jsonify({'daily_thermal_comfort_data': daily_thermal_comfort_data})


# A route that implements an asynchronous call to retrieve data related to the thermal comfort
@app.route('/get_data_preferences')
def get_data_preferences():
    wearable_id = session.get('userinfo', None)['deviceId']

    preferences_thermal_comfort = getThermalComfortPreferences(g.cur, wearable_id)
    preferences_temperature = getTemperaturePreferences(g.cur, wearable_id)
    preferences_flexible_loads = getFlexibleLoadsPreferences(g.cur, wearable_id)

    if preferences_thermal_comfort is not None:
        user_thermal_level_min, user_thermal_level_max = preferences_thermal_comfort
        user_temperature_min, user_temperature_max = preferences_temperature

        response = {
            'preferences': [
                {
                    'thermal_comfort_preferences':
                        {
                            'thermal_comfort_min': user_thermal_level_min,
                            'thermal_comfort_max': user_thermal_level_max
                        },
                    'temperature_preferences':
                        {
                            'temperature_min': user_temperature_min,
                            'temperature_max': user_temperature_max
                        },
                    'flexible_load_preferences':
                        {
                            'importance_electric_vehicle': preferences_flexible_loads[1],
                            'importance_tumble_drier': preferences_flexible_loads[4],
                            'importance_washing_machine': preferences_flexible_loads[7],
                            'importance_dish_washer': preferences_flexible_loads[10],
                            'importance_water_heater': preferences_flexible_loads[13],
                        }
                }
            ]
        }

        return jsonify(response)

    else:

        return jsonify(tuple("1"))


@app.route('/update_preferences_thermal_comfort', methods=['POST'])
def update_preferences_thermal_comfort():
    wearable_id = session.get('userinfo', None)['deviceId']
    user_thermal_level_min = request.form.get('user_thermal_level_min')
    user_thermal_level_max = request.form.get('user_thermal_level_max')

    updateThermalComfortPreference(mysql, g.cur, user_thermal_level_min, user_thermal_level_max, wearable_id)
    return jsonify(success=True)


@app.route('/update_preferences_temperature', methods=['POST'])
def update_preferences_temperature():
    wearable_id = session.get('userinfo', None)['deviceId']
    user_temp_min = request.form.get('user_temp_min')
    user_temp_max = request.form.get('user_temp_max')

    updateTemperaturePreference(mysql, g.cur, user_temp_min, user_temp_max, wearable_id)
    return jsonify(success=True)


@app.route('/update_preferences_importance_electric_vehicle', methods=['POST'])
def update_preferences_importance_electric_vehicle():
    wearable_id = session.get('userinfo', None)['deviceId']
    importance_electric_vehicle = request.form.get('importance_electric_vehicle')

    updatePrefElectricVehicle(mysql, g.cur, importance_electric_vehicle, wearable_id)

    return jsonify(success=True)


@app.route('/update_preferences_importance_washing_machine', methods=['POST'])
def update_preferences_importance_washing_machine():
    wearable_id = session.get('userinfo', None)['deviceId']
    importance_washing_machine = request.form.get('importance_washing_machine')

    updatePrefWashingMachine(mysql, g.cur, importance_washing_machine, wearable_id)

    return jsonify(success=True)


@app.route('/update_preferences_importance_dish_washer', methods=['POST'])
def update_preferences_importance_dish_washer():
    wearable_id = session.get('userinfo', None)['deviceId']
    importance_dish_washer = request.form.get('importance_dish_washer')

    updatePrefDishWasher(mysql, g.cur, importance_dish_washer, wearable_id)

    return jsonify(success=True)


@app.route('/update_preferences_importance_tumble_drier', methods=['POST'])
def update_preferences_importance_tumble_drier():
    wearable_id = session.get('userinfo', None)['deviceId']
    importance_tumble_drier = request.form.get('importance_tumble_drier')

    updatePrefTumbleDrier(mysql, g.cur, importance_tumble_drier, wearable_id)

    return jsonify(success=True)


@app.route('/update_preferences_importance_water_heater', methods=['POST'])
def update_preferences_importance_water_heater():
    wearable_id = session.get('userinfo', None)['deviceId']
    importance_water_heater = request.form.get('importance_water_heater')

    updatePrefWaterHeater(mysql, g.cur, importance_water_heater, wearable_id)

    return jsonify(success=True)


@app.route('/get_data_thermal_comfort_range', methods=['GET'])
def get_data_thermal_comfort_range():
    userinfo = session.get('userinfo', None)

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not start_date or not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date, '%Y-%m-%d').date() + timedelta(days=1)

    start_timestamp = int(time.mktime(start_date.timetuple()))
    end_timestamp = int(time.mktime(end_date.timetuple()))

    g.cur.execute('''SELECT tc_temperature, tc_humidity, tc_timestamp, wb_index, tc_met FROM user_thermal_comfort WHERE tc_timestamp >= %s AND tc_timestamp <= %s AND wearable_id = %s''', (
        start_timestamp, end_timestamp, userinfo['deviceId']))
    thermal_comfort_data = g.cur.fetchall()

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
