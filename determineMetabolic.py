# Implement a function with input the calories of the last 24 hours and returns the met values of each session
def dailyMetabolic(latest_metabolic):
    sessions = [[]]
    sessions_met = []

    # Detect each specific session of the last 24 hours
    for obs, ts in latest_metabolic:
        if sessions[-1] and obs < sessions[-1][-1][0]:
            sessions.append([])
        sessions[-1].append((obs, ts))

    # Specify the metabolic rate and the corresponding timestamp difference of each session
    for session in sessions:
        start_ts, start_obs = session[0][1], session[0][0]
        end_ts, end_obs = session[-1][1], session[-1][0]
        sessions_met.append(round((end_obs * 1000) / (25 * (end_ts - start_ts)), 2))
        print(f"Session from {start_ts} ({start_obs}) to {end_ts} ({end_obs})")

    # Replace met with the min and max acceptable values in case of less or higher than the corresponding boundary ones
    sessions_met = [0.9 if x < 0.9 else 2.0 if x > 2.0 else x for x in sessions_met]

    return sessions_met


# Implement a function with input the calories of the last 24 hours and returns the met values of each session
def dailyMetabolicTime(latest_metabolic):
    sessions = [[]]
    sessions_met_time = []

    # Detect each specific session of the last 24 hours
    for obs, ts in latest_metabolic:
        if sessions[-1] and obs < sessions[-1][-1][0]:
            sessions.append([])
        sessions[-1].append((obs, ts))

    # Specify the metabolic rate and the corresponding timestamp difference of each session
    for session in sessions:
        start_ts, start_obs = session[0][1], session[0][0]
        end_ts, end_obs = session[-1][1], session[-1][0]
        sessions_met_time.append([session[0][1], session[-1][1]])

    sessions_met = [t[i] for t in sessions_met_time for i in range(2)]

    return sessions_met
