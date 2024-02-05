from pulp import *
from multiprocessing import cpu_count
from datetime import datetime

from determineThermalComfort import get_pmv_value


def find_temp_for_desired_pmv(target_pmv, clo, rh=50, met=1.1, vr=0, wme=0, tolerance=0.01, max_iterations=100):
    lower_bound = 10
    upper_bound = 35
    iteration = 0

    while iteration < max_iterations:
        tr_guess = (lower_bound + upper_bound) / 2
        tdb = tr_guess * 0.935
        calculated_pmv = get_pmv_value(tr_guess, tdb, rh, met, clo, vr, wme)

        if abs(calculated_pmv - target_pmv) <= tolerance:
            return round(tr_guess, 2)
        elif calculated_pmv < target_pmv:
            lower_bound = tr_guess
        else:
            upper_bound = tr_guess

        iteration += 1

    raise ValueError(f"Could not find a solution within tolerance after {max_iterations} iterations.")


def get_outdoor_temperature(cur, city):
    today = datetime.now().strftime('%Y-%m-%d')
    cur.execute('''
        SELECT *
        FROM user_outdoor_temperature
        WHERE town_name = %s
        AND date_recorded =%s
        ORDER BY date_recorded DESC
        LIMIT 1;
    ''', (city, today,))
    temperature_preferences = cur.fetchone()
    temperature_float_values = [float(value) for value in list(temperature_preferences[3:])]
    hourly_temperatures = {hour: value for hour, value in enumerate(temperature_float_values, start=1)}

    return hourly_temperatures


def outdoor_temp_to_indoor_temp(outdoor_temp):
    th_in_init = 20
    th_in = {0: th_in_init}
    thg_in = {}
    pmv_values = {}

    alpha, beta = 0.8569, 0.1431
    rh, met, clo, vr = 50, 1, 1.2, 0

    for t in range(1, 25):
        th_in[t] = alpha * th_in[t - 1] + beta * outdoor_temp[t]

        thg_in[t] = 0.935 * th_in[t]

        pmv = get_pmv_value(th_in[t], thg_in[t], rh, met, clo, vr, wme=0)
        pmv_values[t] = round(pmv, 2)

    return th_in, thg_in, pmv_values


def DSM_get_tariffs(prices_json):
    tariffs = {}
    for entry in prices_json:
        hour_index = int(entry['hour_index'])
        tariffs[hour_index] = float(entry['price'])
    return tariffs


def dsm_time_flexible_loads_slots(operation_time):
    T_start_j = {}
    T_end_j = {}

    # Assigning values based on your requirement
    T_start_j[1], T_end_j[1] = operation_time["dish_washer_time"]
    T_start_j[2], T_end_j[2] = operation_time["washing_machine_time"]
    T_start_j[3], T_end_j[3] = operation_time["tumble_drier_time"]

    return [T_start_j, T_end_j]


def dsm_phase_flexible_loads_const_slots(operation_time):
    T_start_k = {}
    T_end_k = {}

    # Assigning values based on your requirement
    T_start_k[1], T_end_k[1] = operation_time["water_heater_time"]

    return [T_start_k, T_end_k]


def dsm_phase_flexible_loads_diff_slots(operation_time):
    T_start_m = {}
    T_end_m = {}

    # Assigning values based on your requirement
    T_start_m[1], T_end_m[1] = operation_time["electric_vehicle_time"]

    return [T_start_m, T_end_m]


