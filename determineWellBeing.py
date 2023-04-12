# Implement a function that returns the literal description of the well-being status based on the VOC index
def get_well_being_description(value):
    if 0 <= value <= 150:
        return "Good"
    elif 151 <= value <= 230:
        return "Moderate"
    elif 231 <= value <= 300:
        return "Unhealthy for Sensitive Groups"
    elif 301 <= value <= 400:
        return "Unhealthy"
    elif 401 <= value <= 450:
        return "Very Unhealthy"
    elif 451 <= value <= 500:
        return "Hazardous"
    else:
        return "Invalid input value"


# Implement a function that fills null values in a row with the last non-null value, to protect from transmission errors
def protect_voc_null_values(all_wb):
    last_non_null = None
    for i in range(len(all_wb)):
        if all_wb[i] == 0 and last_non_null is not None:
            all_wb[i] = last_non_null
        elif all_wb[i] != 0:
            last_non_null = all_wb[i]
    return all_wb
