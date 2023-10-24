from flask import (Flask, render_template, redirect, url_for, session, request, g, jsonify)
from flask_mysqldb import MySQL
from flask_compress import Compress
from keycloak import KeycloakOpenID

from decodeLoRaPackage import decodeMACPayload
from getDeviceStatus import *
from initializeUser import *

from determineThermalComfort import *
from determineAirTemperature import *
from determineWellBeing import *

from apiService import *

# Import functions regarding the user's preferences
from getPreferences import *
from updatePreferences import *
from determineSimosMethod import *
# Import functions regarding the user's clothing insulation
from getClothing import *

from ttnWebhook import *

# Import functions regarding the date and time
from datetime import datetime, timedelta, time, timezone
import time
from urllib.parse import urlparse
import json
import requests

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


# A function to check for updates by the specific wearable device during the last 24 hours
def check_for_daily_updates():
    # Get the current datetime
    now = datetime.now(timezone.utc)

    # Create a new datetime at midnight
    midnight = datetime(year=now.year, month=now.month, day=now.day, hour=0, minute=0, second=0, tzinfo=timezone.utc)

    # Convert the datetime to a UNIX timestamp
    timestamp = int(midnight.timestamp())

    # Execute the modified query
    g.cur.execute(
        '''SELECT COUNT(tc_temperature) FROM user_thermal_comfort WHERE tc_timestamp >= %s AND wearable_id = %s''',
        (
            timestamp,
            session.get('deviceId', None),
        )
    )

    (number_of_daily_data,) = g.cur.fetchone()
    g.total_daily_data = number_of_daily_data


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
    access_token = keycloak_openid.token(
        grant_type='authorization_code',
        code=request.args.get('code'),
        redirect_uri=request.base_url)

    session['access_token'] = access_token
    session['userinfo'] = keycloak_openid.userinfo(access_token['access_token'])
    session['username'] = keycloak_openid.userinfo(access_token['access_token'])['preferred_username']
    session['deviceId'] = keycloak_openid.userinfo(access_token['access_token'])['deviceId']
    session['gatewayId'] = keycloak_openid.userinfo(access_token['access_token'])['gatewayId']

    initialize_user_clothing_insulation(mysql, g.cur, session['deviceId'], session['gatewayId'])
    initialize_user_temperature_preferences(mysql, g.cur, session['deviceId'])
    initialize_user_thermal_comfort_preferences(mysql, g.cur, session['deviceId'])
    initialize_user_load_preferences(mysql, g.cur, session['deviceId'])

    return redirect('/')


# A route that implements the logout mechanism
@app.route('/logout')
def logout():
    access_token = session.get('access_token', None)
    keycloak_openid.logout(access_token['refresh_token'])
    session.clear()
    return redirect('/login')


# A function that renders the template of the 'Dashboard' page under the routes '/index/, 'dashboard' and '/'
@app.route("/")
@app.route("/index/")
@app.route("/dashboard/")
def rout():
    return render_template("index.html") if g.total_daily_data else render_template("index-empty.html")


# A function that renders the template of the 'Thermal Comfort' page under the route '/thermal_comfort/.
@app.route("/thermal_comfort/", methods=['GET', 'POST'])
def thermal_comfort():
    return render_template("thermal-comfort.html")
        # if g.total_daily_data else render_template(
        # "thermal-comfort-empty.html")


# A function that renders the template of the 'Preferences' page under the route '/preferences/.
@app.route("/preferences/", methods=["GET", "POST"])
def preferences():
    return render_template("preferences.html")


# A functions that renders the 'Clothing Insulation' page under the route '/clothing_insulation /'
@app.route("/clothing_insulation/", methods=["GET", "POST"])
def clothing_insulation():
    return render_template("clothing-insulation.html")


# A functions that renders the 'Account' page under the route '/account/'
@app.route('/account/')
def account():
    return render_template('account.html')


# A functions that renders the 'Helpdesk' page under the route '/helpdesk/'
@app.route('/helpdesk')
def helpdesk():
    return render_template('helpdesk.html')


