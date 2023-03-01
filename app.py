from flask import (Flask, render_template, redirect, url_for, request)
from flask_mysqldb import MySQL

from determineMetabolic import dailyMetabolic

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

    cur.execute('''SELECT tc_metabolic, tc_timestamp FROM user_thermal_comfort WHERE tc_timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 24 HOUR));''')
    latest_metabolic = cur.fetchall()

    sessions_met = dailyMetabolic(latest_metabolic)

    print(sessions_met)

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
