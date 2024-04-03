from flask import Blueprint, jsonify, session
from flask.globals import g
from requests.auth import HTTPBasicAuth

from datetime import datetime
import json
import requests

outdoor_temp_bp = Blueprint('outdoor_temp_bp', __name__)


def api_get_outdoor_temperature():
    username = 'universityofpatras_mountzouris_christos'
    password = 'nO3B0cd3Th'

    pilot_cities = [
        {"name": "athens", "coordinates": "37.9838,23.7275"},
        {"name": "benetutti", "coordinates": "40.4172,9.2035"},
        {"name": "bristol", "coordinates": "51.4545,-2.5879"},
        {"name": "hagedorn", "coordinates": "52.0130,8.7774"}
    ]

    today = datetime.now().strftime('%Y-%m-%d')

    base_url = "https://api.meteomatics.com/{}T00:00:00Z--{}T23:00:00Z:PT1H/t_2m:C/{}/json"

    all_towns_hourly_temperatures = {}

    for town in pilot_cities:
        url = base_url.format(today, today, town["coordinates"])

        response = requests.get(url, auth=HTTPBasicAuth(username, password))

        if response.status_code == 200:
            data = response.json()

            hourly_temperatures = {}

            for date_info in data["data"][0]["coordinates"][0]["dates"]:
                hour = date_info["date"][11:13] + ":00"
                temperature = date_info["value"]
                hourly_temperatures[hour] = temperature

            all_towns_hourly_temperatures[town['name']] = hourly_temperatures
        else:
            print(f"Error fetching data for {town['name']}: {response.status_code} {response.reason}")

    return all_towns_hourly_temperatures


@outdoor_temp_bp.route('/insert_outdoor_temp')
def insert_outdoor_temp():
    sql = """
    INSERT INTO outdoor_temperature (user_pilot, forecast_date, hourly_temperature, created_at) 
    VALUES (%s, %s, %s, %s)
    """

    hourly_temperature = api_get_outdoor_temperature()

    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    forecast_date = datetime.now().strftime('%Y-%m-%d')

    for user_pilot, hourly_temps in hourly_temperature.items():
        hourly_temperature = json.dumps(hourly_temps)

        values = (user_pilot, forecast_date, hourly_temperature, created_at)

        try:
            g.cur.execute(sql, values)
            g.cur.connection.commit()
            print(f"Data successfully inserted for {user_pilot}.")
        except Exception as e:
            print(f"An error occurred while inserting data for {user_pilot}:", e)

    return jsonify("Data successfully inserted for all cities.")


@outdoor_temp_bp.route('/get_outdoor_temp')
def get_outdoor_temp():
    sql = """
    SELECT hourly_temperature
    FROM outdoor_temperature
    WHERE user_pilot = %s AND forecast_date = %s
    """

    user_pilot = session.get("userinfo", {}).get("pilotId")
    forecast_date = datetime.now().strftime('%Y-%m-%d')

    values = (user_pilot, forecast_date)

    try:
        g.cur.execute(sql, values)
        result = g.cur.fetchone()

        if result:
            hourly_temperature = result[0]
            hourly_temperature_dict = json.loads(hourly_temperature)
            return jsonify({"status": "success", "data": hourly_temperature_dict})
        else:
            return jsonify({"status": "error",
                            "message": f"No data found for user_pilot '{user_pilot}' on '{forecast_date}'."}), 404
    except Exception as e:
        print("An error occurred while fetching the hourly_temperature data:", e)
        return jsonify({"status": "error", "message": "An error occurred while fetching the data."}), 500
