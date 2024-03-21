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
from filter_thermal_comfort import *

from demandSideManagement import *

from getTariffs import *
from getOutdoorTemperature import *

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

import base64

from urllib.parse import urlparse
import json
import requests
import pandas as pd
import random as rand
import numpy as np
from multiprocessing import cpu_count

from pulp import *

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
    allowed_routes = ['login', 'callback', 'static', 'api_tc', 'api_preferences', 'ttn-webhook', 'webhk', 'get_tariffs','get_electricity_tariffs_dash', 'get_outdoor_temperature']

    # Define the relative paths that bypass the authentication mechanism
    if request.path == '/api_tc' or request.path == '/ttn-webhook' or request.path == '/webhk' or request.path =='/get_tariffs' or request.path == '/get_outdoor_temperature' or request.path == 'get_electricity_tariffs_dash':
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
def index():
    tc = get_data_thermal_comfort().json

    if not tc.get('daily_thermal_comfort_data'):
        return render_template("index-empty.html")
    else:
        return render_template("index.html")


# A function that renders the template of the 'Thermal Comfort' page under the route '/thermal_comfort/.
@app.route("/thermal_comfort/", methods=['GET', 'POST'])
def thermal_comfort():
    return render_template("thermal-comfort.html")
    # if g.total_daily_data else render_template(
    # "thermal-comfort-empty.html")


# A function that renders the template of the 'Preferences' page under the route '/preferences/.
@app.route("/preferences/", methods=["GET", "POST"])
def preferences():
    appliances = [
        {'name': 'Electric Vehicle', 'id': 'electric_vehicle'},
        {'name': 'Washing Machine', 'id': 'washing_machine'},
        {'name': 'Dish Washer', 'id': 'dish_washer'},
        {'name': 'Tumble Drier', 'id': 'tumble_drier'},
        {'name': 'Water Heater', 'id': 'water_heater'}
    ]
    return render_template("preferences.html", appliances=appliances)


# A functions that renders the 'Clothing Insulation' page under the route '/clothing_insulation /'
@app.route("/clothing_insulation/", methods=["GET", "POST"])
def clothing_insulation():
    return render_template("clothing-insulation.html")


# A functions that renders the 'Account' page under the route '/account/'
@app.route('/account/')
def account():
    return render_template('account.html')


# A functions that implements the API service that provides consumer's thermal comfort to CDMP under the route '/api_tc'
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
    return jsonify(api_Preferences(g.cur))


@app.route('/webhk', methods=['POST'])
def handle_webhk():
    data = request.get_json()
    mac_payload = base64.b64decode(data["uplink_message"]["frm_payload"]).hex()

    gateway_id = data['uplink_message']['rx_metadata'][0]['gateway_ids']['gateway_id']
    device_id = data["end_device_ids"]["dev_eui"]

    current_time = datetime.now(timezone.utc)
    unix_timestamp = int(current_time.timestamp())

    timestamp = (datetime.now() + timedelta(hours=2)).strftime("%d/%m/%Y %H:%M:%S")

    temperature_raw = int(mac_payload[-8:-4], 16)

    integer_part_tem = int(str(temperature_raw)[:2])
    decimal_part_tem = int(str(temperature_raw)[2:])

    temperature = integer_part_tem + (decimal_part_tem / 100)

    relative_humidity_raw = int(mac_payload[-4:], 16)

    integer_part_hum = int(str(relative_humidity_raw)[:2])
    decimal_part_hum = int(str(relative_humidity_raw)[2:])

    relative_humidity = integer_part_hum + (decimal_part_hum / 100)

    battery_raw = int(mac_payload[5:8], 16)

    integer_part_bat = int(str(battery_raw)[:2])
    decimal_part_bat = int(str(battery_raw)[2:])

    battery = integer_part_bat + (decimal_part_bat / 256)

    gas_eval = int(mac_payload[-16:-12], 16)
    nox_eval = int(mac_payload[-20:-16], 16)


    temp_co2 = int(mac_payload[13:16], 16)
    integer_part_co2 = int(str(temp_co2)[:2])
    decimal_part_co2 = int(str(temp_co2)[2:])

    co2 = (integer_part_co2 + (decimal_part_co2 / 100)) * 10
    if co2 < 400:
        co2 = round(co2 * 10, 2)


    pm1_concentration = int(mac_payload[25:28], 16)
    pm25_concentration = int(mac_payload[29:32], 16)
    pm4_concentration = int(mac_payload[33:36], 16)
    pm10_concentration = int(mac_payload[37:40], 16)
    pm05_nconcentration = int(mac_payload[41:44], 16)
    pm1_nconcentration = int(mac_payload[45:48], 16)
    pm25_nconcentration = int(mac_payload[49:52], 16)
    pm4_nconcentration = int(mac_payload[53:56], 16)
    pm10_nconcentration = int(mac_payload[57:60], 16)
    typical_particle = int(mac_payload[61:64], 16)
    if device_id=="0080E1150510BDE6" or device_id=="0080E1150533F233":
        url = "https://script.google.com/macros/s/AKfycbzOPn4VcDAs41g2C0vMr5oOxm38okSnpaSMkAS8xfmjVhQmMBqACcKfOjhnrJxRJvZwUA/exec"
    else:
        nox_eval=0
        url = "https://script.google.com/macros/s/AKfycbzxTm-_PNSkPRocRp4Xh3BHm9R0ZsbSXLQ5rARTAZRQlmeAgTF5hjERSy_sFfydktbi/exec"


    data_to_sheet = {
        "column1": device_id,
        "column2": unix_timestamp,
        "column3": temperature,
        "column4": relative_humidity,
        "column5": gas_eval,
        "column6": nox_eval,
        "column7": co2,
        "column8": pm1_concentration,
        "column9": pm25_concentration,
        "column10": pm4_concentration,
        "column11": pm10_concentration,
        "column12": pm05_nconcentration,
        "column13": pm1_nconcentration,
        "column14": pm25_nconcentration,
        "column15": pm4_nconcentration,
        "column16": pm10_nconcentration,
        "column17": typical_particle,
        "column18": timestamp,
        "column19": battery
    }

    response = requests.post(url, data=json.dumps(data_to_sheet), headers={"Content-Type": "application/json"})
    print(response.text)

    return jsonify({'status': 'success'}), 200


