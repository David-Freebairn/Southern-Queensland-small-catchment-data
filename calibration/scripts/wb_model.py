"""Compact PERFECT/HowLeaky-style daily soil water balance used as a stand-in for Waterbal2026.

Process order each day: (optional) soil-water reset to observation -> runoff (SCS-CN, AMC from
soil water, CN reduced by total cover) -> infiltration and saturation overflow -> drainage
cascade above field capacity -> soil evaporation (Ritchie 2-stage) -> transpiration (green cover
x pan evaporation, soil-water stress) -> erosion (Freebairn & Wockner sediment concentration).
"""
import math
import numpy as np
import pandas as pd

DEFAULTS = dict(
    cn2=86.0,          # bare-soil curve number (AMC II)
    cn_red=10.0,       # CN reduction at 100 % total cover
    U=4.0,             # stage-1 soil evaporation limit (mm)
    cona=4.0,          # stage-2 soil evaporation coefficient (mm/d^0.5)
    res_es=0.0,        # fractional reduction of potential soil evap at 100 % residue cover
    kc=1.0,            # transpiration coefficient: potential T = kc * green cover * pan evap
    sw_nostress=0.2,   # fraction of root-zone PAWC below which transpiration is reduced
    tue=25.0,          # transpiration efficiency (kg/ha/mm)
    hi=0.35,           # harvest index
    sed_f=0.4,         # lumped sediment factor (K*LS*P*SDR relative to the concentration curve)
    paw_scale=1.0,     # multiplier on (field capacity - wilting point)
)

GREEN_DAP = np.array([0, 6, 36, 67, 98, 128, 400])   # days after planting, from the .vege matrix
GREEN_PCT = np.array([0, 2, 15, 45, 80, 85, 85])


def crop_seasons(plant_harvest, end_default=150):
    """Pair each planting with the next harvest (last planting wins if replanted)."""
    ph = plant_harvest.sort_index()
    seasons, last_plant = [], None
    for d, row in ph.iterrows():
        if row.iloc[0] == 1:
            if last_plant is not None and (d - last_plant).days > 200:
                seasons.append((last_plant, last_plant + pd.Timedelta(days=end_default), np.nan))
            last_plant = d
        elif row.iloc[0] == 2 and last_plant is not None:
            seasons.append((last_plant, d, row.iloc[1]))
            last_plant = None
    if last_plant is not None:
        seasons.append((last_plant, last_plant + pd.Timedelta(days=end_default), np.nan))
    return seasons


def build_forcing(clim, cover_obs, seasons, start, end):
    idx = pd.date_range(start, end, freq="D")
    f = pd.DataFrame(index=idx)
    f["rain"] = clim["rain"].reindex(idx).fillna(0).values
    f["epan"] = clim["evap"].reindex(idx).fillna(0).values
    green = np.zeros(len(idx))
    crop = np.full(len(idx), -1)
    for k, (p, h, _) in enumerate(seasons):
        m = (idx >= p) & (idx < h)
        dap = (idx[m] - p).days.values
        green[m] = np.interp(dap, GREEN_DAP, GREEN_PCT) / 100
        crop[m] = k
    tot = cover_obs.reindex(cover_obs.index.union(idx)).interpolate("time").reindex(idx)
    tot = tot.bfill().ffill().values / 100
    tot = np.maximum(tot, green)
    f["green"], f["total_cover"], f["crop"] = green, tot, crop
    f["residue"] = np.clip((tot - green) / np.maximum(1 - green, 1e-6), 0, 1)
    return f


