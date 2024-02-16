import requests
from datetime import datetime
from requests.auth import HTTPBasicAuth

def get_outdoorTemperature():
    username = 'universityofpatras_mountzouris_christos'
    password = 'nO3B0cd3Th'

    towns_coordinates = [
        {"name": "Athens, Greece", "coordinates": "37.9838,23.7275"},
        {"name": "Benetutti, Italy", "coordinates": "40.4172,9.2035"},
        {"name": "Bristol, UK", "coordinates": "51.4545,-2.5879"},
        {"name": "Hagedorn, Germany", "coordinates": "52.0130,8.7774"}
    ]

    today = datetime.now().strftime('%Y-%m-%d')

    base_url = "https://api.meteomatics.com/{}T00:00:00Z--{}T23:00:00Z:PT1H/t_2m:C/{}/json"

    all_towns_hourly_temperatures = {}

    for town in towns_coordinates:
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