@app.route('/ttn-webhook', methods=['POST'])
def handle_ttn_webhook():
    data = request.get_json()
    if data['end_device_ids']['dev_eui'] != '0080E1150510BDEB':
        print("#############################")
        print("Received payload for device:", data['end_device_ids']['dev_eui'])
    device_id = data['end_device_ids']['dev_eui']
    gateway_id = data['uplink_message']['rx_metadata'][0]['gateway_ids']['gateway_id']

    decodedPayload = decodeMACPayload(data["uplink_message"]["frm_payload"])
    tc_temperature, tc_humidity, wb_index, tc_metabolic, tc_timestamp = get_air_temperature(decodedPayload[0]), \
                                                                        decodedPayload[1], decodedPayload[2], \
                                                                        decodedPayload[4], decodedPayload[3]
    query = '''SELECT wearable_id, session_start, session_end FROM wearable_device_sessions WHERE wearable_id = %s ORDER BY session_end DESC LIMIT 1'''
    params = (device_id,)
    execute_query(g.cur, mysql, query, params)
    wear_sessions = g.cur.fetchall()
    previous_metabolic = fetch_previous_metabolic(mysql, g.cur, device_id)
    p_metabolic, p_time = previous_metabolic[0] if previous_metabolic else (0, 0)

    if tc_timestamp - p_time > 45 or p_time == 0:
        print(" tc_timestamp-p_time>45 or p_time==0")

        if wear_sessions and tc_timestamp - wear_sessions[0][1] > 120:
            print("Yπάρχει wear_sessions")

            dt = datetime.utcfromtimestamp(tc_timestamp)
            new_dt = dt + timedelta(minutes=2)
            session_ends = int(new_dt.timestamp())
            query = f"UPDATE wearable_device_sessions SET session_start = {tc_timestamp}, session_end = {session_ends} WHERE wearable_id = %s"
            params = (device_id,)
            execute_query(g.cur, mysql, query, params, commit=True)
        else:
            print("Δεν υπάρχει wear_sessions")
            dt = datetime.utcfromtimestamp(tc_timestamp)
            new_dt = dt + timedelta(minutes=2)
            session_ends = int(new_dt.timestamp())
            insert_sql = f"INSERT INTO wearable_device_sessions (wearable_id, session_start, session_end) VALUES ('{device_id}', '{tc_timestamp}', '{session_ends}')"
            insert_into_user_thermal_comfort(g.cur, mysql, 0, 0, 0, 0, 0, 0, session_ends, device_id, 0, 0)
            execute_query(g.cur, mysql, insert_sql, commit=True)

    if tc_timestamp > wear_sessions[0][2]:

        tc_met = calculate_tc_met(tc_metabolic, p_metabolic, tc_timestamp, p_time)
        tc_clo = get_clo_insulation(g.cur, mysql, device_id)[0]
        tc_pmv = get_pmv_value(tc_temperature, 0.935 * tc_temperature, tc_humidity, tc_met, tc_clo, 0.1)

        insert_into_user_thermal_comfort(g.cur, mysql, tc_temperature, tc_humidity, tc_metabolic, tc_met, tc_clo,
            tc_pmv, tc_timestamp, device_id, gateway_id, wb_index)

    else:
        print("Το tc_timestamp μικρότερο του session_end")

    return jsonify({'status': 'success'}), 200


