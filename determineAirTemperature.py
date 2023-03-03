# Get the value of air temperature from the corresponding measurement from the wearable device
def get_air_temperature(t_wearable):
    c = 4.41 ** (-12)

    t_air = round(t_wearable / (1 + 0.5 * c ** 0.03) + 2 * c ** 0.03 / (1 + 0.5 * c ** 0.03), 2)

    return t_air
