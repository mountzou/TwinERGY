import time


def initialize_user_clothing_insulation(mysql, cur, device_id, gateway_id):
    """
    Initialize user clothing insulation preferences for all seasons if not already present in the database.
    """
    initialize_user_clothing_insulation_winter(mysql, cur, device_id, gateway_id)
    initialize_user_clothing_insulation_summer(mysql, cur, device_id, gateway_id)
    initialize_user_clothing_insulation_autumn(mysql, cur, device_id, gateway_id)
    initialize_user_clothing_insulation_spring(mysql, cur, device_id, gateway_id)


def initialize_user_clothing_insulation_winter(mysql, cur, device_id, gateway_id):
    """
    Initialize user clothing insulation preferences for winter if not already present in the database.
    """
    check_existing_preferences_query = '''
        SELECT 1
        FROM user_clo_winter
        WHERE wearable_id = %s
    '''
    cur.execute(check_existing_preferences_query, (device_id,))
    result = cur.fetchone()
    if result is None:
        insert_preferences_query = '''
            INSERT INTO user_clo_winter
            (wearable_id, gateway_id, user_clo, user_timestamp)
            VALUES (%s, %s, 0.88, %s)
        '''
        cur.execute(insert_preferences_query, (device_id, gateway_id, int(time.time())))
        mysql.connection.commit()


def initialize_user_clothing_insulation_autumn(mysql, cur, device_id, gateway_id):
    """
    Initialize user clothing insulation preferences for autumn if not already present in the database.
    """
    check_existing_autumn_clothing_query = '''
        SELECT 1
        FROM user_clo_autumn
        WHERE wearable_id = %s
    '''

    cur.execute(check_existing_autumn_clothing_query, (device_id,))

    if cur.fetchone() is None:
        insert_autumn_clothing_query = '''
            INSERT INTO user_clo_autumn
            (wearable_id, gateway_id, user_clo, user_timestamp)
            VALUES (%s, %s, 0.56, %s)
        '''
        cur.execute(insert_autumn_clothing_query, (device_id, gateway_id, int(time.time())))
        mysql.connection.commit()


def initialize_user_clothing_insulation_spring(mysql, cur, device_id, gateway_id):
    """
    Initialize user clothing insulation preferences for spring if not already present in the database.
    """
    check_existing_spring_clothing_query = '''
        SELECT 1
        FROM user_clo_spring
        WHERE wearable_id = %s
    '''

    cur.execute(check_existing_spring_clothing_query, (device_id,))

    if cur.fetchone() is None:
        insert_spring_clothing_query = '''
            INSERT INTO user_clo_spring
            (wearable_id, gateway_id, user_clo, user_timestamp)
            VALUES (%s, %s, 0.56, %s)
        '''
        cur.execute(insert_spring_clothing_query, (device_id, gateway_id, int(time.time())))
        mysql.connection.commit()


def initialize_user_clothing_insulation_summer(mysql, cur, device_id, gateway_id):
    """
    Initialize user clothing insulation preferences for summer if not already present in the database.
    """
    check_existing_summer_clothing_query = '''
        SELECT 1
        FROM user_clo_summer
        WHERE wearable_id = %s
    '''

    cur.execute(check_existing_summer_clothing_query, (device_id,))

    if cur.fetchone() is None:
        insert_summer_clothing_query = '''
            INSERT INTO user_clo_summer
            (wearable_id, gateway_id, user_clo, user_timestamp)
            VALUES (%s, %s, 0.43, %s)
        '''
        cur.execute(insert_summer_clothing_query, (device_id, gateway_id, int(time.time())))
        mysql.connection.commit()


def initialize_user_temperature_preferences(mysql, cur, device_id):
    """
    Initialize user thermal preferences if not already present in the database.
    """
    check_existing_temperature_preferences_query = '''
        SELECT 1 
        FROM user_temperature_preferences 
        WHERE wearable_id = %s
    '''
    cur.execute(check_existing_temperature_preferences_query, (device_id,))

    if cur.fetchone() is None:
        insert_temperature_preferences_query = '''
            INSERT INTO user_temperature_preferences 
            (wearable_id, min_temp, max_temp, update_timestamp) 
            VALUES (%s, 18, 20, %s)
        '''
        cur.execute(insert_temperature_preferences_query, (device_id, int(time.time())))
        mysql.connection.commit()


def initialize_user_thermal_comfort_preferences(mysql, cur, device_id):
    """
    Initialize user thermal comfort preferences if not already present in the database.
    """
    check_existing_thermal_comfort_preferences_query = '''
        SELECT 1 
        FROM user_thermal_preferences 
        WHERE wearable_id = %s
    '''
    cur.execute(check_existing_thermal_comfort_preferences_query, (device_id,))

    if cur.fetchone() is None:
        insert_thermal_comfort_preferences_query = '''
            INSERT INTO user_thermal_preferences 
            (wearable_id, user_thermal_level_min, user_thermal_description_min, user_thermal_level_max, user_thermal_description_max, user_thermal_timestamp) 
            VALUES (%s, -1, 'Slightly Cool', 1, 'Slightly Warm', %s)
        '''
        cur.execute(insert_thermal_comfort_preferences_query, (device_id, int(time.time())))
        mysql.connection.commit()


def initialize_user_load_preferences(mysql, cur, device_id):
    """
    Initialize user's flexible load preferences if not already present in the database.
    """
    check_existing_flex_load_preferences_query = '''
        SELECT 1 
        FROM user_flex_load_preferences 
        WHERE wearable_id = %s
    '''
    cur.execute(check_existing_flex_load_preferences_query, (device_id,))

    if cur.fetchone() is None:
        insert_flex_load_preferences_query = '''
            INSERT INTO user_flex_load_preferences 
            (wearable_id, user_ev_pref, user_ev_start, user_ev_end, user_ht_pref, user_ht_start, user_ht_end, user_wm_pref, user_wm_start, user_wm_end, user_dw_pref, user_dw_start, user_dw_end, user_wh_pref, user_wh_start, user_wh_end, update_timestamp) 
            VALUES (%s, 4, 2, 14, 2, 2, 10, 3, 4, 6, 1, 5, 8, 2, 9, 12, %s)
        '''
        cur.execute(insert_flex_load_preferences_query, (device_id, int(time.time())))
        mysql.connection.commit()