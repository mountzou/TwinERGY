from flask import (Flask, render_template, redirect, url_for, session, request, g, jsonify)
from flask_mysqldb import MySQL
from flask_compress import Compress
from keycloak import KeycloakOpenID

from decodeLoRaPackage import decodeMACPayload

from determineThermalComfort import get_pmv_status, get_pmv_value, get_calibrate_clo_value, \
    get_calibrate_air_speed_value
from determineAirTemperature import get_air_temperature
from determineWellBeing import get_well_being_description
from determineSimosMethod import determineWeights
from updatePreferences import updateThermalComfortPreference, updateTemperaturePreference, updatePrefElectricVehicle, \
    updatePrefWashingMachine, updatePrefDishWasher, updatePrefWaterHeater, updatePrefTumbleDrier, \
    updateTimeElectricVehicle, updateTimeWashingMachine, updateTimeDishWasher, updateTimeTumbleDrier, \
    updateTimeWaterHeater

from getPreferences import getThermalComfortPreferences, getTemperaturePreferences, getFlexibleLoadsPreferences
from getClothing import getWinterClo, getSummerClo, getSpringClo, getAutumnClo, getSeason, getUseClo

from datetime import datetime, timedelta
from urllib.parse import urlparse
import random
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


# A function that creates the cursor object to interact with the mySQL database
def get_db_cursor():
    return mysql.connection.cursor()

def getWinterClo(cur, wearable_id):
    cur.execute('''
        SELECT user_clo
        FROM user_clo_winter
        WHERE wearable_id = %s;
    ''', (wearable_id,))
    winter_clo = cur.fetchone()

    return winter_clo


def getSummerClo(cur, wearable_id):
    cur.execute('''
        SELECT user_clo
        FROM user_clo_summer
        WHERE wearable_id = %s;
    ''', (wearable_id,))
    summer_clo = cur.fetchone()

    return summer_clo


def getSpringClo(cur, wearable_id):
    cur.execute('''
        SELECT user_clo
        FROM user_clo_spring
        WHERE wearable_id = %s;
    ''', (wearable_id,))
    spring_clo = cur.fetchone()

    return spring_clo


def getAutumnClo(cur, wearable_id):
    cur.execute('''
        SELECT user_clo
        FROM user_clo_autumn
        WHERE wearable_id = %s;
    ''', (wearable_id,))
    autumn_clo = cur.fetchone()

    return autumn_clo

def getUseClo(connection, wearable_id):
    current_season = getSeason()
    with mysql.connection.cursor() as cur:
        if current_season == "winter":
            return getWinterClo(cur, wearable_id)
        elif current_season == "spring":
            return getSpringClo(cur, wearable_id)
        elif current_season == "summer":
            return getSummerClo(cur, wearable_id)
        else:
            return getAutumnClo(cur, wearable_id)

def check_and_insert_wearable_id(device_id):
    gateway_id = '0'
    tables = ['user_clo_winter', 'user_clo_summer', 'user_clo_autumn', 'user_clo_spring']
    for table in tables:
        g.cur.execute(f'''SELECT 1 FROM {table} WHERE wearable_id = %s''', (device_id,))
        result = g.cur.fetchone()
        if result is None:
            user_timestamp = int(time.time())
            g.cur.execute(f'''INSERT INTO {table} (wearable_id, gateway_id, user_clo, user_timestamp) VALUES (%s, %s, 0.6, %s)''', (
                device_id, gateway_id, user_timestamp))
            mysql.connection.commit()


# A function to check for updates by the specific wearable device during the last 24 hours
def check_for_daily_updates():
    g.cur.execute(
        '''SELECT COUNT(tc_temperature) FROM user_thermal_comfort WHERE tc_timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 24 HOUR)) AND wearable_id = %s''',
        (
            session.get('deviceId', None),))
    (number_of_daily_data,) = g.cur.fetchone()
    g.total_daily_data = number_of_daily_data

def generate_random_number_near(number, range_start, range_end):
    return random.uniform(number - range_start, number + range_end)

@app.before_request
def require_login():
    # Define the allowed routes of a non-authenticated user
    allowed_routes = ['login', 'callback', 'static', 'api_tc', 'api_preferences', 'ttn-webhook']

    # Define the relative paths that bypass the authentication mechanism
    if request.path == '/api_tc' or request.path == '/ttn-webhook':
        return None

    # Redirect non-authenticated user to the 'login' rout
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect(url_for('login'))


