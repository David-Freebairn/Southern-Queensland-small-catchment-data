"""Joint runoff calibration across the three sites.
Shared: CN reduction at full cover, zero-till CN2 offset. Site-specific: base CN2.
Objective (David's): cumulative P:O = 1 per catchment, with 3-day NSE as a secondary term.
Usage: python joint_runoff.py A|B     A = cn_red shared by all 3 sites; B = shared by GM+GW, Wallumbilla own."""
import sys, json, time
import numpy as np, pandas as pd
from scipy.optimize import minimize
from multiprocessing import Pool
import joint_setup as J

MODE = sys.argv[1] if len(sys.argv) > 1 else 'A'
SITES = ['Greenmount', 'Greenwood', 'Wallumbilla']

def params_of(x):
    cn2 = dict(zip(SITES, x[:3])); cn_red, zt = x[3], x[4]
    out = {}
    for s in SITES:
        out[s] = dict(cn2=cn2[s], cn_red=cn_red, zt_cn2_offset=zt)
    if MODE == 'B':
        out['Wallumbilla']['cn_red'] = x[5]
    return out

def one(args):
    i, over = args
    k = J.CATS[i]; r = J.simulate(k, over)
    o = k['ro']; s = r.runoff.reindex(o.index)
    o3 = o.rolling(3, center=True, min_periods=1).sum(); s3 = s.rolling(3, center=True, min_periods=1).sum()
    return dict(po=float(s.sum() / o.sum()), nse3=J.nse(o3, s3), o3=o3.values, s3=s3.values)

POOL = None
def evaluate(x):
    P = params_of(x)
    res = POOL.map(one, [(i, P[k['site']]) for i, k in enumerate(J.CATS)])
    O3 = np.concatenate([r['o3'] for r in res]); S3 = np.concatenate([r['s3'] for r in res])
    return res, J.nse(O3, S3)

def objective(x):
    res, pn = evaluate(x)
    dev = sum(abs(r['po'] - 1) for r in res)
    return dev + 0.5 * (1 - pn)

if __name__ == '__main__':
    POOL = Pool(4)
    t0 = time.time()
    ref = [J.P_GM['cn2'], J.P_GW['cn2'], J.P_WB['cn2']]
    x0 = ref + [14.6, 5.2] + ([8.0] if MODE == 'B' else [])
    if MODE == 'A':
        x0[3] = 12.5
    r0, n0 = evaluate(x0)
    print('start', round(objective(x0), 3), [round(r['po'], 2) for r in r0], round(n0, 3), flush=True)
    m = minimize(objective, x0, method='Nelder-Mead',
                 options={'maxfev': 260, 'xatol': 0.05, 'fatol': 1e-3, 'initial_simplex': None})
    res, pn = evaluate(m.x)
    out = dict(mode=MODE, x=list(m.x), fun=float(m.fun), pooled_nse3=pn,
               params={s: v for s, v in params_of(m.x).items()},
               cats=[dict(site=k['site'], name=k['name'], po=r['po'], nse3=r['nse3']) for k, r in zip(J.CATS, res)])
    json.dump(out, open(f'/home/claude/joint/runoff_{MODE}.json', 'w'), indent=1, default=float)
    print(MODE, 'done', round(time.time() - t0), 's', np.round(m.x, 2), round(m.fun, 3), round(pn, 3))
    for c in out['cats']:
        print(f"  {c['site']:12s} {c['name']:13s} P:O {c['po']:.2f}  NSE3 {c['nse3']:.2f}")
