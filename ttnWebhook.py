CASE_NEW_SESSION = 0
CASE_UNWANTED_RESET = 1
CASE_NORMAL_FLOW = 2

from decodeLoRaPackage import decodeMACPayload
from determineAirTemperature import get_air_temperature

def check_case(tc_timestamp, p_time):
    if tc_timestamp - p_time >30:
        return CASE_NEW_SESSION
    elif tc_timestamp - p_time >12:
        return CASE_UNWANTED_RESET
    else:
        return CASE_NORMAL_FLOW


def execute_query(cur, mysql, query, params=None, commit=False):
    try:
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)

        if commit:
            mysql.connection.commit()
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
    return True


def fetch_previous_metabolic(cur, device_id):
    query = '''SELECT tc_metabolic, tc_timestamp, tc_temperature FROM user_thermal_comfort WHERE wearable_id = %s ORDER BY tc_timestamp DESC LIMIT 1'''
    params = (device_id,)
    execute_query(cur, None, query, params)
    return cur.fetchall()


def insert_into_exc_assist(cur, mysql, device_id):
    query = f"INSERT INTO exc_assist (new_ses , reset , init_temp , wearable_id) VALUES ({False}, '{False}', {0}, {device_id})"
    execute_query(cur, mysql, query, commit=True)


def fetch_exc_assist(cur, device_id):
    query = '''SELECT new_ses, reset, init_temp FROM exc_assist WHERE wearable_id = %s LIMIT 1'''
    params = (device_id,)
    execute_query(cur, None, query, params)
    return cur.fetchall()


def handle_normal_flow(cur, mysql, case, reset, new_ses, raw_temp, p_temperature, init_temp, device_id):
    if case == CASE_NORMAL_FLOW:
        if reset:
            reset = handle_reset(reset, wb_index, device_id)
        if new_ses:
            tc_temperature, new_ses = handle_new_session_temperature(raw_temp, p_temperature, init_temp, new_ses, device_id)
    return reset, new_ses


def handle_reset(cur, mysql, reset, wb_index, device_id):
    if wb_index < 100:
        wb_index = 100
    else:
        reset = False
        query = f"UPDATE exc_assist SET reset = {reset} WHERE wearable_id = %s"
        params = (device_id,)
        execute_query(cur, mysql, query, params, commit=True)
    return reset


def handle_new_session_temperature(raw_temp, p_temperature, init_temp, new_ses, device_id):
    if raw_temp - p_temperature >= 0:
        tc_temperature = init_temp
    else:
        new_ses = False
        query = f"UPDATE exc_assist SET new_ses = {new_ses} WHERE wearable_id = %s"
        params = (device_id,)
        execute_query(cur, mysql, query, params, commit=True)
    return tc_temperature, new_ses


def handle_new_session(cur, mysql, case, new_ses, reset, raw_temp, device_id):
    if case == CASE_NEW_SESSION:
        new_ses = True
        reset = True
        initial_temp = raw_temp
        tc_temperature = initial_temp
        wb_index = 100
        query = f"UPDATE exc_assist SET new_ses = {new_ses}, reset = {reset}, init_temp = {initial_temp} WHERE wearable_id = %s"
        params = (device_id,)
        execute_query(cur, mysql, query, params, commit=True)
    return new_ses, reset


def calculate_tc_met(tc_metabolic, p_metabolic, tc_timestamp, p_time):
    if (tc_metabolic - p_metabolic) < 0:
        tc_met = 1
    else:
        tc_met = ((tc_metabolic - p_metabolic) * 40) / (tc_timestamp - p_time)
        if tc_met < 1:
            tc_met = 1
        if tc_met > 6:
            tc_met = 6
    return tc_met


def insert_into_user_thermal_comfort(cur, mysql, tc_temperature, tc_humidity, tc_metabolic, tc_met, tc_clo, tc_comfort, tc_timestamp, device_id, gateway_id, wb_index):
    insert_sql = f"INSERT INTO user_thermal_comfort (tc_temperature, tc_humidity, tc_metabolic, tc_met, tc_clo, tc_comfort, tc_timestamp, wearable_id, gateway_id, wb_index) VALUES ({tc_temperature}, {tc_humidity}, {tc_metabolic}, {tc_met}, {tc_clo}, {tc_comfort}, {tc_timestamp}, '{device_id}', '{gateway_id}', '{wb_index}')"
    execute_query(cur, mysql, insert_sql, commit=True)