# A functions that implements the API service that provides consumer's thermal comfort to CDMP under the route '/api_tc'
@app.route('/api_tc', methods=['GET'])
def api_tc():
    # Execute SQL query to get the latest environmental parameters of temperature and humidity
    g.cur.execute(
        '''SELECT tc_temperature, tc_humidity, wearable_id, gateway_id, tc_timestamp, wb_index, tc_met FROM user_thermal_comfort WHERE tc_timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 1 MINUTE));''')
    latest_data = g.cur.fetchall()

    print(latest_data)

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
    api_response_preferences = api_Preferences(g.cur)

    return jsonify(api_response_preferences)


@app.route('/ttn-webhook', methods=['POST'])
def handle_ttn_webhook():
    data = request.get_json()

    # Decode incoming LoRa message
    device_id = data['end_device_ids']['dev_eui']
    gateway_id = data['uplink_message']['rx_metadata'][0]['gateway_ids']['gateway_id']

    decodedPayload = decodeMACPayload(data["uplink_message"]["frm_payload"])
    raw_temp = decodedPayload[0]
    tc_temperature, tc_humidity, wb_index, tc_metabolic, tc_timestamp = get_air_temperature(decodedPayload[0]), \
        decodedPayload[1], decodedPayload[2], decodedPayload[4], decodedPayload[3]

    # Retrieve the latest stored value in the thermal comfort database
    previous_metabolic = fetch_previous_metabolic(mysql, g.cur, device_id)

    # Extract previous values or set defaults
    p_metabolic, p_time = previous_metabolic[0] if previous_metabolic else (0, 0)

    result = fetch_exc_assist(mysql, g.cur, device_id)
    print(data)
    print(result)
    if not result:

        print(device_id)
        insert_into_exc_assist(g.cur, mysql, device_id, tc_timestamp, raw_temp)
        new_ses, reset, init_temp, p_temperature, tries, time_st = 0, 0, raw_temp, raw_temp, 0, tc_timestamp
    else:
        new_ses, reset, init_temp, p_temperature, tries, time_st = result[0]

    # Check the time difference of the current timestamp to the previous stored to decide what is the case
    case = check_case(tc_timestamp, p_time)

    if case == CASE_UNWANTED_RESET:
        print("case unwanted reset")
        wb_index = handle_unwanted_reset(g.cur, mysql, wb_index, device_id)

    if case == CASE_NORMAL_FLOW:
        print("case normal flow")

        wb_index, tc_temperature = handle_normal_flow(g.cur, mysql, wb_index, reset, new_ses, raw_temp, p_temperature,
                                                      init_temp, tc_temperature, device_id, tries)

    if case == CASE_NEW_SESSION:
        print("case new_session")

        tc_temperature, wb_index = handle_new_session(g.cur, mysql, raw_temp, device_id, tc_timestamp, p_time,
                                                      init_temp, time_st, tc_temperature)

    query = f"UPDATE exc_assist SET p_temperature={raw_temp} WHERE wearable_id = %s"
    params = (device_id,)
    execute_query(g.cur, mysql, query, params, commit=True)

    # Calculate tc_met
    tc_met = calculate_tc_met(tc_metabolic, p_metabolic, tc_timestamp, p_time)

    tc_clo = get_clo_insulation(g.cur, mysql, device_id)[0]

    tc_comfort = get_pmv_value(tc_temperature, 0.935 * tc_temperature, tc_humidity, tc_met, tc_clo, 0.1)

    # Execute SQL INSERT statement
    insert_into_user_thermal_comfort(g.cur, mysql, tc_temperature, tc_humidity, tc_metabolic, tc_met, tc_clo,
                                     tc_comfort, tc_timestamp, device_id, gateway_id, wb_index)

    return jsonify({'status': 'success'}), 200


