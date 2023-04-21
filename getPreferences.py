def getThermalComfortPreferences(cur, wearable_id):
    cur.execute('''
        SELECT user_thermal_level_min, user_thermal_level_max
        FROM user_thermal_preferences
        WHERE wearable_id = %s
        ORDER BY user_thermal_timestamp DESC
        LIMIT 1;
    ''', (wearable_id,))
    thermal_preferences = cur.fetchone()

    return thermal_preferences


def getTemperaturePreferences(cur, wearable_id):
    cur.execute('''
        SELECT min_temp, max_temp
        FROM user_temperature_preferences
        WHERE wearable_id = %s
        ORDER BY update_timestamp DESC
        LIMIT 1;
    ''', (wearable_id,))
    temperature_preferences = cur.fetchone()

    return temperature_preferences


def getFlexibleLoadsPreferences(cur, wearable_id):
    cur.execute('''
        SELECT *
        FROM user_flex_load_preferences
        WHERE wearable_id = %s
        ORDER BY update_timestamp DESC
        LIMIT 1;
    ''', (wearable_id,))
    flexible_loads_preferences = cur.fetchone()

    return flexible_loads_preferences
