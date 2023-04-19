import math


def get_calibrate_clo_value(clo, met):
    clo = clo * (0.6 + 0.4 / met)
    return round(clo, 2)


def get_calibrate_air_speed_value(vr, met):
    vr = (vr + 0.3 * (met - 1))
    return round(vr, 2)


def get_pmv_value(tr, tdb, rh, met, clo, vr, wme=0):
    pa = rh * 10 * math.exp(16.6536 - 4030.183 / (tdb + 235))
    clo = clo * (0.6 + 0.4 / met)
    vr = (vr + 0.3 * (met - 1))
    icl = 0.155 * clo
    m = met * 58.15
    w = wme * 58.15
    mw = m - w

    if icl <= 0.078:
        f_cl = 1 + (1.29 * icl)
    else:
        f_cl = 1.05 + (0.645 * icl)

    hcf = 12.1 * math.sqrt(vr)
    hc = hcf
    taa = tdb + 273
    tra = tr + 273
    t_cla = taa + (35.5 - tdb) / (3.5 * icl + 0.1)

    p1 = icl * f_cl
    p2 = p1 * 3.96
    p3 = p1 * 100
    p4 = p1 * taa
    p5 = (308.7 - 0.028 * mw) + (p2 * (tra / 100.0) ** 4)
    xn = t_cla / 100
    xf = t_cla / 50
    eps = 0.00015

    n = 0
    while abs(xn - xf) > eps:
        xf = (xf + xn) / 2
        hcn = 2.38 * abs(100.0 * xf - taa) ** 0.25
        if hcf > hcn:
            hc = hcf
        else:
            hc = hcn
        xn = (p5 + p4 * hc - p2 * xf ** 4) / (100 + p3 * hc)
        n += 1
        if n > 150:
            raise StopIteration("Max iterations exceeded")

    tcl = 100 * xn - 273

    hl1 = 3.05 * 0.001 * (5733 - (6.99 * mw) - pa)

    if mw > 58.15:
        hl2 = 0.42 * (mw - 58.15)
    else:
        hl2 = 0

    hl3 = 1.7 * 0.00001 * m * (5867 - pa)

    hl4 = 0.0014 * m * (34 - tdb)

    hl5 = 3.96 * f_cl * (xn ** 4 - (tra / 100.0) ** 4)

    hl6 = f_cl * hc * (tcl - tdb)

    ts = 0.303 * math.exp(-0.036 * m) + 0.028
    pmv = round(ts * (mw - hl1 - hl2 - hl3 - hl4 - hl5 - hl6), 2)

    return pmv


def get_pmv_status(pmv):
    status_dict = {
        (-2.5, -1.5): 'Cool',
        (-1.5, -0.5): 'Slightly Cool',
        (-0.5, 0.5): 'Neutral',
        (0.5, 1.5): 'Slightly Warm',
        (1.5, 2.5): 'Warm'
    }
    for prange, status in status_dict.items():
        if prange[0] <= pmv < prange[1]:
            return status
    return 'Cold' if pmv < -2.5 else 'Hot' if pmv > 2.5 else '-'