@app.before_request
def before_request():
    g.cur = mysql.connection.cursor()
    check_for_daily_updates()


# A route that implements the user authentication process
@app.route('/login')
def login():
    if urlparse(request.base_url).netloc == '127.0.0.1:5000':
        auth_url = keycloak_openid.auth_url(redirect_uri="http://" + urlparse(request.base_url).netloc + "/callback",
            scope="openid", state="af0ifjsldkj")
    else:
        auth_url = keycloak_openid.auth_url(redirect_uri="https://" + urlparse(request.base_url).netloc + "/callback",
            scope="openid", state="af0ifjsldkj")

    return redirect(auth_url)


# A function that implements the access token generation for an authenticated user
@app.route('/callback')
def callback():
    code_token = request.args.get('code')

    access_token = keycloak_openid.token(
        grant_type='authorization_code',
        code=code_token,
        redirect_uri=request.base_url)

    session['access_token'] = access_token
    session['userinfo'] = keycloak_openid.userinfo(access_token['access_token'])
    session['username'] = keycloak_openid.userinfo(access_token['access_token'])['preferred_username']
    session['deviceId'] = keycloak_openid.userinfo(access_token['access_token'])['deviceId']

    check_and_insert_wearable_id(session['deviceId'])

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
    return render_template("index.html") if g.total_daily_data else render_template("index-empty.html")


@app.route("/thermal_comfort/", methods=['GET', 'POST'])
def thermal_comfort():
    return render_template("thermal-comfort.html")
    # if g.total_daily_data else render_template("thermal-comfort-empty.html")


# A functions that implements the 'Preferences' page under the route '/preferences/'
@app.route("/preferences/", methods=["GET", "POST"])
def preferences():
    return render_template("preferences.html")


# A functions that implements the 'Clothing Insulation' page under the route '/clothing_insulation /'
@app.route("/clothing_insulation/", methods=["GET", "POST"])
def clothing_insulation():
    return render_template("clothing-insulation.html")


# A functions that implements the API service that provides consumer's thermal comfort to CDMP under the route 'api_tc'
@app.route('/api_tc', methods=['GET'])
def api_tc():
    # Execute SQL query to get the latest environmental parameters of temperature and humidity
    g.cur.execute(
        '''SELECT tc_temperature, tc_humidity, wearable_id, gateway_id, tc_timestamp, wb_index, tc_met FROM user_thermal_comfort WHERE tc_timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 1 MINUTE));''')
    latest_data = g.cur.fetchall()

    def create_data_dict(data=None):
        if data is None:
            data = [0, 0, 0, 0, 0, 0, 0]
        return {
            'air_temperature': data[0],
            'globe_temperature': round(data[0] * 0.935, 2),
            'relative_humidity': data[1],
            'wearable_id': data[2],
            'gateway_id': data[3],
            'session_met': data[6],
            'clothing_insulation': get_calibrate_clo_value(0.8, data[6]) if data[6] != 0 else 0,
            'air_velocity': get_calibrate_air_speed_value(0.1, data[6]) if data[6] != 0 else 0,
            'voc_index': data[5],
            'voc_index_desc': get_well_being_description(data[5]) if data[5] != 0 else 0,
            'thermal_comfort': get_pmv_value(data[0], 0.935 * data[0], data[1], data[6], 0.8, 0.1) if data != [
                0] * 7 else 0,
            'thermal_comfort_desc': get_pmv_status(
                get_pmv_value(data[0], 0.935 * data[0], data[1], data[6], 0.8, 0.1)) if data != [0] * 7 else 0,
            "timestamp": data[4]
        }

    data_list = [create_data_dict(data) for data in latest_data] if latest_data else [create_data_dict()]

    json_schema = {'data': data_list}
    return jsonify(json_schema)


