from app import mysql

# Create a cursor object to interact with the TwinERGY UPAT database
cur = mysql.connection.cursor()


# A function that gets the range of importance and the desired time window for each flexible load
def get_importance_ranges():

    cur.execute('''SELECT * FROM user_pref_thermal WHERE user_id='2' ORDER BY user_pref_time DESC''')
    preference_thermal_comfort = cur.fetchone()

    cur.execute('''SELECT * FROM user_flex_loads WHERE user_id='2' ORDER BY user_pref_time DESC''')
    preference_flex_loads = cur.fetchone()

    return [preference_thermal_comfort[1] + 3, preference_thermal_comfort[2] + 3, preference_flex_loads[1],
            preference_flex_loads[4], preference_flex_loads[7], preference_flex_loads[10], preference_flex_loads[2],
            preference_flex_loads[3], preference_flex_loads[5], preference_flex_loads[6], preference_flex_loads[8],
            preference_flex_loads[9], preference_flex_loads[11], preference_flex_loads[12], preference_flex_loads[14],
            preference_flex_loads[15], preference_flex_loads[13]]


# A function that gets the determined weight from SIMOS method for each flexible load
def get_load_weights():
    cur.execute('''SELECT * FROM load_weight_simos WHERE user_id='2' ORDER BY weight_timestamp DESC''')
    load_weight = cur.fetchone()
    """
    The position of each flexible load is as follows
    - 1; - 2; - 3; - 4; - 5;
    """
    return [load_weight[1], load_weight[2], load_weight[3], load_weight[4], load_weight[5]]
