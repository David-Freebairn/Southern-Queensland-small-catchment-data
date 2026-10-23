"""Greenwood runoff/sediment observations: daily series per treatment, event grouping, back-calculated CN."""
import numpy as np
import pandas as pd
import openpyxl
import gw_setup as G

X = G.D + "Greenwood_runoff_sediment_data.xlsx"
ws = openpyxl.load_workbook(X, data_only=True).worksheets[0]
rows = [r for r in ws.iter_rows(values_only=True)]
hi = next(i for i, r in enumerate(rows) if r[0] == "Date")
obs = pd.DataFrame(rows[hi + 1:], columns=rows[hi]).dropna(subset=["Date"]).set_index("Date")
obs.index = pd.to_datetime(obs.index)
obs = obs.apply(pd.to_numeric, errors="coerce")

PREFIX = {"Burnt": "Burnt", "Incorporated": "Incorp", "Mulch": "Mulch", "Zero till": "Zero_till"}
OBS_START = {"Burnt": "1979-01-01", "Incorporated": "1979-01-01", "Mulch": "1979-01-01", "Zero till": "1980-11-01"}
OBS_END = "1984-04-30"


def daily(name):
    """Daily observed runoff (mm), soil movement (t/ha), suspended sediment (t/ha); unlisted days = 0."""
    p = PREFIX[name]
    idx = pd.date_range(OBS_START[name], OBS_END, freq="D")
    q = obs[f"{p}_Runoff_mm"].reindex(idx).fillna(0.0)
    sm = obs[f"{p}_Soil_movement_t_ha"].reindex(idx).fillna(0.0)
    ss = obs[f"{p}_Suspended_sediment_t_ha"].reindex(idx).fillna(0.0)
    return pd.DataFrame({"runoff": q, "soil_movement": sm, "suspended": ss})


def events(o_q, s_q, rain, gap=2):
    """Group days with observed or simulated runoff into events; days within `gap` days join one event."""
    act = ((o_q > 0) | (s_q > 0.5)).values
    idx = o_q.index
    groups, cur, last = [], [], None
    for i, a in enumerate(act):
        if a:
            if cur and (i - last) > gap:
                groups.append(cur); cur = []
            cur.append(i); last = i
    if cur:
        groups.append(cur)
    out = []
    for g in groups:
        sl = slice(max(0, g[0] - 1), g[-1] + 1)       # include the day before (rain often a day early)
        out.append(dict(start=idx[g[0]], end=idx[g[-1]], days=idx[sl]))
    return out


def back_cn(P, Q):
    """Curve number that reproduces runoff Q from rain P with Ia = 0.2 S."""
    if P <= 0 or Q <= 0 or Q >= P:
        return np.nan
    S = 5.0 * (P + 2 * Q - np.sqrt(4 * Q * Q + 5 * P * Q))
    return 25400.0 / (S + 254.0)