# A function that implements the API service that provides consumer's preferences to CDMP under the route 'api_preferences'
@app.route('/api_preferences', methods=['GET'])
def api_preferences():
    # Execute SQL query to retrieve consumer's preferences regarding the household flexible loads from the UPAT db
    g.cur.execute(
        '''SELECT user_ev_pref, user_ht_pref, user_wm_pref, user_wh_pref, user_dw_pref FROM user_flex_load_preferences WHERE wearable_id = %s''',
        (
            session.get('deviceId', None),))
    (electric_vehicle, tumble_drier, washing_machine, water_heater, dish_washer) = g.cur.fetchone()

    flexible_load_preferences = {
        'Electric Vehicle': electric_vehicle,
        'Tumble Drier': tumble_drier,
        'Washing Machine': washing_machine,
        'Water Heater': water_heater,
        'Dish Washer': dish_washer
    }

    # Determine the importance of each household flexible load according to SIMOS revised method
    flexible_load_weights = determineWeights(flexible_load_preferences)

    return jsonify(flexible_load_weights)


@app.route('/ttn-webhook', methods=['POST'])
def handle_ttn_webhook():

    messages2exclude=5
    # Time to ensure that a message did not come exactly after the previous
    time_diff=15

    data = request.get_json()

    # Decode incoming LoRa message

    device_id = data['end_device_ids']['dev_eui']
    gateway_id = data['uplink_message']['rx_metadata'][0]['gateway_ids']['gateway_id']

    re = decodeMACPayload(data["uplink_message"]["frm_payload"])
    raw_temp = re[0]
    tc_temperature, tc_humidity, wb_index, tc_metabolic, tc_timestamp = get_air_temperature(re[0]), re[1], re[2], re[4], \
                                                                        re[3]

    # Retrieve the latest stored value in the thermal comfort database

    g.cur.execute(
        '''SELECT tc_metabolic, tc_timestamp FROM user_thermal_comfort WHERE wearable_id = %s ORDER BY tc_timestamp DESC LIMIT 1''',
        (
            device_id,))
    previous_metabolic = g.cur.fetchall()
    try:
        p_metabolic, p_time = previous_metabolic[0][0], previous_metabolic[0][1]
    except IndexError:
        # In case there are no available data for the specific wearable ID
        p_metabolic, p_time = 0, 0

    # Retrieve the latest value from the exclude_assist database, which stores the time of arrival of the most recent rejected LoRa message
    # and the counter of how many messages have already been rejected

    g.cur.execute('''SELECT exclude_counter,time_st FROM exc_assist WHERE wearable_id = %s LIMIT 1''',
        (
            device_id,))
    try:
        result = g.cur.fetchall()
        exclude_count = result[0][0]
        exclude_time = result[0][1]
    except IndexError:
        # In case that no data for the specific wearable ID have been stored
        exclude_count = g.cur.fetchone()

    # "Initialize the exclusion procedure"
    # For the first time, populate the exclude_assist db with the received message's Wearable ID and timestamp.

    if exclude_count is None:
        exclude_count = messages2exclude
        exclude_time = tc_timestamp
        g.cur.execute(
            f"INSERT INTO exc_assist (exclude_counter, wearable_id, time_st,init_temp) VALUES ({exclude_count}, '{device_id}',{tc_timestamp},{raw_temp})")
        mysql.connection.commit()

    #tc_timestamp->Most recent message to arrive, exclude_time->Latest excluded message, p_time->Latest stored message
    if tc_timestamp - exclude_time > time_diff:
        exclude_count = messages2exclude

    if exclude_count < messages2exclude-1:

        # if exclude_count == 0 and tc_timestamp - p_time > 600:
        #     g.cur.execute(f"UPDATE exc_assist SET init_temp = {raw_temp-1.5} WHERE wearable_id = %s", (device_id,))

        exclude_count += 1

        # Update exclude counter in the exc_counter table with the most recent received LoRa message
        g.cur.execute(
            f"UPDATE exc_assist SET exclude_counter = {exclude_count}, time_st={tc_timestamp} WHERE wearable_id = %s", (
                device_id,))
        mysql.connection.commit()
        g.cur.close()
        return jsonify({'status': 'success'}), 200

    if tc_timestamp - p_time > time_diff and exclude_count == messages2exclude:
        exclude_count = 0
        g.cur.execute(
            f"UPDATE exc_assist SET exclude_counter = {exclude_count}, time_st={tc_timestamp} WHERE wearable_id = %s", (
                device_id,))
        mysql.connection.commit()
        g.cur.close()
        return jsonify({'status': 'success'}), 200

    # By the time the device is turned on, the difference between tc_metabolic and p_metabolic will be less than zero
    if (tc_metabolic - p_metabolic) < 0:
        tc_met = 1

    # Calculate the met for the 2nd, 3rd, etc..
    else:
        tc_met = ((tc_metabolic - p_metabolic) * 40) / (tc_timestamp - p_time)
        if tc_met < 1: tc_met = 1
        if tc_met > 6: tc_met = 6

    # g.cur.execute('''SELECT init_temp FROM exc_assist WHERE wearable_id = %s LIMIT 1''',(device_id,))
    #
    # initial_temp = g.cur.fetchone()
    #
    # if initial_temp[0] - tc_temperature > 0.3 or initial_temp[0] - tc_temperature < -0.3:
    #     result = generate_random_number_near(initial_temp[0], 0, 0.28)
    #     tc_temperature = result
    # else:
    #     g.cur.execute(
    #         f"UPDATE exc_assist SET init_temp = {tc_temperature} WHERE wearable_id = %s", (
    #             device_id,))

    tc_clo = getUseClo(g.cur, device_id)[0]

    tc_comfort = get_pmv_value(tc_temperature, 0.935 * tc_temperature, tc_humidity, tc_met, tc_clo, 0.1)

    # Execute SQL INSERT statement
    insert_sql = f"INSERT INTO user_thermal_comfort (tc_temperature, tc_humidity, tc_metabolic, tc_met, tc_clo, tc_comfort, tc_timestamp, wearable_id, gateway_id, wb_index) VALUES ({tc_temperature}, {tc_humidity}, {tc_metabolic}, {tc_met}, {tc_clo}, {tc_comfort}, {tc_timestamp}, '{device_id}', '{gateway_id}', '{wb_index}')"

    g.cur.execute(insert_sql)
    exclude_count = messages2exclude
    g.cur.execute(
        f"UPDATE exc_assist SET exclude_counter = {exclude_count}, time_st={tc_timestamp} WHERE wearable_id = %s", (
            device_id,))

    mysql.connection.commit()
    g.cur.close()

    return jsonify({'status': 'success'}), 200


