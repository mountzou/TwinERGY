import time
from flask import jsonify


def device_status(cur, device_id):
    with cur as cur:
        # Execute an SQL query that retrieves the number of latest recordings for the specific wearable device
        query_get_number_of_latest_recording = """
            SELECT COUNT(*)
            FROM user_thermal_comfort
            WHERE wearable_id = %s AND tc_timestamp > %s
        """

        cur.execute(query_get_number_of_latest_recording, (device_id, int(time.time()) - 20))
        number_of_latest_recordings = cur.fetchone()[0]

    return number_of_latest_recordings