def fetch_time_to_wait(mysql, cur, device_id):
    query = '''SELECT session_end FROM wearable_device_sessions WHERE wearable_id = %s ORDER BY session_end DESC LIMIT 1'''
    params = (device_id,)
    execute_query(cur, mysql, query, params)
    return cur.fetchall()


@app.route('/get_data_lem_pricing/')
def get_data_lem_pricing():
    url = "https://lem.dev.twinergy.transactiveenergymodule.com/api/v1/lem/all_lem_price"
    user_city = session.get("userinfo", {}).get("pilotId")

    try:
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()

        if not data.get("success"):
            raise ValueError("Request unsuccessful")

        lem_data = data.get("data", [])

        latest_date = max([datetime.strptime(entry["timestamp"], "%d/%m/%Y") for entry in lem_data])
        latest_date_str = latest_date.strftime("%d/%m/%Y")

        added_entries = set()

        latest_day_data = []
        for entry in lem_data:
            if entry["timestamp"] == latest_date_str and user_city in entry:
                key = (entry["timestamp"], entry["hour_index"])
                if key not in added_entries:
                    latest_day_data.append({
                        "timestamp": entry["timestamp"],
                        "hour_index": entry["hour_index"],
                        "price": entry[user_city]  # Use a unified key for price
                    })
                    added_entries.add(key)

        return jsonify(latest_day_data)

    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 500


# Retrieve user's thermal comfort data from the latest active session of the wearable device
@app.route('/get_data_thermal_comfort/')
def get_data_thermal_comfort():
    # Define the timestamp of the current day, i.e., from 00:00:01 and on.
    today = datetime.combine(datetime.now(timezone.utc).date(), datetime.min.time(), tzinfo=timezone.utc)

    # Execute SQL query to retrieve the current day's thermal comfort parameters for the specific wearable device
    query = """
        SELECT tc_temperature, tc_humidity, tc_timestamp, wb_index, tc_met
        FROM user_thermal_comfort
        WHERE tc_timestamp >= %s
        AND wearable_id = %s
        ORDER BY tc_timestamp DESC
    """
    with g.cur as cur:
        cur.execute(query, (int(today.timestamp()), session.get('deviceId', None)))
        thermal_comfort_data = cur.fetchall()

    # Create a dataframe with the retrieved thermal comfort data to filter the latest active session of the wearable device
    df = pd.DataFrame(thermal_comfort_data, columns=['tc_temperature', 'tc_humidity', 'tc_timestamp', 'wb_index',
                                                     'tc_met'])
    tc_latest_active_session = filter_thermal_comfort_dashboard(df)

    met_data = [tc_met for _, _, _, _, tc_met in tc_latest_active_session[:10]]
    average_met = sum(met_data) / len(met_data) if sum(met_data) > 0 else 0

    clo_insulation = get_clo_insulation(mysql, g.cur, (session.get('deviceId', None)))[0]

    daily_thermal_comfort_data = [(tc_temperature, tc_humidity, tc_timestamp, wb_index, tc_met,
                                   get_pmv_value(tc_temperature, 0.935 * tc_temperature, tc_humidity, average_met,
                                       clo_insulation,
                                       0.1), clo_insulation, get_t_wearable(tc_temperature))
                                  for tc_temperature, tc_humidity, tc_timestamp, wb_index, tc_met in
                                  tc_latest_active_session]

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
    # Update the preference regarding the user's thermal comfort
    updateThermalComfortPreference(mysql, g.cur, user_thermal_level_min, user_thermal_level_max,
        session.get('deviceId', None))

    return jsonify(success=True)


