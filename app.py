from flask import (Flask, render_template, redirect, url_for, request, jsonify)
from flask_mysqldb import MySQL

from determineMetabolic import dailyMetabolic, dailyMetabolicTime
from determineThermalComfort import get_pmv_status, get_pmv_value
from determineAirTemperature import get_air_temperature

import datetime

app = Flask(__name__)

# Credentials to connect with mySQL DB of CDT UPAT
app.config['MYSQL_HOST'] = 'eu15.tmd.cloud'
app.config['MYSQL_USER'] = 'consume5_twinERGY'
app.config['MYSQL_PASSWORD'] = 'w*}S2x1pKMM='
app.config['MYSQL_DB'] = 'consume5_twinERGY'

mysql = MySQL(app)


@app.route("/")
@app.route("/index/")
def rout():
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
    latest_metabolic = cur.fetchall()

    # Detect the sessions of metabolic rate during the last 24 hours
    sessions_met = dailyMetabolic(latest_metabolic)

    daily_temp = [get_air_temperature(t[0]) for t in daily_environmental]
    daily_hum = [t[1] for t in daily_environmental]
    daily_time = [t[2] for t in daily_environmental]

    # Determine the latest and average air temperature from corresponding wearable measurements
    latest_temperature, avg_temperature = get_air_temperature(latest_temperature), get_air_temperature(avg_temperature)

    # Determine the latest thermal comfort value
    latest_pmv = get_pmv_value(latest_temperature, 0.935 * latest_temperature + 1.709, latest_humidity,
        sessions_met[-1], 0.8, 0.1)

    latest_pmv_status = get_pmv_status(latest_pmv)

    latest_update = datetime.datetime.fromtimestamp(daily_time[-1]).strftime("%Y-%m-%d %H:%M:%S")

    return render_template("index.html", avg_temp=avg_temperature, avg_hum=avg_humidity, l_temp=latest_temperature, l_hum=latest_humidity, l_met=
    sessions_met[
        -1], l_pmv=latest_pmv, d_temp=daily_temp, d_hum=daily_hum, d_time=daily_time, l_pmv_status=latest_pmv_status, l_update=latest_update)


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
        cur.execute('''SELECT AVG(tc_temperature) AS avg_temperature, AVG(tc_humidity) AS avg_humidity  FROM user_thermal_comfort WHERE tc_timestamp BETWEEN %s AND %s;''', (
            ts, te))
        tc_parameters = cur.fetchall()

        pmv = get_pmv_value(get_air_temperature(tc_parameters[0][0]), 0.935 * get_air_temperature(
            tc_parameters[0][0]) + 1.709, tc_parameters[0][1], met, 0.8, 0.1)

    daily_time = [datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') for ts in daily_time]
    sessions_met_time = [datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') for ts in sessions_met_time]

    return render_template("thermal-comfort.html", l_temp=latest_temperature, l_hum=latest_humidity, l_met=sessions_met[
        -1], avg_temp=avg_temperature, avg_hum=avg_humidity, d_temp=daily_temp, d_hum=daily_hum, d_time=daily_time, d_met=sessions_met, d_met_time=sessions_met_time, l_update=
    daily_time[-1])


@app.route('/api_tc', methods=['GET'])
def api_tc():
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

    response = {'userID': 2,
                'airTemperature': get_air_temperature(latest_temperature),
                'relativeHumidity': latest_humidity,
                'globeTemperature': 0.935 * get_air_temperature(latest_temperature) + 1.709,
                'metabolicRate': sessions_met[-1],
                'clothingInsulation': 0.8,
                'airVelocity': 0,
                'thermalComfort': latest_pmv,
                'thermalStatus': latest_pmv_status,
                'timeUnix': sessions_met_time[-1]}
    return jsonify(response)


if __name__ == "__main__":
    app.run(debug=True)
