from determineSimosMethod import *


def api_Preferences(cur):
    # Execute SQL query to retrieve consumer's preferences regarding the household flexible loads from the UPAT db
    cur.execute('''SELECT user_ev_pref, user_ht_pref, user_wm_pref, user_wh_pref, user_dw_pref FROM user_flex_load_preferences''')
    # Fetch the results of the consumers' preferences regarding the household flexible loads
    (electric_vehicle, tumble_drier, washing_machine, water_heater, dish_washer) = cur.fetchone()

    # Create a dictionary with the consumers' preferences regarding the household flexible loads
    flexible_load_preferences = {
        'Electric Vehicle': electric_vehicle,
        'Tumble Drier': tumble_drier,
        'Washing Machine': washing_machine,
        'Water Heater': water_heater,
        'Dish Washer': dish_washer
    }

    # Determine the importance of each household flexible load according to SIMOS revised method
    flexible_load_weights = determineWeights(flexible_load_preferences)

    return flexible_load_weights
