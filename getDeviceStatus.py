import time
from flask import jsonify


def device_status(cur, device_id):
    with cur as cur:

        query = """
            SELECT tc_timestamp
            FROM user_thermal_comfort
            WHERE wearable_id = %s
            ORDER BY tc_timestamp DESC
            LIMIT 1
        """

        cur.execute(query, (device_id,))
        latest_timestamp = cur.fetchone()

        query = """
            SELECT exclude_counter,time_st 
            FROM exc_assist 
            WHERE wearable_id = %s 
            LIMIT 1
        """

        cur.execute(query, (device_id,))
        result = cur.fetchone()

    try:
        exclude_count, exclude_time = result[0], result[1]
        current_timestamp = int(time.time())
        if exclude_count < 5 and current_timestamp - exclude_time < 12:
            latest_timestamp = (0,)
    except IndexError:
        print('Initial')
    except TypeError:
        print('Initial')

    return jsonify(latest_timestamp)