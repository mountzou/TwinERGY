import base64
import time

from determineAirTemperature import get_air_temperature


# Function that decodes the bytes of payload from the wearable device
def decodeMACPayload(payload):
    # Value of MAC Payload in hex format
    mac_payload = base64.b64decode(payload).hex()

    # Get the integer part and the decimal part of the air temperature from the payload
    integer_temperature, decimal_temperature = int(str(int(mac_payload[-8:-4], 16))[:2]), int(str(int(mac_payload[
                                                                                                      -8:-4], 16))[2:])
    air_temperature = integer_temperature + (decimal_temperature / 100)

    # Determine the value of air temperature based on the captured measurement from the wearable device
    # air_temperature = get_air_temperature(air_temperature)

    # Get the integer part and the decimal part of the relative humidity from the payload
    integer_humidity, decimal_humidity = int(str(int(mac_payload[-4:], 16))[:2]), int(str(int(mac_payload[-4:], 16))[
                                                                                      2:])
    relative_humidity = integer_humidity + (decimal_humidity / 100)

    # Value of total energy expenditure in kCal
    decimal_energy_exp = int(mac_payload[34:42], 16) * 0.1

    # Get the value of VOC index from the payload
    voc_index = int(mac_payload[-16:-12], 16)

    # Get the value of current timestamp in UNIX format
    unix_timestamp = int(time.time())

    return [air_temperature, relative_humidity, voc_index, unix_timestamp, decimal_energy_exp]
