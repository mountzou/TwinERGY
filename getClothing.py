from datetime import datetime

# A function that returns the value of the current season
def get_season():
    now = datetime.now()
    month = now.month
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:
        return "autumn"

def getWinterClo(cur, wearable_id):
    cur.execute('''
        SELECT user_clo
        FROM user_clo_winter
        WHERE wearable_id = %s;
    ''', (wearable_id,))
    winter_clo = cur.fetchone()

    return winter_clo


def getSummerClo(cur, wearable_id):
    cur.execute('''
        SELECT user_clo
        FROM user_clo_summer
        WHERE wearable_id = %s;
    ''', (wearable_id,))
    summer_clo = cur.fetchone()

    return summer_clo


def getSpringClo(cur, wearable_id):
    cur.execute('''
        SELECT user_clo
        FROM user_clo_spring
        WHERE wearable_id = %s;
    ''', (wearable_id,))
    spring_clo = cur.fetchone()

    return spring_clo


def getAutumnClo(cur, wearable_id):
    cur.execute('''
        SELECT user_clo
        FROM user_clo_autumn
        WHERE wearable_id = %s;
    ''', (wearable_id,))
    autumn_clo = cur.fetchone()

    return autumn_clo

def getUseClo(cur, wearable_id):
    current_season = get_season()
    if current_season == "winter":
        return getWinterClo(cur, wearable_id)
    elif current_season == "spring":
        return getSpringClo(cur, wearable_id)
    elif current_season == "summer":
        return getSummerClo(cur, wearable_id)
    else:
        return getAutumnClo(cur, wearable_id)