import base64
import time


# Function that decodes the bytes of payload from the wearable device
def decodeMACPayload(payload):
    # Value of MAC Payload in hex format
    mac_payload = base64.b64decode(payload).hex()

    # Get the integer part and the decimal part of the air temperature from the payload
    integer_temperature = int(str(int(mac_payload[132:136], 16))[:2])
    decimal_temperature = int(str(int(mac_payload[132:136], 16))[2:])

    # Determine the value of air temperature
    air_temperature = integer_temperature + 0.01*decimal_temperature

    # Get the integer part and the decimal part of the relative humidity from the payload
    integer_humidity = int(str(int(mac_payload[136:140], 16))[:2])
    decimal_humidity = int(str(int(mac_payload[136:140], 16))[2:])

    # Determine the value of relative humidity
    relative_humidity = integer_humidity + 0.01*decimal_humidity

    # Value of total energy expenditure in kCal
    decimal_energy_exp = int(mac_payload[34:42], 16) * 0.1

    # Get the value of VOC index from the payload
    voc_index = int(mac_payload[124:128], 16)

    # Get the value of current timestamp in UNIX format
    unix_timestamp = int(time.time())

    return [air_temperature, relative_humidity, voc_index, unix_timestamp, decimal_energy_exp]
