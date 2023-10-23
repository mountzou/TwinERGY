# Implement a function that returns the literal description of the well-being status based on the VOC index
def get_well_being_description(value):
    if 0 <= value <= 200:
        return "Excellent"
    elif 201 <= value <= 500:
        return "Good"
    elif 501 <= value <= 1000:
        return "Moderate"
    elif 1001 <= value <= 3000:
        return "Poor"
    elif 3001 <= value <= 4500:
        return "Very Unhealthy"
    elif 4501 <= value <= 5000:
        return "Hazardous"
    else:
        return "Invalid input value"
