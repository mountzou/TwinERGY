from flask import (Flask, render_template, redirect, url_for, session, request, jsonify)
from flask_mysqldb import MySQL

from keycloak import KeycloakOpenID

from determineMetabolic import dailyMetabolic, dailyMetabolicTime
from determineThermalComfort import get_pmv_status, get_pmv_value
from determineAirTemperature import get_air_temperature

from datetime import datetime
from urllib.parse import urlparse
import json
import requests

app = Flask(__name__)

# Credentials to connect with mySQL TwinERGY UPAT database
app.config['MYSQL_HOST'] = 'eu15.tmd.cloud'
app.config['MYSQL_USER'] = 'consume5_twinERGY'
app.config['MYSQL_PASSWORD'] = 'w*}S2x1pKMM='
app.config['MYSQL_DB'] = 'consume5_twinERGY'

mysql = MySQL(app)

keycloak_openid = KeycloakOpenID(server_url='https://auth.tec.etra-id.com/auth/',
    client_id='cdt-twinergy',
    realm_name='TwinERGY',
    client_secret_key="secret")
app.secret_key = 'secret'


@app.before_request
def require_login():
    # Define the allowed routes of a non-authenticated user
    allowed_routes = ['login', 'callback', 'static']

    # Redirect non-authenticated user to the 'login' rout
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect(url_for('login'))