# A functions that implements the 'Account' page under the route '/account/'
@app.route('/account/')
def account():
    return render_template('account.html')


# A functions that implements the 'Helpdesk' page under the route '/helpdesk/'
@app.route('/helpdesk')
def helpdesk():
    return render_template('helpdesk.html')


# A route that implements an asynchronous call to retrieve data related to the user's thermal comfort during the last 24 hours
@app.route('/get_data_thermal_comfort/')
def get_data_thermal_comfort():
    userinfo = session.get('userinfo', None)
    query = """
        SELECT tc_temperature, tc_humidity, tc_timestamp, wb_index, tc_met
        FROM user_thermal_comfort
        WHERE tc_timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 24 HOUR))
        AND wearable_id = %s
        ORDER BY tc_timestamp DESC
        LIMIT 100
    """
    with g.cur as cur:
        cur.execute(query, (session.get('deviceId', None),))
        thermal_comfort_data = cur.fetchall()

    met_data = [tc_met for _, _, _, _, tc_met in thermal_comfort_data[:10]]
    met_sum, met_count = sum(met_data), len(met_data)

    average_met = met_sum / met_count if met_count > 0 else 0

    clo_insulation = getUseClo(g.cur, session['deviceId'])[0]

    daily_thermal_comfort_data = [(tc_temperature, tc_humidity, tc_timestamp, wb_index, tc_met,
                                   get_pmv_value(tc_temperature, 0.935 * tc_temperature, tc_humidity, average_met, clo_insulation,
                                       0.1), clo_insulation)
                                  for tc_temperature, tc_humidity, tc_timestamp, wb_index, tc_met in
                                  reversed(thermal_comfort_data)]

    return jsonify({'daily_thermal_comfort_data': daily_thermal_comfort_data})


@app.route('/get_user_clothing_insulation')
def get_user_clothing_insulation():
    tables = ['user_clo_winter', 'user_clo_summer', 'user_clo_autumn', 'user_clo_spring']
    seasons = ['winter', 'summer', 'autumn', 'spring']
    user_clo_dict = {}

    for season, table in zip(seasons, tables):
        g.cur.execute(f'''SELECT user_clo FROM {table} WHERE wearable_id = %s''', (
            session.get('userinfo', None)['deviceId'],))
        clo_value = g.cur.fetchone()
        user_clo_dict[season] = clo_value[0] if clo_value else None

    user_clo_json = json.dumps(user_clo_dict)
    return user_clo_json


