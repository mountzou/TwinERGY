from datetime import datetime


def updateThermalComfortPreference(mysql, cur, minTC, maxTC, wearable_id):
    current_timestamp = int(datetime.now().timestamp())

    # Insert the values into the database, including the 'user_thermal_timestamp' column
    cur.execute('''
         INSERT INTO user_thermal_preferences (wearable_id, user_thermal_level_min, user_thermal_level_max, user_thermal_description_min, user_thermal_description_max, user_thermal_timestamp)
         VALUES (%s, %s, %s, %s, %s, %s)
     ''', (wearable_id, minTC, maxTC, 'OK', 'OK', current_timestamp))

    mysql.connection.commit()

    return 0
