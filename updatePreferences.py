from datetime import datetime

# Mapping of appliance names to their abbreviations
appliance_abbreviations = {
    'electric_vehicle': 'ev',
    'tumble_drier': 'ht',
    'washing_machine': 'wm',
    'dish_washer': 'dw',
    'water_heater': 'wh'
}


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


def updatePreference(mysql, cur, appliance, importance, wearable_id):
    current_timestamp = int(datetime.now().timestamp())
    # Get the abbreviation for the appliance
    abbreviation = appliance_abbreviations.get(appliance)
    # Construct the column name
    preference_column = f'user_{abbreviation}_pref'

    cur.execute(f'''
        UPDATE user_flex_load_preferences 
        SET {preference_column} = %s, update_timestamp = %s 
        WHERE wearable_id = %s;
    ''', (importance, current_timestamp, wearable_id))

    mysql.connection.commit()

    return 0


def updateTimeRange(mysql, cur, appliance, from_time, to_time, wearable_id):
    current_timestamp = int(datetime.now().timestamp())
    # Get the abbreviation for the appliance
    abbreviation = appliance_abbreviations.get(appliance)
    # Construct the column names
    start_column = f'user_{abbreviation}_start'
    end_column = f'user_{abbreviation}_end'

    cur.execute(f'''
        UPDATE user_flex_load_preferences 
        SET {start_column} = %s, {end_column} = %s, update_timestamp = %s 
        WHERE wearable_id = %s;
    ''', (from_time, to_time, current_timestamp, wearable_id))

    mysql.connection.commit()

    return 0