def run(soil, forcing, seasons, p=None, resets=None, paw0=None):
    q = dict(DEFAULTS)
    if p:
        q.update(p)
    depth = soil["depth"]
    thick = np.diff(np.concatenate([[0], depth]))
    nl = len(thick)
    wp = (soil["wp"] * thick).tolist()
    fc = ((soil["wp"] + (soil["fc"] - soil["wp"]) * q["paw_scale"]) * thick).tolist()
    sat = [max(s * t, f_) for s, t, f_ in zip(soil["sat"], thick, fc)]
    ad = (soil["airdry"] * thick).tolist()
    mdr = soil["maxdrain"].tolist()
    pawc = [fc[i] - wp[i] for i in range(nl)]
    pawc_tot = sum(pawc)
    D = depth[-1]
    top = np.concatenate([[0], depth[:-1]])
    wf = 1.016 * (np.exp(-4.16 * top / D) - np.exp(-4.16 * depth / D))
    wf = (wf / wf.sum()).tolist()

    cn2 = q["cn2"]
    sw = [wp[i] + pawc[i] * (paw0 / pawc_tot if paw0 is not None else 0.5) for i in range(nl)]
    sumes1, t2 = q["U"], 0.0
    resets = resets or {}

    rain = forcing["rain"].values; epan = forcing["epan"].values
    green = forcing["green"].values; totc = forcing["total_cover"].values
    resid = forcing["residue"].values; crop = forcing["crop"].values
    dates = forcing.index
    n = len(rain)
    out = np.zeros((n, 7))      # runoff, soilevap, transp, drainage, sediment, paw, overflow
    T_season = np.zeros(len(seasons))

    for d in range(n):
        if dates[d] in resets:
            frac = min(max(resets[dates[d]] / pawc_tot, 0.0), 1.0)
            sw = [wp[i] + pawc[i] * frac for i in range(nl)]
        P = rain[d]
        # --- runoff
        Q = 0.0
        if P > 0:
            cn = cn2 - q["cn_red"] * min(1.0, totc[d])
            cn1 = cn / (2.334 - 0.01334 * cn)
            smax = 254.0 * (100.0 / cn1 - 1.0)
            wet = sum(wf[i] * min(1.0, max(0.0, (sw[i] - wp[i]) / (sat[i] - wp[i]))) for i in range(nl))
            S = smax * (1.0 - wet)
            if P > 0.2 * S:
                Q = (P - 0.2 * S) ** 2 / (P + 0.8 * S)
        infil = P - Q
        # --- infiltration, saturation overflow
        room = sum(sat[i] - sw[i] for i in range(nl))
        over = 0.0
        if infil > room:
            over = infil - room
            infil = room
        w = infil
        for i in range(nl):
            if w <= 0:
                break
            add = min(w, sat[i] - sw[i])
            sw[i] += add
            w -= add
        Q += over
        # --- drainage cascade
        for i in range(nl):
            ex = sw[i] - fc[i]
            if ex > 0:
                dr = min(ex, mdr[i])
                if i < nl - 1:
                    dr = min(dr, sat[i + 1] - sw[i + 1])
                    sw[i + 1] += dr
                sw[i] -= dr
                if i == nl - 1:
                    out[d, 3] = dr
        # --- soil evaporation (Ritchie)
        if infil > 0:
            sumes1 = max(0.0, sumes1 - infil)
            if sumes1 < q["U"]:
                t2 = 0.0
        pot_es = epan[d] * (1 - green[d]) * (1 - q["res_es"] * resid[d])
        if sumes1 < q["U"]:
            es = min(pot_es, q["U"] - sumes1)
            sumes1 += es
            rem = pot_es - es
            if rem > 0 and sumes1 >= q["U"]:
                t2 += 1
                es2 = min(rem, q["cona"] * (math.sqrt(t2) - math.sqrt(t2 - 1)))
                es += es2
        else:
            t2 += 1
            es = min(pot_es, q["cona"] * (math.sqrt(t2) - math.sqrt(t2 - 1)))
        avail1 = sw[0] - ad[0]
        take1 = min(es, max(avail1, 0.0))
        sw[0] -= take1
        take2 = min(es - take1, max(0.5 * (sw[1] - ad[1]), 0.0))
        sw[1] -= take2
        es = take1 + take2
        # --- transpiration (roots through full profile once crop is established)
        tr = 0.0
        if crop[d] >= 0 and green[d] > 0:
            dap = (dates[d] - seasons[crop[d]][0]).days
            rd = min(D, 300 + (D - 300) * dap / 90.0)
            avail = []
            for i in range(nl):
                frac_in = min(1.0, max(0.0, (rd - top[i]) / thick[i]))
                avail.append(max(0.0, sw[i] - wp[i]) * frac_in)
            a_tot = sum(avail)
            cap = sum(pawc[i] * min(1.0, max(0.0, (rd - top[i]) / thick[i])) for i in range(nl))
            stress = min(1.0, (a_tot / cap) / q["sw_nostress"]) if cap > 0 else 0.0
            tr = min(q["kc"] * green[d] * epan[d] * stress, a_tot)
            if a_tot > 0:
                for i in range(nl):
                    sw[i] -= tr * avail[i] / a_tot
            T_season[crop[d]] += tr
        # --- sediment (Freebairn & Wockner concentration, g/L) -> t/ha
        sed = 0.0
        if Q > 0:
            c = totc[d] * 100
            conc = 16.52 - 0.46 * c + 0.0031 * c * c if c < 50 else max(0.0, 2.54 - 0.0254 * c)
            sed = conc * Q * 0.01 * q["sed_f"]
        out[d, 0] = Q; out[d, 1] = es; out[d, 2] = tr; out[d, 4] = sed
        out[d, 5] = sum(sw[i] - wp[i] for i in range(nl)); out[d, 6] = over

    res = pd.DataFrame(out, index=dates,
                       columns=["runoff", "soil_evap", "transp", "drainage", "sediment", "paw", "overflow"])
    res["rain"] = rain
    yields = np.array([q["tue"] * T * q["hi"] / 1000 for T in T_season])
    return res, yields, T_season