@app.route('/update_preferences_temperature', methods=['POST'])
def update_preferences_temperature():
    user_temp_min, user_temp_max = map(request.form.get, ('user_temp_min', 'user_temp_max'))
    # Update the preference regarding the indoor air temperature
    updateTemperaturePreference(mysql, g.cur, user_temp_min, user_temp_max, session.get('deviceId', None))

    return jsonify(success=True)


@app.route('/update/<appliance>/<update_type>', methods=['POST'])
def update_appliance_preferences(appliance, update_type):
    wearable_id = session.get('deviceId', None)
    if update_type == 'preference':
        importance = request.form.get(f'importance_{appliance}')
        return updatePreference(mysql, g.cur, appliance, importance, wearable_id)
    elif update_type == 'time_range':
        from_time = request.form.get(f'from{appliance.capitalize()}')
        to_time = request.form.get(f'to{appliance.capitalize()}')
        return updateTimeRange(mysql, g.cur, appliance, from_time, to_time, wearable_id)
    else:
        return jsonify(success=False, message='Invalid update type')


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
    # Return the number of the latest recordings from the specific wearable device in JSON format
    return jsonify({'device_status': current_device_status})


@app.route('/demand_side_management/')
def demand_side_management():
    min_temp, max_temp = getTemperaturePreferences(g.cur, session.get('deviceId', None))
    min_comfort, max_comfort = getThermalComfortPreferences(g.cur, session.get('deviceId', None))



    out_temperatures = get_outdoor_temperature(g.cur, session.get("userinfo", {}).get("pilotId").capitalize())
    tariff = get_electricity_tariffs(g.cur, session.get("userinfo", {}).get("pilotId").capitalize())
    # pi_i = {j: round(rand.uniform(0, 0.10), 3) for j in range(1, 13)}
    # pi_i.update({j: round(rand.uniform(0.10, 0.20), 3) for j in range(13, 25)})
    pi_i=tariff

    clo_insulation = get_clo_insulation(g.cur, mysql, session.get('deviceId', None))[0]
    metabolic_rate = 1

    preferences_flexible_loads = get_data_preferences().get_json()

    operation_times = {}

    for load, times in preferences_flexible_loads['preferences'][0].items():
        from_key, to_key = f'{load}_from', f'{load}_to'
        if from_key in times and to_key in times:
            operation_times[load] = (times[from_key], times[to_key])

    operation_times_json = jsonify(operation_times).data.decode('utf-8')

    T_start_j, T_end_j = dsm_time_flexible_loads_slots(json.loads(operation_times_json))
    T_start_k, T_end_k = dsm_phase_flexible_loads_const_slots(json.loads(operation_times_json))
    T_start_m, T_end_m = dsm_phase_flexible_loads_diff_slots(json.loads(operation_times_json))


    optimal_schedule = dsm_solve_problem(T_start_j, T_end_j, T_start_m, T_end_m, T_start_k, T_end_k, min_comfort, max_comfort, out_temperatures, clo_insulation, pi_i)
    optimal_schedule_json = jsonify(optimal_schedule).data.decode('utf-8')

    return render_template('demand-side-management.html',
        operation_times=operation_times,
        operation_times_json=operation_times_json,
        optimal_schedule_json=optimal_schedule_json,
        prices=pi_i,
        min_temp=min_temp,
        max_temp=max_temp,
        min_comfort=min_comfort,
        max_comfort=max_comfort)


@app.route('/account_loads/')
def account_loads():
    return render_template('account-loads.html')


