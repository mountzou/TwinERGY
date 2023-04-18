from flask import (Flask, render_template, redirect, url_for, session, request, jsonify)
from flask_mysqldb import MySQL

from keycloak import KeycloakOpenID

from decodeLoRaPackage import decodeMACPayload
from determineMetabolic import dailyMetabolic, dailyMetabolicTime
from determineThermalComfort import get_pmv_status, get_pmv_value
from determineAirTemperature import get_air_temperature
from determineWellBeing import get_well_being_description

from datetime import datetime
from urllib.parse import urlparse

import json
import requests

import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

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


# The route for the dashboard page of the Consumer Digital Twin
@app.route("/")
@app.route("/index/")
def rout():
    # Create a userInfo object with information related to the authenticated user's session
    userinfo = session.get('userinfo', None)

    # Create a cursor object to interact with the TwinERGY UPAT database
    cur = mysql.connection.cursor()

    # Execute SQL query to get the values of air temperature and relative humidity during the last 24 hours
    cur.execute('''SELECT tc_temperature, tc_humidity, tc_timestamp, wb_index FROM user_thermal_comfort WHERE tc_timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 24 HOUR)) AND wearable_id = %s''', (
        userinfo['deviceId'],))
    daily_env = cur.fetchall()

    # Execute SQL query to get the values of metabolic rate during the last 24 hours
    cur.execute('''SELECT tc_metabolic, tc_timestamp FROM user_thermal_comfort WHERE tc_timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 24 HOUR)) AND wearable_id = %s''', (
        userinfo['deviceId'],))
    daily_met = cur.fetchall()

    # Check if tuples are empty, in case of an empty tuple assign a single value of -1
    daily_env = daily_env if daily_env else []
    daily_met = daily_met if daily_met else []

    all_tem, all_hum, all_time, all_wb = [get_air_temperature(row[0]) for row in daily_env], [row[1] for row in
                                                                                              daily_env], [
                                             row[2] for row in daily_env], [row[3] for row in daily_env]

    all_times = [datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') for ts in all_time]

    # Determine the latest air temperature and the latest relative humidity
    l_tem, l_hum, l_time = get_air_temperature(daily_env[-1][0]), daily_env[-1][1], datetime.utcfromtimestamp(
        daily_env[-1][2]).strftime('%Y-%m-%d %H:%M:%S')

    # Determine the latest metabolic rate
    l_met = dailyMetabolic(daily_met)[0]

    # Determine the latest PMV value and the corresponding status
    l_pmv = get_pmv_value(l_tem, 0.935 * l_tem + 1.709, l_hum, l_met, 0.8, 0.1)
    d_pmv = get_pmv_status(l_pmv)

    return render_template("index.html", daily_env=daily_env, all_tem=all_tem, all_hum=all_hum, all_wb=all_wb, l_wb=
    all_wb[-1], all_times=all_times, l_met=l_met, l_pmv=l_pmv, d_pmv=d_pmv, usernameId=session[
        'username']) if len(daily_env) > 0 else render_template("index-empty.html", usernameId=session['username'])


@app.route("/thermal_comfort/")
def thermal_comfort():
    cur = mysql.connection.cursor()

    # Execute SQL query to get the average environmental parameters of temperature and humidity that recorded during the last 24-hours
    cur.execute('''SELECT ROUND(AVG(tc_temperature),2), ROUND(AVG(tc_humidity), 2) FROM user_thermal_comfort WHERE tc_timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 24 HOUR))''')
    (avg_temperature, avg_humidity) = cur.fetchone()

    # Execute SQL query to get the latest environmental parameters of temperature and humidity
    cur.execute('''SELECT tc_temperature, tc_humidity FROM user_thermal_comfort ORDER BY tc_timestamp DESC LIMIT 1;''')
    (latest_temperature, latest_humidity) = cur.fetchone()

    # Execute SQL query to get the daily environmental parameters of temperature and humidity
    cur.execute('''SELECT tc_temperature, tc_humidity, tc_timestamp FROM user_thermal_comfort WHERE tc_timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 24 HOUR));''')
    daily_environmental = cur.fetchall()

    # Execute SQL query to get the daily physiological parameter of metabolic rate
    cur.execute('''SELECT tc_metabolic, tc_timestamp FROM user_thermal_comfort WHERE tc_timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 24 HOUR));''')
    daily_metabolic = cur.fetchall()

    # Determine the latest and average air temperature from corresponding wearable measurements
    latest_temperature, avg_temperature = get_air_temperature(latest_temperature), get_air_temperature(avg_temperature)

    sessions_met = [item for item in dailyMetabolic(daily_metabolic) for _ in range(2)]
    sessions_met_time = dailyMetabolicTime(daily_metabolic)

    avg_met = round(sum(sessions_met) / len(sessions_met), 2)

    daily_temp = [get_air_temperature(t[0]) for t in daily_environmental]
    daily_hum = [t[1] for t in daily_environmental]
    daily_time = [t[2] for t in daily_environmental]

    for ts, te, met in zip(sessions_met_time, sessions_met_time[1:], sessions_met[:-1]):
        cur.execute('''SELECT AVG(tc_temperature) AS avg_temperature, AVG(tc_humidity) AS avg_humidity FROM user_thermal_comfort WHERE tc_timestamp BETWEEN %s AND %s;''', (
            ts, te))
        tc_parameters = cur.fetchall()

        pmv = get_pmv_value(get_air_temperature(tc_parameters[0][0]), 0.935 * get_air_temperature(
            tc_parameters[0][0]) + 1.709, tc_parameters[0][1], met, 0.8, 0.1)

    daily_time = [datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') for ts in daily_time]
    sessions_met_time = [datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') for ts in sessions_met_time]

    return render_template("thermal-comfort.html", avg_met=avg_met, l_temp=latest_temperature, l_hum=latest_humidity, l_met=
    sessions_met[
        -1], avg_temp=avg_temperature, avg_hum=avg_humidity, d_temp=daily_temp, d_hum=daily_hum, d_time=daily_time, d_met=sessions_met, d_met_time=sessions_met_time, l_update=
    daily_time[-1], usernameId=session['username'])


@app.route('/login')
def login():
    if urlparse(request.base_url).netloc == '127.0.0.1:5000':
        auth_url = keycloak_openid.auth_url(redirect_uri="http://" + urlparse(request.base_url).netloc + "/callback", scope="openid", state="af0ifjsldkj")
    else:
        auth_url = keycloak_openid.auth_url(redirect_uri="https://" + urlparse(request.base_url).netloc + "/callback", scope="openid", state="af0ifjsldkj")

    return redirect(auth_url)


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


@app.route("/preferences/", methods=["GET", "POST"])
def preferences():
    from determinePreferences import get_importance_ranges, get_load_weights
    userinfo = session.get('userinfo', None)

    cur = mysql.connection.cursor()

    if request.method == "POST":
        unix_timestamp = (int(datetime.timestamp(datetime.now())))

        importnace_thermal_comfort = request.form.get("preference_thermal_comfort").split(';')

        thermal_dict = {-3: "Cold", -2: "Cool", -1: "Slightly Cool", 0: "Neutral",
                        1: "Slightly Warm", 2: "Warm", 3: "Hot"}

        importance_dict = {1: "Not Important", 2: "Slightly Important", 3: "Important", 4: "Fairly Important",
                           5: "Very Important"}

        thermal_tolerance_list = [k for k, v in thermal_dict.items() if v in importnace_thermal_comfort]

        importnace_ev_range = request.form.get("preference_range_electric_vehicle").split(';')
        importnace_dw_range = request.form.get("preference_range_dish_washer").split(';')
        importnace_wm_range = request.form.get("preference_range_washing_machine").split(';')
        importnace_ht_range = request.form.get("preference_range_drier").split(';')
        importnace_wh_range = request.form.get("preference_range_water_heater").split(';')

        ev_start, ev_end = int(importnace_ev_range[0].split(":")[0]), int(importnace_ev_range[1].split(":")[0])
        dw_start, dw_end = int(importnace_dw_range[0].split(":")[0]), int(importnace_dw_range[1].split(":")[0])
        wm_start, wm_end = int(importnace_wm_range[0].split(":")[0]), int(importnace_wm_range[1].split(":")[0])
        ht_start, ht_end = int(importnace_ht_range[0].split(":")[0]), int(importnace_ht_range[1].split(":")[0])
        wh_start, wh_end = int(importnace_wh_range[0].split(":")[0]), int(importnace_wh_range[1].split(":")[0])

        importance_ev = list(importance_dict.keys())[
                            list(importance_dict.values()).index(request.form.get("preference_electric_vehicle"))] - 1
        importance_dw = list(importance_dict.keys())[
                            list(importance_dict.values()).index(request.form.get("preference_dish_washer"))] - 1
        importance_wm = list(importance_dict.keys())[
                            list(importance_dict.values()).index(request.form.get("preference_washing_machine"))] - 1
        importance_ht = list(importance_dict.keys())[
                            list(importance_dict.values()).index(request.form.get("preference_tumble"))] - 1
        importance_wh = list(importance_dict.keys())[
                            list(importance_dict.values()).index(request.form.get("preference_water_heater"))] - 1

        cur.execute('''INSERT INTO user_pref_thermal VALUES (2, "%s", "%s" , %s, '') ''', (
            thermal_tolerance_list[0], thermal_tolerance_list[1], unix_timestamp))

        cur.execute('''INSERT INTO user_flex_loads VALUES (2, "%s", "%s" , "%s", "%s", "%s", "%s", "%s", "%s" , "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s" ) ''', (
            importance_ev, ev_start, ev_end, importance_ht, ht_start, ht_end, importance_wm, wm_start, wm_end,
            importance_dw, dw_start, dw_end, importance_wh, wh_start, wh_end, unix_timestamp
        ))

        preferences_loads = {"Electric Vehicle": importance_ev + 1, "Dish Washer": importance_dw + 1,
                             "Washing Machine": importance_wm + 1, "Tumble Drier": importance_ht + 1,
                             "Water Heater": importance_wh + 1}

        weights = determineWeights(preferences_loads)

        cur.execute('''INSERT INTO load_weight_simos VALUES (2, "%s", "%s", "%s", "%s", "%s", "%s") ''', (
            float(weights['Electric Vehicle'][0]), float(weights['Tumble Drier'][0]),
            float(weights['Washing Machine'][0]), float(weights['Dish Washer'][0]), float(weights['Water Heater'][0]),
            unix_timestamp
        ))

        mysql.connection.commit()

    preferences_importance, preferences_simos = get_importance_ranges(), get_load_weights()

    return render_template("preferences.html", preferences_importance=preferences_importance, preferences_simos=preferences_simos, usernameId=
    session['username'])


@app.route('/cdmp', methods=['GET'])
def cdmp():
    userinfo = session.get('userinfo', None)

    cur = mysql.connection.cursor()

    # Execute SQL query to get the latest environmental parameters of temperature and humidity
    cur.execute('''SELECT tc_temperature, tc_humidity FROM user_thermal_comfort ORDER BY tc_timestamp DESC LIMIT 1;''')
    (latest_temperature, latest_humidity) = cur.fetchone()

    # Execute SQL query to get the daily physiological parameter of metabolic rate
    cur.execute('''SELECT tc_metabolic, tc_timestamp FROM user_thermal_comfort WHERE tc_timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 24 HOUR));''')
    daily_metabolic = cur.fetchall()

    sessions_met = [item for item in dailyMetabolic(daily_metabolic) for _ in range(2)]
    sessions_met_time = dailyMetabolicTime(daily_metabolic)

    # Determine the latest thermal comfort value
    latest_pmv = get_pmv_value(latest_temperature, 0.935 * latest_temperature + 1.709, latest_humidity,
        sessions_met[-1], 0.8, 0.1)

    latest_pmv_status = get_pmv_status(latest_pmv)

    response = {'userID': '2',
                'airTemperature': latest_temperature,
                'relativeHumidity': latest_humidity,
                'globeTemperature': 0.935 * latest_temperature + 1.709,
                'metabolicRate': sessions_met[-1],
                'clothingInsulation': 0.8,
                'airVelocity': 0,
                'thermalComfort': latest_pmv,
                'thermalStatus': latest_pmv_status,
                'timeUnix': sessions_met_time[-1]}
    return jsonify(response)


@app.route('/api_tc', methods=['GET'])
def api_tc():
    userinfo = session.get('userinfo', None)

    cur = mysql.connection.cursor()

    # Execute SQL query to get the latest environmental parameters of temperature and humidity
    cur.execute('''SELECT tc_temperature, tc_humidity, wearable_id, gateway_id, tc_timestamp, wb_index FROM user_thermal_comfort WHERE tc_timestamp >= UNIX_TIMESTAMP(DATE_ADD(NOW(), INTERVAL -1 MINUTE));''')
    latest_env = cur.fetchall()

    # Execute SQL query to get the daily physiological parameter of metabolic rate
    cur.execute('''SELECT tc_metabolic, tc_timestamp FROM user_thermal_comfort WHERE tc_timestamp >= UNIX_TIMESTAMP(DATE_ADD(NOW(), INTERVAL -10 MINUTE));''')
    daily_metabolic = cur.fetchall()

    sessions_met = [item for item in dailyMetabolic(daily_metabolic) for _ in range(2)]

    # Create a list of dictionaries using a list comprehension
    data_list = [{'air_temperature': item[0], 'globe_temperature': item[0] * 0.935, 'relative_humidity': item[1],
                  'wearable_id': item[2], 'gateway_id': item[3],
                  'session_met': sessions_met[-1], 'clothing_insulation': 0.8, 'air_velocity': 0.1,
                  'voc_index': item[5],
                  'thermal_comfort': get_pmv_value(item[0], 0.935 * item[0], item[1], sessions_met[-1], 0.8, 0.1),
                  'thermal_comfort_desc': get_pmv_status(get_pmv_value(
                      item[0], 0.935 * item[0], item[1], sessions_met[-1], 0.8, 0.1)),
                  'timestamp': item[4], 'user_id': '2', 'dwelling_id': 'ATH-1'
                  } for item in latest_env]

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

    # decodedPayload = decodeMACPayload(data['uplink_message']['frm_payload'])
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

    # Execute SQL INSERT statement
    insert_sql = f"INSERT INTO user_thermal_comfort (tc_temperature, tc_humidity, tc_metabolic, tc_met, tc_timestamp, wearable_id, gateway_id, wb_index) VALUES ({tc_temperature}, {tc_humidity}, {tc_metabolic}, {tc_met}, {tc_timestamp}, '{device_id}', '{gateway_id}', '{wb_index}')"

    cur.execute(insert_sql)

    mysql.connection.commit()

    cur.close()

    return jsonify({'status': 'success'}), 200


@app.route('/logout')
def logout():
    access_token = session.get('access_token', None)
    keycloak_openid.logout(access_token['refresh_token'])
    session.clear()
    return redirect('/login')


@app.route('/account')
def account():
    return render_template('account.html')


@app.route('/as_test')
def as_test():
    userinfo = session.get('userinfo', None)

    cur = mysql.connection.cursor()
    cur.execute('''SELECT tc_temperature, tc_humidity, tc_timestamp, wb_index, tc_met FROM user_thermal_comfort WHERE tc_timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 24 HOUR)) AND wearable_id = %s''', (
        userinfo['deviceId'],))
    data = cur.fetchall()

    modified_data = []
    for row in data:

        tc_temperature, tc_humidity, tc_timestamp, wb_index, tc_met = row

        pmv = get_pmv_value(tc_temperature, 0.935 * tc_temperature, tc_humidity, tc_met, 0.8, 0.1)

        modified_row = row + (pmv,)

        modified_data.append(modified_row)

    data = tuple(modified_data)

    return jsonify(data)


@app.route('/session', methods=['GET'])
def current_session():
    # Return a json object that includes the session data
    return jsonify(dict(session))


if __name__ == "__main__":
    app.run(debug=True)