# A route that implements an asynchronous call to retrieve data related to the thermal comfort
@app.route('/get_data_preferences')
def get_data_preferences():
    preferences_thermal_comfort = getThermalComfortPreferences(g.cur, session.get('deviceId', None))
    preferences_temperature = getTemperaturePreferences(g.cur, session.get('deviceId', None))
    preferences_flexible_loads = getFlexibleLoadsPreferences(g.cur, session.get('deviceId', None))

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
                        },
                    'electric_vehicle_time':
                        {
                            'electric_vehicle_time_from': preferences_flexible_loads[2],
                            'electric_vehicle_time_to': preferences_flexible_loads[3],
                        },
                    'tumble_drier_time':
                        {
                            'tumble_drier_time_from': preferences_flexible_loads[5],
                            'tumble_drier_time_to': preferences_flexible_loads[6],
                        },
                    'washing_machine_time':
                        {
                            'washing_machine_time_from': preferences_flexible_loads[8],
                            'washing_machine_time_to': preferences_flexible_loads[9],
                        },
                    'dish_washer_time':
                        {
                            'dish_washer_time_from': preferences_flexible_loads[11],
                            'dish_washer_time_to': preferences_flexible_loads[12],
                        },
                    'water_heater_time':
                        {
                            'water_heater_time_from': preferences_flexible_loads[14],
                            'water_heater_time_to': preferences_flexible_loads[15],
                        },
                }
            ]
        }

        return jsonify(response)

    else:

        return jsonify(tuple("1"))


@app.route('/get_preferences_weights')
def get_preferences_weights():
    # Execute SQL query to retrieve consumer's preferences regarding the household flexible loads from the UPAT db
    g.cur.execute(
        '''SELECT user_ev_pref, user_ht_pref, user_wm_pref, user_wh_pref, user_dw_pref FROM user_flex_load_preferences WHERE wearable_id = %s''',
        (
            session.get('deviceId', None),))
    (electric_vehicle, tumble_drier, washing_machine, water_heater, dish_washer) = g.cur.fetchone()

    flexible_load_preferences = {
        'Electric Vehicle': electric_vehicle,
        'Tumble Drier': tumble_drier,
        'Washing Machine': washing_machine,
        'Water Heater': water_heater,
        'Dish Washer': dish_washer
    }

    # Determine the importance of each household flexible load according to SIMOS revised method
    flexible_load_weights = determineWeights(flexible_load_preferences)

    return jsonify(flexible_load_weights)


@app.route('/update_preferences_thermal_comfort', methods=['POST'])
def update_preferences_thermal_comfort():
    user_thermal_level_min = request.form.get('user_thermal_level_min')
    user_thermal_level_max = request.form.get('user_thermal_level_max')

    updateThermalComfortPreference(mysql, g.cur, user_thermal_level_min, user_thermal_level_max,
        session.get('deviceId', None))
    return jsonify(success=True)


@app.route('/update_preferences_temperature', methods=['POST'])
def update_preferences_temperature():
    user_temp_min = request.form.get('user_temp_min')
    user_temp_max = request.form.get('user_temp_max')

    updateTemperaturePreference(mysql, g.cur, user_temp_min, user_temp_max, session.get('deviceId', None))
    return jsonify(success=True)


@app.route('/update_preferences_importance_electric_vehicle', methods=['POST'])
def update_preferences_importance_electric_vehicle():
    importance_electric_vehicle = request.form.get('importance_electric_vehicle')

    updatePrefElectricVehicle(mysql, g.cur, importance_electric_vehicle, session.get('deviceId', None))

    return jsonify(success=True)


@app.route('/update_preferences_importance_washing_machine', methods=['POST'])
def update_preferences_importance_washing_machine():
    importance_washing_machine = request.form.get('importance_washing_machine')

    updatePrefWashingMachine(mysql, g.cur, importance_washing_machine, session.get('deviceId', None))

    return jsonify(success=True)


@app.route('/update_preferences_importance_dish_washer', methods=['POST'])
def update_preferences_importance_dish_washer():
    importance_dish_washer = request.form.get('importance_dish_washer')

    updatePrefDishWasher(mysql, g.cur, importance_dish_washer, session.get('deviceId', None))

    return jsonify(success=True)