# A route that implements an asynchronous call to retrieve data related to the user's thermal comfort during the last 24 hours
@app.route('/get_data_thermal_comfort/')
def get_data_thermal_comfort():
    # Get the current date
    now = datetime.now()

    # Create a new datetime at midnight
    midnight = datetime(year=now.year, month=now.month, day=now.day, hour=0, minute=0, second=0, tzinfo=timezone.utc)

    # Convert the datetime to a UNIX timestamp
    timestamp = int(midnight.timestamp())

    query = """
        SELECT tc_temperature, tc_humidity, tc_timestamp, wb_index, tc_met
        FROM user_thermal_comfort
        WHERE tc_timestamp >= %s
        AND wearable_id = %s
        ORDER BY tc_timestamp DESC
    """
    with g.cur as cur:
        cur.execute(query, (timestamp, session.get('deviceId', None)))
        thermal_comfort_data = cur.fetchall()

    met_data = [tc_met for _, _, _, _, tc_met in thermal_comfort_data[:10]]
    met_sum, met_count = sum(met_data), len(met_data)

    average_met = met_sum / met_count if met_count > 0 else 0

    clo_insulation = get_clo_insulation(mysql, g.cur, (session.get('deviceId', None)))[0]

    daily_thermal_comfort_data = [(tc_temperature, tc_humidity, tc_timestamp, wb_index, tc_met,
                                   get_pmv_value(tc_temperature, 0.935 * tc_temperature, tc_humidity, average_met,
                                                 clo_insulation,
                                                 0.1), clo_insulation, get_t_wearable(tc_temperature))
                                  for tc_temperature, tc_humidity, tc_timestamp, wb_index, tc_met in
                                  reversed(thermal_comfort_data)]

    return jsonify({'daily_thermal_comfort_data': daily_thermal_comfort_data})


@app.route('/get_user_clothing_insulation')
def get_user_clothing_insulation():
    summer_clo = getSummerClo(g.cur, session.get('userinfo', None)['deviceId'])[0]
    winter_clo = getWinterClo(g.cur, session.get('userinfo', None)['deviceId'])[0]
    autumn_clo = getAutumnClo(g.cur, session.get('userinfo', None)['deviceId'])[0]
    spring_clo = getSpringClo(g.cur, session.get('userinfo', None)['deviceId'])[0]

    user_clo_dict = {"summer": summer_clo, "winter": winter_clo, "autumn": autumn_clo, "spring": spring_clo}

    return json.dumps(user_clo_dict)


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
    # Update the preference regarding the importance of electric vehicle
    updatePrefElectricVehicle(mysql, g.cur, importance_electric_vehicle, session.get('deviceId', None))

    return jsonify(success=True)


@app.route('/update_preferences_importance_washing_machine', methods=['POST'])
def update_preferences_importance_washing_machine():
    importance_washing_machine = request.form.get('importance_washing_machine')
    # Update the preference regarding the importance of washing machine
    updatePrefWashingMachine(mysql, g.cur, importance_washing_machine, session.get('deviceId', None))

    return jsonify(success=True)


@app.route('/update_preferences_importance_dish_washer', methods=['POST'])
def update_preferences_importance_dish_washer():
    importance_dish_washer = request.form.get('importance_dish_washer')
    # Update the preference regarding the importance of dishwasher
    updatePrefDishWasher(mysql, g.cur, importance_dish_washer, session.get('deviceId', None))

    return jsonify(success=True)


@app.route('/update_preferences_importance_tumble_drier', methods=['POST'])
def update_preferences_importance_tumble_drier():
    importance_tumble_drier = request.form.get('importance_tumble_drier')
    # Update the preference regarding the importance of tumble drier
    updatePrefTumbleDrier(mysql, g.cur, importance_tumble_drier, session.get('deviceId', None))

    return jsonify(success=True)


@app.route('/update_preferences_importance_water_heater', methods=['POST'])
def update_preferences_importance_water_heater():
    importance_water_heater = request.form.get('importance_water_heater')
    # Update the preference regarding the importance of water heater
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

    clo_insulation = get_clo_insulation(mysql, g.cur, userinfo['deviceId'])[0]

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
    current_device_status = device_status(g.cur, session['deviceId'])
    # Return the current device status
    return current_device_status


if __name__ == "__main__":
    app.run(debug=True)