@app.route('/update_account_loads', methods=['POST'])
def update_account_loads():
    data = request.json
    wearable_id = session.get('deviceId', None)

    # Accessing each field in the JSON data
    washing_machine_power = data.get('washingMachinePower')
    dish_washer_power = data.get('dishWasherPower')
    tumble_drier_power = data.get('tumbleDrierPower')
    washing_machine_duration = data.get('washingMachineDuration')
    dish_washer_duration = data.get('dishWasherDuration')
    tumble_drier_duration = data.get('tumbleDrierDuration')

    electric_vehicle_power1 = data.get('electricVehiclePower1')
    electric_vehicle_power2 = data.get('electricVehiclePower2')
    electric_vehicle_power3 = data.get('electricVehiclePower3')
    max_electric_vehicle_power = data.get('maxElectricVehiclePower')

    electric_water_heater_power1 = data.get('electricWaterHeaterPower1')
    max_electric_water_heater_power = data.get('maxElectricWaterHeaterPower')

    ac_power = data.get('acPower')
    ac_power_25 = data.get('acPower25')
    ac_power_50 = data.get('acPower50')
    ac_power_75 = data.get('acPower75')
    ac_power_100 = data.get('acPower100')

    load_information = {
        'Time-flexible Loads': {
            'Washing Machine': {
                'Power': washing_machine_power,
                'Duration': washing_machine_duration
            },
            'Dish Washer': {
                'Power': dish_washer_power,
                'Duration': dish_washer_duration
            },
            'Tumble Drier': {
                'Power': tumble_drier_power,
                'Duration': tumble_drier_duration
            }
        },
        'Phase-flexible Loads': {
            'Electric Vehicle': {
                'Power 1': electric_vehicle_power1,
                'Power 2': electric_vehicle_power2,
                'Power 3': electric_vehicle_power3,
                'Max Power': max_electric_vehicle_power
            },
            'Electric Water Heater': {
                'Power 1': electric_water_heater_power1,
                'Max Power': max_electric_water_heater_power
            }
        },
        'Thermostatic Load': {
            'AC Power': {
                'Power': ac_power,
                '25% Power': ac_power_25,
                '50% Power': ac_power_50,
                '75% Power': ac_power_75,
                '100% Power': ac_power_100
            }
        }
    }

    insert_load_time_wm = f"INSERT INTO load_flexible_time (wearable_id, appliance_type, power, duration, update_timestamp) VALUES ('{wearable_id}', 'WM', '{washing_machine_power}', '{washing_machine_duration}', '{int(datetime.now().timestamp())}')"
    execute_query(g.cur, mysql, insert_load_time_wm, commit=True)
    insert_load_time_dw = f"INSERT INTO load_flexible_time (wearable_id, appliance_type, power, duration, update_timestamp) VALUES ('{wearable_id}', 'DW', '{dish_washer_power}', '{dish_washer_duration}', '{int(datetime.now().timestamp())}')"
    execute_query(g.cur, mysql, insert_load_time_dw, commit=True)
    insert_load_time_td = f"INSERT INTO load_flexible_time (wearable_id, appliance_type, power, duration, update_timestamp) VALUES ('{wearable_id}', 'TD', '{tumble_drier_power}', '{tumble_drier_duration}', '{int(datetime.now().timestamp())}')"
    execute_query(g.cur, mysql, insert_load_time_td, commit=True)

    insert_load_ac = f"INSERT INTO load_flexible_ac (wearable_id, ac_power, ac_power_25, ac_power_50, ac_power_75, ac_power_100, update_timestamp) VALUES ('{wearable_id}', '{ac_power}', '{ac_power_25}', '{ac_power_50}', '{ac_power_75}', '{ac_power_100}', '{int(datetime.now().timestamp())}')"
    execute_query(g.cur, mysql, insert_load_ac, commit=True)
    insert_load_phase_ev = f"INSERT INTO load_flexible_phase (wearable_id, appliance_type, power1, power2, power3, max_power, update_timestamp) VALUES ('{wearable_id}', 'EV', '{electric_vehicle_power1}', '{electric_vehicle_power2}', '{electric_vehicle_power3}', '{max_electric_vehicle_power}', '{int(datetime.now().timestamp())}')"
    execute_query(g.cur, mysql, insert_load_phase_ev, commit=True)
    insert_load_phase_ewh = f"INSERT INTO load_flexible_phase (wearable_id, appliance_type, power1, power2, power3, max_power, update_timestamp) VALUES ('{wearable_id}', 'EWH', '{electric_water_heater_power1}', 0, 0, '{max_electric_water_heater_power}', '{int(datetime.now().timestamp())}')"
    execute_query(g.cur, mysql, insert_load_phase_ewh, commit=True)

    return jsonify({'status': 'success', 'message': 'Data processed successfully'})