@app.route('/update_preferences_importance_tumble_drier', methods=['POST'])
def update_preferences_importance_tumble_drier():
    importance_tumble_drier = request.form.get('importance_tumble_drier')

    updatePrefTumbleDrier(mysql, g.cur, importance_tumble_drier, session.get('deviceId', None))

    return jsonify(success=True)


@app.route('/update_preferences_importance_water_heater', methods=['POST'])
def update_preferences_importance_water_heater():
    importance_water_heater = request.form.get('importance_water_heater')

    updatePrefWaterHeater(mysql, g.cur, importance_water_heater, session.get('deviceId', None))

    return jsonify(success=True)


@app.route('/update_range_electric_vehicle', methods=['POST'])
def update_range_electric_vehicle():
    fromElectricVehicle = request.form.get('fromElectricVehicle')
    toElectricVehicle = request.form.get('toElectricVehicle')

    updateTimeElectricVehicle(mysql, g.cur, fromElectricVehicle, toElectricVehicle, session.get('deviceId', None))

    return jsonify(success=True)


@app.route('/update_range_washing_machine', methods=['POST'])
def update_range_washing_machine():
    fromWashingMachine = request.form.get('fromWashingMachine')
    toWashingMachine = request.form.get('toWashingMachine')

    updateTimeWashingMachine(mysql, g.cur, fromWashingMachine, toWashingMachine, session.get('deviceId', None))

    return jsonify(success=True)


@app.route('/update_range_dish_washer', methods=['POST'])
def update_range_dish_washer():
    fromDishWasher = request.form.get('fromDishWasher')
    toDishWasher = request.form.get('toDishWasher')

    updateTimeDishWasher(mysql, g.cur, fromDishWasher, toDishWasher, session.get('deviceId', None))

    return jsonify(success=True)


@app.route('/update_range_tumble_drier', methods=['POST'])
def update_range_tumble_drier():
    fromTumbleDrier = request.form.get('fromTumbleDrier')
    toTumbleDrier = request.form.get('toTumbleDrier')

    updateTimeTumbleDrier(mysql, g.cur, fromTumbleDrier, toTumbleDrier, session.get('deviceId', None))

    return jsonify(success=True)


@app.route('/update_range_water_heater', methods=['POST'])
def update_range_water_heater():
    fromWaterHeater = request.form.get('fromWaterHeater')
    toWaterHeater = request.form.get('toWaterHeater')

    updateTimeWaterHeater(mysql, g.cur, fromWaterHeater, toWaterHeater, session.get('deviceId', None))

    return jsonify(success=True)


# A route that implements an asynchronous call to retrieve data related to the thermal comfort
@app.route('/get_user_clothing')
def get_user_clothing():
    winter_clo = getWinterClo(g.cur, session.get('deviceId', None))
    spring_clo = getSpringClo(g.cur, session.get('deviceId', None))
    summer_clo = getSummerClo(g.cur, session.get('deviceId', None))
    autumn_clo = getAutumnClo(g.cur, session.get('deviceId', None))

    response = {
        'clothing_insulation': [
            {
            'season_insulation':
                {
                    'winter_clo': winter_clo,
                    'summer_clo': summer_clo,
                    'spring_clo': spring_clo,
                    'autumn_clo': autumn_clo
                },
            }
        ]
    }

    return jsonify(response)


@app.route('/update_clothing_summer', methods=['POST'])
def update_clothing_summer():

    g.cur.execute('''
        UPDATE user_clo_summer
        SET wearable_id = %s, gateway_id = %s, user_clo = %s, user_timestamp = %s
        WHERE wearable_id = %s;
    ''', (session['deviceId'], 0, request.form.get('summer_clo'), int(datetime.now().timestamp()), session['deviceId']))

    mysql.connection.commit()


    return jsonify(success=True)


@app.route('/update_clothing_winter', methods=['POST'])
def update_clothing_winter():

    g.cur.execute('''
        UPDATE user_clo_winter
        SET wearable_id = %s, gateway_id = %s, user_clo = %s, user_timestamp = %s
        WHERE wearable_id = %s;
    ''', (session['deviceId'], 0, request.form.get('winter_clo'), int(datetime.now().timestamp()), session['deviceId']))

    mysql.connection.commit()

    return jsonify(success=True)


