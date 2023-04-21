from datetime import datetime


def updateThermalComfortPreference(mysql, cur, minTC, maxTC, wearable_id):
    current_timestamp = int(datetime.now().timestamp())

    # Insert preferences related to the thermal comfort level into the database
    cur.execute('''
         INSERT INTO user_thermal_preferences (wearable_id, user_thermal_level_min, user_thermal_level_max, user_thermal_description_min, user_thermal_description_max, user_thermal_timestamp)
         VALUES (%s, %s, %s, %s, %s, %s)
     ''', (wearable_id, minTC, maxTC, 'OK', 'OK', current_timestamp))

    mysql.connection.commit()

    return 0


def updateTemperaturePreference(mysql, cur, minTemp, maxTemp, wearable_id):
    current_timestamp = int(datetime.now().timestamp())

    # Insert preferences related to the indoor temperature into the database
    cur.execute('''
         INSERT INTO user_temperature_preferences (wearable_id, min_temp, max_temp, update_timestamp)
         VALUES (%s, %s, %s, %s)
     ''', (wearable_id, minTemp, maxTemp, current_timestamp))

    mysql.connection.commit()

    return 0
