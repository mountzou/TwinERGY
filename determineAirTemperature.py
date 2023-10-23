# Get the value of air temperature from the corresponding measurement from the wearable device
def get_air_temperature(t_wearable):
    c = 4.41 ** (-12)

    air_temperature_CFD = round(t_wearable / (1 + 0.5 * c ** 0.03) + 2 * c ** 0.03 / (1 + 0.5 * c ** 0.03), 2)

    return air_temperature_CFD


def get_t_wearable(air_temperature_CFD):
    c = 4.41 ** (-12)
    A = 1 + 0.5 * c ** 0.03
    B = 2 * c ** 0.03

    t_wearable = A * air_temperature_CFD - B

    return t_wearable
