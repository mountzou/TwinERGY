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
