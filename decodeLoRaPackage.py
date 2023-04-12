import base64
import time
from datetime import datetime, timedelta


def decodeMACPayload(payload):
    # Value of MAC Payload in hex format
    mac_payload = base64.b64decode(payload).hex()

    relative_humidity_raw = int(mac_payload[-4:], 16)

    integer_part_hum = int(str(relative_humidity_raw)[:2])
    decimal_part_hum = int(str(relative_humidity_raw)[2:])

    relative_humidity = integer_part_hum + (decimal_part_hum / 100)

    voc_index = int(mac_payload[-16:-12], 16)

    air_temperature_raw = int(mac_payload[-8:-4], 16)

    integer_part_tem = int(str(air_temperature_raw)[:2])
    decimal_part_tem = int(str(air_temperature_raw)[2:])

    air_temperature = integer_part_tem + (decimal_part_tem / 100)

    # Value of current timestamp in UNIX format
    unix_timestamp = int(time.time())

    return [air_temperature, relative_humidity, voc_index, unix_timestamp]
