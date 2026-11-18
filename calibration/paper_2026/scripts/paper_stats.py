"""Fit statistics, original vs revised, from runs.pkl (paper_runs.py)."""
import sys, pickle
sys.path.insert(0, '/home/claude/Watbal2026')
import numpy as np, pandas as pd
from core.vege import read_vege
from core.run_simulation import _make_vege_fn
from paper_runs_meta import VEGE, W, B_SS

R = pickle.load(open('/home/claude/paper/runs.pkl', 'rb'))

def nse(o, p):
    m = o.notna() & p.notna(); o, p = o[m], p[m]
    return float(1 - ((o - p) ** 2).sum() / ((o - o.mean()) ** 2).sum()) if len(o) > 2 and o.var() > 0 else np.nan

def r2(o, p):
    m = o.notna() & p.notna()
    return float(np.corrcoef(o[m], p[m])[0, 1] ** 2) if m.sum() > 2 else np.nan

def r3(x): return x.rolling(3, center=True, min_periods=1).sum()

def monthly(x): return x.resample('MS').sum()

def series(site, trt):
    d = R[(site, trt)]
    fn = _make_vege_fn(read_vege(W + 'Vegetation descriptions/Contour bay catchments 2026/' + VEGE[(site, trt)] + '.vege'))
    out = {}
    for v in ('old', 'new'):
        r = d[v].copy(); r.index = pd.to_datetime(r.index) if not isinstance(r.index, pd.DatetimeIndex) else r.index
        if 'date' in r.columns: r = r.set_index(pd.to_datetime(r['date']))
        tot = np.array([fn(int(dd.dayofyear))[1] for dd in r.index]) * 100
        q = r.runoff
        if v == 'new':
            ss = pd.Series(np.where(q > 1, d['A_new'] * np.exp(-B_SS * np.minimum(tot, 100)) * q / 100, 0.0), index=r.index)
        else:
            ss = r.erosion * d['sdr_old']
        out[v] = pd.DataFrame({'runoff': q, 'sm': r.erosion, 'ss': ss, 'paw': r.pasw, 'cover': tot}, index=r.index)
    return out, d['obs']

rows, ts = [], {}
for (site, trt) in R:
    m, ob = series(site, trt); ts[(site, trt)] = (m, ob)
    for v in ('old', 'new'):
        md = m[v]; row = dict(site=site, treatment=trt, model='Original' if v == 'old' else 'Revised')
        o = ob['ro']; p = md.runoff.reindex(o.index)
        row.update(runoff_obs_mm=o.sum(), runoff_pred_mm=p.sum(), runoff_PO=p.sum() / o.sum(), runoff_NSE_3day=nse(r3(o), r3(p)),
                   runoff_R2_monthly=r2(monthly(o), monthly(p)), runoff_NSE_monthly=nse(monthly(o), monthly(p)), runoff_days=len(o))
        if ob['sm'] is not None:
            o = ob['sm']; p = md.sm.reindex(o.index)
            row.update(sm_obs_t_ha=o.sum(), sm_pred_t_ha=p.sum(), sm_PO=p.sum() / o.sum(), sm_NSE_3day=nse(r3(o), r3(p)),
                       sm_R2_monthly=r2(monthly(o), monthly(p)))
        o = ob['ss']; p = md.ss.reindex(o.index)
        row.update(ss_obs_t_ha=o.sum(), ss_pred_t_ha=p.sum(), ss_PO=p.sum() / o.sum(), ss_NSE_3day=nse(r3(o), r3(p)),
                   ss_R2_monthly=r2(monthly(o), monthly(p)))
        o = ob['paw']; p = md.paw.reindex(o.index)
        mm = o.notna() & p.notna()
        row.update(paw_n=int(mm.sum()), paw_RMSE_mm=float(np.sqrt(((p - o)[mm] ** 2).mean())), paw_bias_mm=float((p - o)[mm].mean()),
                   paw_R2=r2(o, p), paw_NSE=nse(o, p))
        rows.append(row)
S = pd.DataFrame(rows)

# pooled by site and overall: totals for P:O, concatenated daily series for NSE / R2
def pooled(keys, label_site):
    out = []
    for v, lab in (('old', 'Original'), ('new', 'Revised')):
        row = dict(site=label_site, treatment='All', model=lab)
        for var, ok, mk in [('runoff', 'ro', 'runoff'), ('sm', 'sm', 'sm'), ('ss', 'ss', 'ss')]:
            O, P, O3, P3, OM, PM = [], [], [], [], [], []
            for k in keys:
                m, ob = ts[k]
                if ob[ok] is None: continue
                o = ob[ok]; p = m[v][mk].reindex(o.index)
                O.append(o); P.append(p); O3.append(r3(o)); P3.append(r3(p)); OM.append(monthly(o)); PM.append(monthly(p))
            if not O: continue
            o, p = pd.concat(O), pd.concat(P)
            pre = {'runoff': 'runoff', 'sm': 'sm', 'ss': 'ss'}[var]
            row[f'{pre}_PO'] = p.sum() / o.sum()
            row[f'{pre}_NSE_3day'] = nse(pd.concat(O3).reset_index(drop=True), pd.concat(P3).reset_index(drop=True))
            row[f'{pre}_R2_monthly'] = r2(pd.concat(OM).reset_index(drop=True), pd.concat(PM).reset_index(drop=True))
        O, P = [], []
        for k in keys:
            m, ob = ts[k]; o = ob['paw']; p = m[v].paw.reindex(o.index); O.append(o); P.append(p)
        o, p = pd.concat(O).reset_index(drop=True), pd.concat(P).reset_index(drop=True); mm = o.notna() & p.notna()
        row.update(paw_n=int(mm.sum()), paw_RMSE_mm=float(np.sqrt(((p - o)[mm] ** 2).mean())), paw_bias_mm=float((p - o)[mm].mean()), paw_R2=r2(o, p))
        out.append(row)
    return out

P = []
for site in ('Greenmount', 'Greenwood', 'Wallumbilla'):
    P += pooled([k for k in ts if k[0] == site], site)
P += pooled(list(ts), 'All sites')
S.to_csv('/home/claude/paper/stats_by_catchment.csv', index=False)
pd.DataFrame(P).to_csv('/home/claude/paper/stats_pooled.csv', index=False)
pickle.dump(ts, open('/home/claude/paper/series.pkl', 'wb'))
pd.set_option('display.width', 250)
print(S[['site', 'treatment', 'model', 'runoff_PO', 'runoff_NSE_3day', 'runoff_R2_monthly', 'sm_PO', 'sm_NSE_3day', 'ss_PO', 'ss_NSE_3day', 'paw_RMSE_mm', 'paw_bias_mm', 'paw_R2']].round(2).to_string())
print(pd.DataFrame(P).round(2).to_string())
