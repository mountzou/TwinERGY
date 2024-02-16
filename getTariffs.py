import requests
from urllib.parse import quote
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import pandas as pd
from flask_mysqldb import MySQL


def getTariffENTSOE():

    base_url = "https://web-api.tp.entsoe.eu/api"
    api_key = "0540bc4c-8f7e-42fc-82d0-b089b19ee016"

    today = datetime.now()

    periodStart, periodEnd = (today + timedelta(days=0)).strftime("%Y%m%d0000"), (today + timedelta(days=0)).strftime("%Y%m%d2300")

    params = {
        "documentType": "A44",
        "processType": "A01",
        "in_Domain": "10YGR-HTSO-----Y",
        "out_Domain": "10YGR-HTSO-----Y",
        "periodStart": periodStart,
        "periodEnd": periodEnd
    }

    param_string = "&".join([f"{key}={quote(str(value))}" for key, value in params.items()])
    request_url = f"{base_url}?securityToken={api_key}&{param_string}"

    response = requests.get(request_url)

    if response.status_code == 200:

        root = ET.fromstring(response.text)

        start_time_str = root.find('.//{urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:0}period.timeInterval/{urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:0}start').text
        start_timestamp = datetime.strptime(start_time_str, "%Y-%m-%dT%H:%MZ")

        points = root.findall('.//{urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:0}Point')
        data = []

        for point in points:
            position = int(point.find('{urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:0}position').text)
            price_amount = float(point.find('{urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:0}price.amount').text)
            timestamp = start_timestamp + timedelta(hours=position)
            data.append({'Position': position, 'Price': price_amount, 'Timestamp': timestamp.isoformat()})

        return data

    else:
        print(f"Error fetching day-ahead prices: HTTP {response.status_code}")

    return "error"