@app.route('/update_clothing_autumn', methods=['POST'])
def update_clothing_autumn():

    g.cur.execute('''
        UPDATE user_clo_autumn
        SET wearable_id = %s, gateway_id = %s, user_clo = %s, user_timestamp = %s
        WHERE wearable_id = %s;
    ''', (session['deviceId'], 0, request.form.get('autumn_clo'), int(datetime.now().timestamp()), session['deviceId']))

    mysql.connection.commit()

    return jsonify(success=True)


@app.route('/update_clothing_spring', methods=['POST'])
def update_clothing_spring():

    g.cur.execute('''
        UPDATE user_clo_spring 
        SET wearable_id = %s, gateway_id = %s, user_clo = %s, user_timestamp = %s
        WHERE wearable_id = %s;
    ''', (session['deviceId'], 0, request.form.get('spring_clo'), int(datetime.now().timestamp()), session['deviceId']))

    mysql.connection.commit()

    return jsonify(success=True)


@app.route('/get_data_thermal_comfort_range', methods=['GET'])
def get_data_thermal_comfort_range():
    userinfo = session.get('userinfo', None)

    start_date, end_date = request.args.get('start_date'), request.args.get('end_date')

    if not start_date or not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date, '%Y-%m-%d').date() + timedelta(days=1)

    start_timestamp, end_timestamp = int(time.mktime(start_date.timetuple())), int(time.mktime(end_date.timetuple()))

    g.cur.execute(
        '''SELECT tc_temperature, tc_humidity, tc_timestamp, wb_index, tc_met FROM user_thermal_comfort WHERE tc_timestamp >= %s AND tc_timestamp <= %s AND wearable_id = %s ORDER BY tc_timestamp ASC''',
        (
            start_timestamp, end_timestamp, userinfo['deviceId']))
    thermal_comfort_data = g.cur.fetchall()

    thermal_comfort_list = []

    clo_insulation = getUseClo(g.cur, userinfo['deviceId'])[0]

    for row in thermal_comfort_data:
        tc_temperature, tc_humidity, tc_timestamp, wb_index, tc_met = row

        pmv = row + (get_pmv_value(tc_temperature, 0.935 * tc_temperature, tc_humidity, tc_met, clo_insulation, 0.1),)
        thermal_comfort_list.append(pmv)

    return jsonify(tuple(thermal_comfort_list))


# A method that retrieves a specific number of results for the thermal comfort dataset in CDMP
@app.route('/monitor_thermal_comfort_cdmp/')
def monitor_thermal_comfort_cdmp():
    # Create a header with the X-API-TOKEN of our user in CDMP
    headers = {"X-API-TOKEN": '8a3cb21d-be27-466d-a797-54fae21a0d8a'}
    # Define the number of results in response object through the page size
    page_size = 1000
    # Insert the URL of a specific dataset included in the CDMP
    url = f"https://twinergy.s5labs.eu/api/query/00bb2745-578a-400f-bcef-da04f3a174d4?pageSize={page_size}"
    # Assign the response in a JSON format variable
    response_thermal_comfort = requests.get(url, headers=headers).json()

    return jsonify(response_thermal_comfort)


@app.route('/session', methods=['GET'])
def current_session():
    # Return a json object that includes the session data
    return jsonify(dict(session))


@app.route('/get_device_status')
def get_device_status():
    with g.cur as cur:

        query = """
            SELECT tc_timestamp
            FROM user_thermal_comfort
            WHERE wearable_id = %s
            ORDER BY tc_timestamp DESC
            LIMIT 1
        """

        cur.execute(query, (session.get('userinfo', None)['deviceId'],))
        latest_timestamp = cur.fetchone()

        query = """
            SELECT exclude_counter,time_st 
            FROM exc_assist 
            WHERE wearable_id = %s 
            LIMIT 1
        """

        cur.execute(query, (session.get('userinfo', None)['deviceId'],))
        result = cur.fetchone()

    try:
        exclude_count, exclude_time = result[0], result[1]
        current_timestamp = int(time.time())
        if exclude_count < 5 and current_timestamp - exclude_time < 12:
            latest_timestamp = (0,)
    except IndexError:
        print('Initial')
    except TypeError:
        print('Initial')

    return jsonify(latest_timestamp)


if __name__ == "__main__":
    app.run(debug=True)