def dsm_solve_problem(T_start_j, T_end_j, T_start_m, T_end_m, T_start_k, T_end_k, min_temp, max_temp, out_temperatures, clo, pi_i):
    T, I = 1, range(1, 25)
    from app import get_account_loads
    loads_info = get_account_loads().get_json()

    dj = {1: int(loads_info['time_shiftable'][0][4]), 2: int(loads_info['time_shiftable'][1][4]),
          3: int(loads_info['time_shiftable'][2][4])}
    fjr = {1: {1: float(loads_info['time_shiftable'][0][3])}, 2: {1: float(loads_info['time_shiftable'][1][3])},
           3: {1: float(loads_info['time_shiftable'][2][3])}}

    b_i = {i: 0.4 for i in I}
    p_cont_i = {i: 10.5 for i in I}
    th_min, th_max = find_temp_for_desired_pmv(-2, clo), find_temp_for_desired_pmv(-1, clo)
    th_in_init, th_ext_init = 22, out_temperatures[1]
    th_ext = out_temperatures
    ind = outdoor_temp_to_indoor_temp(th_ext)
    print(ind)
    P_AC_nom = float(loads_info['ac_shiftable'][0][2])
    Q_k, E_k = {1: float(loads_info['phase_shiftable'][1][3])}, {1: float(loads_info['phase_shiftable'][1][6])}
    M, K, J = range(1, 2), range(1, 2), range(1, 4)
    S = 3
    Q_m_s = {(1, 1): float(loads_info['phase_shiftable'][0][3]), (1, 2): float(loads_info['phase_shiftable'][0][4]),
             (1, 3): float(loads_info['phase_shiftable'][0][5])}
    G_m = {1: float(loads_info['phase_shiftable'][0][6])}
    prob = LpProblem("Demand_Side_Management", LpMinimize)
    p_j = LpVariable.dicts("p", ((j, t) for t in I for j in range(1, len(J) + 1)), lowBound=0)
    w = LpVariable.dicts("w", ((j, r, t) for t in I for j in range(1, len(J) + 1) for r in
                               range(1, dj[j] + 1)), cat='Binary')

    u_kt = LpVariable.dicts("u_kt", ((k, t) for k in K for t in range(T_start_k[k], T_end_k[k] + 1)), cat='Binary')
    q_kt = LpVariable.dicts("q_kt", ((k, t) for k in K for t in range(1, len(I) + 1)), lowBound=0)

    x_mt_s = LpVariable.dicts("x_mt_s", ((m, t, s) for m in M for t in range(1, len(I) + 1) for s in
                                         range(1, S + 1)), cat='Binary')
    y_mt = LpVariable.dicts("y_mt", ((m, t) for m in M for t in range(1, len(I) + 1)), lowBound=0)

    th_in = LpVariable.dicts("θ_in", I)
    aq_in = LpVariable.dicts("aq_in", I)

    delta_t = LpVariable.dicts("δ", ((t, s) for t in I for s in range(1, 6)), cat='Binary', lowBound=0)
    lamda_t = LpVariable.dicts("λ", ((t, s) for t in I for s in range(1, 6)), cat='Binary', lowBound=0)

    v_t = LpVariable.dicts("v", I, lowBound=0)

    p_AC = LpVariable.dicts("P_AC", I)

    objective_function = (
            lpSum([pi_i[t] * (b_i[t] + lpSum(p_j[j, t] for j in J) + p_AC[t]) for t in I]) +
            lpSum([pi_i[t] * q_kt[k, t] for k in K for t in I]) +
            lpSum([pi_i[t] * y_mt[m, t] for m in M for t in I]) +
            lpSum([0.2 * v_t[t] for t in I])
    )

    prob += objective_function, "Total Cost"

    '''Constraint 2'''
    for j in J:
        for t in I:
            if T_start_j[j] <= t <= T_end_j[j]:
                prob += lpSum([fjr[j][r] * w[j, r, t] for r in range(1, dj[j])]) == p_j[
                    j, t], f"PowerConstraint_{j}_{t}"

    '''Constraint 3'''
    for j in J:
        for t in I:
            if t < T_start_j[j] or t > T_end_j[j]:
                prob += p_j[j, t] == 0, f"Zero_Power_{j}_{t}"

    '''Constraint 4'''
    for j in J:
        for t in I:
            if T_start_j[j] <= t <= T_end_j[j]:
                prob += lpSum(w[j, r, t] for r in range(1, dj[j] + 1)) <= 1, f"MaxDurationConstraint_{j}_{t}"

    '''Constraint 5'''
    for j in J:
        for t in range(T_start_j[j], T_end_j[j]):
            for r in range(1, dj[j]):
                prob += w[j, r + 1, t + 1] >= w[j, r, t], f"ContinuityConstraint_{j}_{t}_{r}"

    '''Constraint 6'''
    for j in J:
        for r in range(1, dj[j] + 1):
            prob += lpSum(
                w[j, r, t] for t in range(T_start_j[j], T_end_j[j] + 1)) == 1, f"ExactlyOnceConstraint_{j}_{r}"

    '''Constraint 7'''
    for j in J:
        prob += lpSum(
            w[j, 1, t] for t in range(T_start_j[j], T_end_j[j] - dj[j] + 2)) >= 1, f"StartWindowConstraint_{j}"

    '''Constraint 10'''
    for k in K:
        for t in range(T_start_k[k], T_end_k[k] + 1):
            prob += q_kt[k, t] == u_kt[k, t] * Q_k[k], f"Power_Consumption_{k}_{t}"

    '''Constraint 11'''
    for k in K:
        for t in range(1, len(I) + 1):
            if t < T_start_k[k] or t > T_end_k[k]:
                prob += q_kt[k, t] == 0, f"Zero_Power_Outside_Comfort_{k}_{t}"

    '''Constraint 12'''
    for k in K:
        prob += lpSum(q_kt[k, t] for t in range(T_start_k[k], T_end_k[k] + 1)) == E_k[k], f"Total_Energy_{k}"

    '''Constraint 15'''
    for m in M:
        for t in range(T_start_m[m], T_end_m[m] + 1):
            prob += y_mt[m, t] == lpSum(
                x_mt_s[m, t, s] * Q_m_s[m, s] for s in range(1, S + 1)), f"Power_Level_Consumption_{m}_{t}"

    '''Constraint 16'''
    for m in M:
        for t in range(T_start_m[m], T_end_m[m] + 1):
            prob += lpSum(x_mt_s[m, t, s] for s in range(1, S + 1)) <= 1, f"One_Power_Level_Active_{m}_{t}"

    '''Constraint 17'''
    for m in M:
        prob += lpSum(y_mt[m, t] for t in range(T_start_m[m], T_end_m[m] + 1)) == G_m[m], f"Total_Energy_G_{m}"

    '''Constraint 18'''
    for m in M:
        for t in range(1, T_start_m[m]):
            prob += y_mt[m, t] == 0, f"Zero_Power_Before_{m}_{t}"
        for t in range(T_end_m[m] + 1, T + 1):
            prob += y_mt[m, t] == 0, f"Zero_Power_After_{m}_{t}"

    alpha, beta, gamma = 0.8569, 0.1431, 2.775
    for t in I:
        '''Constraint 21'''
        if t > 1:
            prob += th_in[t] == alpha * th_in[t - 1] + beta * th_ext[t - 1] + gamma * p_AC[t], f"TempModel_{t}"
        elif t == 1:
            prob += th_in[t] == alpha * th_in_init + beta * th_ext_init + gamma * p_AC[t], f"TempModel_{t}"

        '''Constraint 22'''
        prob += p_AC[t] == (
                0.2 * delta_t[t, 1] + 0.4 * delta_t[t, 2] + 0.6 * delta_t[t, 3] + 0.8 * delta_t[t, 4] + delta_t[
            t, 5]) * P_AC_nom, f"PowerModel_{t}"
        '''Constraint 23'''
        prob += lpSum(delta_t[t, s] for s in range(1, 6)) <= 1, f"ACLevelSelection_{t}"
        '''Constraint 24'''
        prob += v_t[t] >= th_min - th_in[t], f"MinConstraintThermalComfort_{t}"
        '''Constraint 25'''
        prob += v_t[t] >= th_in[t] - th_max, f"MaxConstraintThermalComfort_{t}"

    for t in I:
        prob += (
                        b_i[t] +
                        lpSum(p_j[j, t] for j in J) +
                        lpSum(q_kt[k, t] for k in K) +
                        lpSum(y_mt[m, t] for m in M) +
                        p_AC[t]
                ) <= p_cont_i[t], f"Power_Limit_Constraint_{t}"

    solver = pulp.PULP_CBC_CMD(threads=cpu_count())

    prob.solve(solver)

    results = {
        "Time-Shiftable Loads": [],
        "Power Constant Loads": [],
        "Power Variable Loads": [],
        "Air Conditioning Power and Temperature": []
    }

    threshold = 0.01

    for j in J:
        for r in range(1, dj[j] + 1):
            for t in I:
                if w[(j, r, t)].varValue == 1:
                    results["Time-Shiftable Loads"].append((j, t, r))

    for k in K:
        for t in range(T_start_k[k], T_end_k[k] + 1):
            if q_kt[(k, t)].varValue > threshold:
                results["Power Constant Loads"].append((k, t, q_kt[(k, t)].varValue))

    for m in M:
        for t in I:
            if y_mt[(m, t)].varValue > threshold:
                results["Power Variable Loads"].append((m, t, y_mt[(m, t)].varValue))

    for t in I:
        results["Air Conditioning Power and Temperature"].append((t, p_AC[t].varValue, th_in[t].varValue))

    return results
