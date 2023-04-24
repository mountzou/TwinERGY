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


def updatePrefElectricVehicle(mysql, cur, importance_electric_vehicle, wearable_id):
    current_timestamp = int(datetime.now().timestamp())

    # Update preferences related to the importance of electric vehicle into the database
    cur.execute('''
        UPDATE user_flex_load_preferences 
        SET user_ev_pref = %s, update_timestamp = %s 
        WHERE wearable_id = %s;
    ''', (importance_electric_vehicle, current_timestamp, wearable_id))

    mysql.connection.commit()

    return 0


def updatePrefWashingMachine(mysql, cur, importance_washing_machine, wearable_id):
    current_timestamp = int(datetime.now().timestamp())

    # Update preferences related to the importance of washing machine into the database
    cur.execute('''
        UPDATE user_flex_load_preferences 
        SET user_wm_pref = %s, update_timestamp = %s 
        WHERE wearable_id = %s;
    ''', (importance_washing_machine, current_timestamp, wearable_id))

    mysql.connection.commit()

    return 0


def updatePrefWaterHeater(mysql, cur, importance_water_heater, wearable_id):
    current_timestamp = int(datetime.now().timestamp())

    # Update preferences related to the importance of water heater into the database
    cur.execute('''
        UPDATE user_flex_load_preferences 
        SET user_wh_pref = %s, update_timestamp = %s 
        WHERE wearable_id = %s;
    ''', (importance_water_heater, current_timestamp, wearable_id))

    mysql.connection.commit()

    return 0


def updatePrefTumbleDrier(mysql, cur, importance_tumble_drier, wearable_id):
    current_timestamp = int(datetime.now().timestamp())

    # Update preferences related to the importance of tumble drier into the database
    cur.execute('''
        UPDATE user_flex_load_preferences 
        SET user_ht_pref = %s, update_timestamp = %s 
        WHERE wearable_id = %s;
    ''', (importance_tumble_drier, current_timestamp, wearable_id))

    mysql.connection.commit()

    return 0


def updatePrefDishWasher(mysql, cur, importance_dish_washer, wearable_id):
    current_timestamp = int(datetime.now().timestamp())

    # Update preferences related to the importance of dish washer into the database
    cur.execute('''
        UPDATE user_flex_load_preferences 
        SET user_dw_pref = %s, update_timestamp = %s 
        WHERE wearable_id = %s;
    ''', (importance_dish_washer, current_timestamp, wearable_id))

    mysql.connection.commit()

    return 0


def updateTimeElectricVehicle(mysql, cur, from_electric_vehicle, to_electric_vehicle, wearable_id):
    current_timestamp = int(datetime.now().timestamp())

    # Update preferences related to the importance of dish washer into the database
    cur.execute('''
        UPDATE user_flex_load_preferences 
        SET user_ev_start = %s, user_ev_end = %s, update_timestamp = %s 
        WHERE wearable_id = %s;
    ''', (from_electric_vehicle, to_electric_vehicle, current_timestamp, wearable_id))

    mysql.connection.commit()

    return 0


def updateTimeWashingMachine(mysql, cur, from_washing_machine, to_washing_machine, wearable_id):
    current_timestamp = int(datetime.now().timestamp())

    # Update preferences related to the importance of dish washer into the database
    cur.execute('''
        UPDATE user_flex_load_preferences 
        SET user_wm_start = %s, user_wm_end = %s, update_timestamp = %s 
        WHERE wearable_id = %s;
    ''', (from_washing_machine, to_washing_machine, current_timestamp, wearable_id))

    mysql.connection.commit()

    return 0


def updateTimeDishWasher(mysql, cur, from_dish_washer, to_dish_washer, wearable_id):
    current_timestamp = int(datetime.now().timestamp())

    # Update preferences related to the importance of dish washer into the database
    cur.execute('''
        UPDATE user_flex_load_preferences 
        SET user_dw_start = %s, user_dw_end = %s, update_timestamp = %s 
        WHERE wearable_id = %s;
    ''', (from_dish_washer, to_dish_washer, current_timestamp, wearable_id))

    mysql.connection.commit()

    return 0


def updateTimeTumbleDrier(mysql, cur, from_tumble_drier, to_tumble_drier, wearable_id):
    current_timestamp = int(datetime.now().timestamp())

    # Update preferences related to the importance of dish washer into the database
    cur.execute('''
        UPDATE user_flex_load_preferences 
        SET user_ht_start = %s, user_ht_end = %s, update_timestamp = %s 
        WHERE wearable_id = %s;
    ''', (from_tumble_drier, to_tumble_drier, current_timestamp, wearable_id))

    mysql.connection.commit()

    return 0


def updateTimeWaterHeater(mysql, cur, from_water_heater, to_water_heater, wearable_id):
    current_timestamp = int(datetime.now().timestamp())

    # Update preferences related to the importance of dish washer into the database
    cur.execute('''
        UPDATE user_flex_load_preferences 
        SET user_wh_start = %s, user_wh_end = %s, update_timestamp = %s 
        WHERE wearable_id = %s;
    ''', (from_water_heater, to_water_heater, current_timestamp, wearable_id))

    mysql.connection.commit()

    return 0