@app.route('/get_account_loads', methods=['GET'])
def get_account_loads():
    wearable_id = session.get('deviceId', None)

    query_time_shiftable = """
        (SELECT * FROM load_flexible_time WHERE wearable_id = %s AND appliance_type = 'WM' ORDER BY update_timestamp DESC LIMIT 1)
        UNION ALL
        (SELECT * FROM load_flexible_time WHERE wearable_id = %s AND appliance_type = 'DW' ORDER BY update_timestamp DESC LIMIT 1)
        UNION ALL
        (SELECT * FROM load_flexible_time WHERE wearable_id = %s AND appliance_type = 'TD' ORDER BY update_timestamp DESC LIMIT 1);
    """

    query_phase_shiftable = """
        (SELECT * FROM load_flexible_phase WHERE wearable_id = %s AND appliance_type = 'EV' ORDER BY update_timestamp DESC LIMIT 1)
        UNION ALL
        (SELECT * FROM load_flexible_phase WHERE wearable_id = %s AND appliance_type = 'EWH' ORDER BY update_timestamp DESC LIMIT 1)
    """

    query_ac = """
        (SELECT * FROM load_flexible_ac WHERE wearable_id = %s ORDER BY update_timestamp DESC LIMIT 1)
    """

    with g.cur as cur:
        cur.execute(query_time_shiftable, (wearable_id, wearable_id, wearable_id))
        time_shiftable = cur.fetchall()
        cur.execute(query_phase_shiftable, (wearable_id, wearable_id))
        phase_shiftable = cur.fetchall()
        cur.execute(query_ac, (wearable_id,))
        ac_shiftable = cur.fetchall()

    return jsonify({'phase_shiftable': phase_shiftable, 'time_shiftable': time_shiftable, 'ac_shiftable': ac_shiftable})


@app.route('/get_electricity_tariffs_dash', methods=['POST', 'GET'])
def get_electricity_tariffs_dash():
    city = 'Athens'
    today = datetime.now()
    tariffs = None
    while tariffs is None or len(tariffs) == 0:
        date_str = today.strftime('%Y-%m-%d')
        g.cur.execute('''
            SELECT *
            FROM user_tariffs
            WHERE city = %s
            AND date_recorded = %s
            ORDER BY date_recorded DESC
            LIMIT 1;
        ''', (city, date_str,))
        tariffs = g.cur.fetchone()

        # Check if tariffs is not None and has data
        if tariffs is not None and len(tariffs) > 0:
            tariffs_float_values = [round(float(value)/1000,3) for value in list(tariffs[3:])]
            hourly_tariffs = {hour: value for hour, value in enumerate(tariffs_float_values, start=1)}
            return hourly_tariffs
        else:
            # Decrement the date by one day and try again
            today -= timedelta(days=1)
            # You may want to add a condition to break the loop after a certain number of attempts
            # to prevent an infinite loop in case there are no records at all.

    # Handle the case where no tariffs are found after exiting the loop
    print("No tariffs found for the given city in the recent period.")
    return None

@app.route('/get_tariffs')
def get_tariffs():
    sql = """
    INSERT INTO user_tariffs (city, date_recorded, hour_0, hour_1, hour_2, hour_3, hour_4, hour_5, hour_6, hour_7, hour_8, hour_9, hour_10, hour_11, hour_12, hour_13, hour_14, hour_15, hour_16, hour_17, hour_18, hour_19, hour_20, hour_21, hour_22, hour_23) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    tariffs_athens = getTariffENTSOE('Greece')
    tariffs_benetutti = getTariffENTSOE('Italy')

    print()

    if tariffs_athens != "error":
        date_recorded = tariffs_athens[0]['Timestamp'].split('T')[0]
        prices = [tariff['Price'] for tariff in sorted(tariffs_athens, key=lambda x: x['Position'])]
        values = ("Athens", date_recorded, *prices)
        execute_query(g.cur, mysql, sql, values, commit=True)

    if tariffs_benetutti != "error":
        date_recorded = tariffs_benetutti[0]['Timestamp'].split('T')[0]
        prices = [tariff['Price'] for tariff in sorted(tariffs_benetutti, key=lambda x: x['Position'])]
        values = ("Benetutti", date_recorded, *prices)
        execute_query(g.cur, mysql, sql, values, commit=True)

    return "Tariffs added successfully."


@app.route('/insert_outdoor_temperature')
def insert_outdoor_temperature():
    sql = """
    INSERT INTO user_outdoor_temperature (town_name, date_recorded, hour_0, hour_1, hour_2, hour_3, hour_4, hour_5, hour_6, hour_7, hour_8, hour_9, hour_10, hour_11, hour_12, hour_13, hour_14, hour_15, hour_16, hour_17, hour_18, hour_19, hour_20, hour_21, hour_22, hour_23) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    temp = get_outdoorTemperature()

    date_recorded = datetime.now().strftime("%Y-%m-%d")

    for full_city_name, temps in temp.items():
        city_name = full_city_name.split(',')[0].strip()
        hourly_temps = [temps[f"{hour:02d}:00"] for hour in range(24)]
        values = [city_name, date_recorded] + hourly_temps
        execute_query(g.cur, mysql, sql, values, commit=True)

    return "Outdoor temperatures added successfully."

if __name__ == "__main__":
    app.run(debug=True)
