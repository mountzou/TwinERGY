from flask import (Flask, render_template, redirect, url_for, request)
from flask_mysqldb import MySQL

from determineMetabolic import dailyMetabolic

from determineThermalComfort import get_pmv_status, get_pmv_value

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

    # Execute SQL query to get the latest environmental parameters of temperature and humidity that recorded
    cur.execute('''SELECT tc_temperature, tc_humidity FROM user_thermal_comfort ORDER BY tc_timestamp DESC LIMIT 1;''')
    (latest_temperature, latest_humidity) = cur.fetchone()

    cur.execute('''SELECT tc_temperature, tc_humidity, tc_timestamp FROM user_thermal_comfort WHERE tc_timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 24 HOUR));''')
    daily_environmental = cur.fetchall()

    cur.execute('''SELECT tc_metabolic, tc_timestamp FROM user_thermal_comfort WHERE tc_timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 24 HOUR));''')
    latest_metabolic = cur.fetchall()

    sessions_met = dailyMetabolic(latest_metabolic)

    # Determine the latest thermal comfort value
    latest_pmv = get_pmv_value(latest_temperature, 0.935*latest_temperature + 1.709, latest_humidity, sessions_met[-1], 0.8, 0.1)
    latest_pmv_status = get_pmv_status(latest_pmv)

    daily_temp, daily_hum, daily_time = [t[0] for t in daily_environmental], [t[1] for t in daily_environmental], [t[2] for t in daily_environmental]

    return render_template("index.html", avg_temp=avg_temperature, avg_hum=avg_humidity, l_temp=latest_temperature, l_hum=latest_humidity, l_met=sessions_met[-1], l_pmv=latest_pmv, d_temp=daily_temp, d_hum=daily_hum, d_time=daily_time, l_pmv_status=latest_pmv_status)


if __name__ == "__main__":
    app.run(debug=True)