@app.route("/")
@app.route("/index/")
def rout():
    # Create a userInfo object with information related to the authenticated user's session
    userinfo = session.get('userinfo', None)

    # Create a cursor object to interact with the TwinERGY UPAT database
    cur = mysql.connection.cursor()

    # Execute SQL query to get the values of air temperature and relative humidity during the last 24 hours
    cur.execute('''SELECT tc_temperature, tc_humidity, tc_timestamp FROM user_thermal_comfort WHERE tc_timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 24 HOUR)) AND wearable_id = %s''', (
    userinfo['deviceId'],))
    daily_env = cur.fetchall()

    # Execute SQL query to get the values of metabolic rate during the last 24 hours
    cur.execute('''SELECT tc_metabolic, tc_timestamp FROM user_thermal_comfort WHERE tc_timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 24 HOUR)) AND wearable_id = %s''', (
    userinfo['deviceId'],))
    daily_met = cur.fetchall()

    # Check if tuples are empty, in case of an empty tuple assign a single value of -1
    daily_env = daily_env if daily_env else []
    daily_met = daily_met if daily_met else []

    all_tem, all_hum, all_time = [get_air_temperature(row[0]) for row in daily_env], [row[1] for row in daily_env], [
        row[2] for row in daily_env]

    all_times = [datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') for ts in all_time]

    # Determine the average air temperature and the average relative humidity
    m_tem, m_hum = round(sum(all_tem) / len(all_tem), 2), round(sum(all_hum) / len(all_hum), 2)

    # Determine the latest air temperature and the latest relative humidity
    l_tem, l_hum, l_time = get_air_temperature(daily_env[-1][0]), daily_env[-1][1], datetime.utcfromtimestamp(
        daily_env[-1][2]).strftime('%Y-%m-%d %H:%M:%S')

    # Determine the latest metabolic rate
    l_met = dailyMetabolic(daily_met)[0]

    # Determine the latest PMV value and the corresponding status
    l_pmv = get_pmv_value(l_tem, 0.935 * l_tem + 1.709, l_hum, l_met, 0.8, 0.1)
    d_pmv = get_pmv_status(l_pmv)

    # Detect the sessions of metabolic rate during the last 24 hours
    # try:
    #     sessions_met = dailyMetabolic(latest_metabolic)
    # except IndexError:
    #     print('Empty metabolic rate')

    # Determine the daily, the latest and the average environmental parameters
    # try:
    #     daily_temp, daily_hum, daily_time = [get_air_temperature(t[0]) for t in daily_environmental], [t[1] for t in daily_environmental], [t[2] for t in daily_environmental]
    #     latest_temperature, avg_temperature = get_air_temperature(latest_temperature), get_air_temperature(avg_temperature)
    #     latest_pmv = get_pmv_value(latest_temperature, 0.935 * latest_temperature + 1.709, latest_humidity, sessions_met[-1], 0.8, 0.1)
    #     latest_pmv_status = get_pmv_status(latest_pmv)
    #     latest_update = datetime.datetime.fromtimestamp(daily_time[-1]).strftime("%Y-%m-%d %H:%M:%S")
    # except IndexError:
    #     print('Empty environmental parameters')

    # data = {
    #     "l_tem": l_tem, "l_hum": l_tem, "m_tem": m_tem, "m_hum": m_tem,
    #     "d_tem": d_tem, "d_hum": d_tem, "l_time": l_time, "m_time": m_time
    # }

    return render_template("index.html", daily_env=daily_env, all_tem=all_tem, all_hum=all_hum, all_times=all_times, m_tem=m_tem, m_hum=m_hum, l_met=l_met, l_tem=l_tem, l_hum=l_hum, l_time=l_time, l_pmv=l_pmv, d_pmv=d_pmv, dId=
    userinfo['dwellingId'], wId=userinfo['deviceId'], pId=userinfo[
        'pilotId'].capitalize()) if len(daily_env) > 0 else render_template("index-empty.html", dId=userinfo[
        'dwellingId'], wId=userinfo['deviceId'], pId=userinfo['pilotId'].capitalize(), username=userinfo[
        'preferred_username'])


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

    daily_temp = [get_air_temperature(t[0]) for t in daily_environmental]
    daily_hum = [t[1] for t in daily_environmental]
    daily_time = [t[2] for t in daily_environmental]

    for ts, te, met in zip(sessions_met_time, sessions_met_time[1:], sessions_met[:-1]):
        cur.execute('''SELECT AVG(tc_temperature) AS avg_temperature, AVG(tc_humidity) AS avg_humidity FROM user_thermal_comfort WHERE tc_timestamp BETWEEN %s AND %s;''', (
            ts, te))
        tc_parameters = cur.fetchall()

        pmv = get_pmv_value(get_air_temperature(tc_parameters[0][0]), 0.935 * get_air_temperature(
            tc_parameters[0][0]) + 1.709, tc_parameters[0][1], met, 0.8, 0.1)

    daily_time = [datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') for ts in daily_time]
    sessions_met_time = [datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') for ts in sessions_met_time]

    return render_template("thermal-comfort.html", l_temp=latest_temperature, l_hum=latest_humidity, l_met=sessions_met[
        -1], avg_temp=avg_temperature, avg_hum=avg_humidity, d_temp=daily_temp, d_hum=daily_hum, d_time=daily_time, d_met=sessions_met, d_met_time=sessions_met_time, l_update=
    daily_time[-1])


@app.route('/login')
def login():

    auth_url = keycloak_openid.auth_url(redirect_uri="https://"+urlparse(request.base_url).netloc+"/callback", scope="openid", state="af0ifjsldkj")

    return redirect(auth_url)


@app.route('/callback')
def callback():
    code_token = request.args.get('code')

    base_url = request.base_url

    access_token = keycloak_openid.token(
        grant_type='authorization_code',
        code=code_token,
        redirect_uri=request.base_url)

    session['userinfo'] = keycloak_openid.userinfo(access_token['access_token'])

    session['username'] = keycloak_openid.userinfo(access_token['access_token'])['preferred_username']

    return redirect('/')


@app.route('/cdmp', methods=['GET'])
def cdmp():
    # Create a userInfo object with information related to the authenticated user's session
    # userinfo = session.get('userinfo', None)
    #
    # cur = mysql.connection.cursor()
    #
    # # Execute SQL query to get the latest environmental parameters of temperature and humidity
    # cur.execute('''SELECT tc_temperature, tc_humidity FROM user_thermal_comfort ORDER BY tc_timestamp DESC LIMIT 1;''')
    # (latest_temperature, latest_humidity) = cur.fetchone()
    #
    # # Execute SQL query to get the daily physiological parameter of metabolic rate
    # cur.execute('''SELECT tc_metabolic, tc_timestamp FROM user_thermal_comfort WHERE tc_timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 24 HOUR));''')
    # daily_metabolic = cur.fetchall()
    #
    # sessions_met = [item for item in dailyMetabolic(daily_metabolic) for _ in range(2)]
    # sessions_met_time = dailyMetabolicTime(daily_metabolic)
    #
    # # Determine the latest thermal comfort value
    # latest_pmv = get_pmv_value(latest_temperature, 0.935 * latest_temperature + 1.709, latest_humidity,
    #     sessions_met[-1], 0.8, 0.1)
    #
    # latest_pmv_status = get_pmv_status(latest_pmv)

    response = {'userID': '3'}

    return jsonify(response)

@app.route('/api_tc', methods=['GET'])
def api_tc():
    # Create a userInfo object with information related to the authenticated user's session
    # userinfo = session.get('userinfo', None)
    #
    # cur = mysql.connection.cursor()
    #
    # # Execute SQL query to get the latest environmental parameters of temperature and humidity
    # cur.execute('''SELECT tc_temperature, tc_humidity FROM user_thermal_comfort ORDER BY tc_timestamp DESC LIMIT 1;''')
    # (latest_temperature, latest_humidity) = cur.fetchone()
    #
    # # Execute SQL query to get the daily physiological parameter of metabolic rate
    # cur.execute('''SELECT tc_metabolic, tc_timestamp FROM user_thermal_comfort WHERE tc_timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 24 HOUR));''')
    # daily_metabolic = cur.fetchall()
    #
    # sessions_met = [item for item in dailyMetabolic(daily_metabolic) for _ in range(2)]
    # sessions_met_time = dailyMetabolicTime(daily_metabolic)
    #
    # # Determine the latest thermal comfort value
    # latest_pmv = get_pmv_value(latest_temperature, 0.935 * latest_temperature + 1.709, latest_humidity,
    #     sessions_met[-1], 0.8, 0.1)
    #
    # latest_pmv_status = get_pmv_status(latest_pmv)

    response = {'userID': '3'}

    return jsonify(response)


if __name__ == "__main__":
    app.run(debug=True)
