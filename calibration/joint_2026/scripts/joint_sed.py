"""Joint sediment calibration, offline from the jointly calibrated daily runoff and total cover.
Soil movement (Greenmount, Greenwood): sed = conc(cover) * LS * K * Q / 10 for Q > 1 mm (Watbal2026 form, no season term).
Suspended sediment (all three sites):  ss = A * exp(-bT*cover%) * LS^x * Q / 1e5  (A in mg/L) for Q > 1 mm.
Objective: cumulative P:O = 1 per catchment (sum |P:O-1|), with 3-day-sum NSE as a light secondary term.
Usage: python joint_sed.py A|B   (which runoff calibration to use)"""
import sys, json
import numpy as np, pandas as pd
from scipy.optimize import minimize, differential_evolution
import joint_setup as J

MODE = sys.argv[1] if len(sys.argv) > 1 else 'A'
OBJ = sys.argv[2] if len(sys.argv) > 2 else 'abs'
R = json.load(open(f'/home/claude/joint/runoff_{MODE}.json'))
SIM = {}
for k in J.CATS:
    r = J.simulate(k, R['params'][k['site']])
    SIM[(k['site'], k['name'])] = r

def perfect_conc(c):
    return np.maximum(0, np.where(c < 50, 16.52 - 0.46 * c + 0.0031 * c * c, -0.0254 * c + 2.54))

_C = {}
def series(k, idx):
    key = (k['site'], k['name'], len(idx), idx[0])
    if key in _C: return _C[key]
    r = SIM[(k['site'], k['name'])].reindex(idx)
    q = r.runoff.values; cov = np.minimum(100, r.total_cover.values * 100)
    _C[key] = (q, cov)
    return q, cov

def optimise(obj, x0):
    B = []
    for v in x0:     # bounds by parameter type: coefficients (0..0.2), log K/A (+-3 around start), LS exponent
        if v == 0.0: B.append((-1.5, 1.5))
        elif abs(v) < 0.5 and v > 0: B.append((0.0, 0.2))
        else: B.append((v - 3, v + 3))
    r = differential_evolution(obj, B, seed=3, popsize=20, maxiter=150, tol=1e-7, polish=False, init='sobol')
    m = minimize(obj, r.x, method='Nelder-Mead', options={'maxfev': 2000, 'xatol': 1e-6, 'fatol': 1e-8})
    return m if m.fun <= r.fun else r

# ---------------- soil movement ----------------
SMK = [k for k in J.CATS if 'sm_win' in k]
def sm_pred(k, form, b, K):
    idx = k['sm_win'].index; q, cov = series(k, idx)
    conc = perfect_conc(cov) if form == 'perfect' else 16.52 * np.exp(-b * cov)
    return pd.Series(np.where(q > 1, conc * J.LS[k['site']] * K * q / 10, 0.0), index=idx)

def score(cats, predf, obskey):
    dev, O3, S3, out = 0, [], [], []
    for k in cats:
        o = k[obskey]; s = predf(k)
        po = s.sum() / o.sum(); dev += (np.log(max(po, 1e-3)) ** 2 if OBJ == 'log2' else abs(po - 1))
        o3 = o.rolling(3, center=True, min_periods=1).sum(); s3 = s.rolling(3, center=True, min_periods=1).sum()
        O3 += list(o3); S3 += list(s3)
        out.append(dict(site=k['site'], name=k['name'], obs=float(o.sum()), sim=float(s.sum()), po=float(po), nse3=J.nse(o3, s3)))
    return dev, J.nse(O3, S3), out

def fit_sm(variant):
    if variant == 'joint':        # shared b, single K
        def pf(x): return lambda k: sm_pred(k, 'exp', x[0], np.exp(x[1]))
        x0 = [0.05, np.log(0.6)]
    elif variant == 'perfect':    # PERFECT curve, single K
        def pf(x): return lambda k: sm_pred(k, 'perfect', 0, np.exp(x[0]))
        x0 = [np.log(0.6)]
    elif variant == 'site':       # b and K per site
        def pf(x):
            m = {'Greenmount': (x[0], np.exp(x[1])), 'Greenwood': (x[2], np.exp(x[3]))}
            return lambda k: sm_pred(k, 'exp', *m[k['site']])
        x0 = [0.05, np.log(0.6), 0.08, np.log(0.8)]
    elif variant == 'joint_siteK':  # shared b, K per site
        def pf(x):
            m = {'Greenmount': np.exp(x[1]), 'Greenwood': np.exp(x[2])}
            return lambda k: sm_pred(k, 'exp', x[0], m[k['site']])
        x0 = [0.05, np.log(0.6), np.log(0.6)]
    obj = lambda x: (lambda d, n, _: d + 0.25 * (1 - n))(*score(SMK, pf(x), 'sm_win'))
    m = optimise(obj, x0)
    d, n, out = score(SMK, pf(m.x), 'sm_win')
    return dict(variant=variant, x=list(m.x), dev=d, nse3=n, cats=out, pf=pf(m.x))

# ---------------- suspended ----------------
def ss_pred(k, A, bT, x_ls):
    idx = k['ss_win'].index; q, cov = series(k, idx)
    return pd.Series(np.where(q > 1, A * np.exp(-bT * cov) * J.LS[k['site']] ** x_ls * q / 1e5, 0.0), index=idx)

def fit_ss(variant):
    S3 = ['Greenmount', 'Greenwood', 'Wallumbilla']
    if variant == 'joint':
        def pf(x): return lambda k: ss_pred(k, np.exp(x[0]), x[1], 0.0)
        x0 = [np.log(7000), 0.02]
    elif variant == 'joint_LS':
        def pf(x): return lambda k: ss_pred(k, np.exp(x[0]), x[1], x[2])
        x0 = [np.log(7000), 0.02, 0.0]
    elif variant == 'siteA':
        def pf(x):
            A = dict(zip(S3, np.exp(x[:3])))
            return lambda k: ss_pred(k, A[k['site']], x[3], 0.0)
        x0 = [np.log(7000)] * 3 + [0.02]
    elif variant == 'site':
        def pf(x):
            A = dict(zip(S3, np.exp(x[:3]))); b = dict(zip(S3, x[3:]))
            return lambda k: ss_pred(k, A[k['site']], b[k['site']], 0.0)
        x0 = [np.log(7000)] * 3 + [0.02] * 3
    obj = lambda x: (lambda d, n, _: d + 0.25 * (1 - n))(*score(J.CATS, pf(x), 'ss_win'))
    m = optimise(obj, x0)
    d, n, out = score(J.CATS, pf(m.x), 'ss_win')
    return dict(variant=variant, x=list(m.x), dev=d, nse3=n, cats=out, pf=pf(m.x))

if __name__ == '__main__':
    res = {'sm': {}, 'ss': {}}
    for v in ['perfect', 'site', 'joint_siteK', 'joint']:
        f = fit_sm(v); res['sm'][v] = f
        print('SM', v, np.round(f['x'], 4), 'dev %.3f nse3 %.3f' % (f['dev'], f['nse3']),
              [f"{c['site'][:5]}-{c['name'][:4]} {c['po']:.2f}" for c in f['cats']])
    for v in ['joint', 'joint_LS', 'siteA', 'site']:
        f = fit_ss(v); res['ss'][v] = f
        print('SS', v, np.round(f['x'], 4), 'dev %.3f nse3 %.3f' % (f['dev'], f['nse3']),
              [f"{c['site'][:5]}-{c['name'][:4]} {c['po']:.2f}" for c in f['cats']])
    # cumulative series for plots (chosen joint forms)
    cum = []
    smj, ssj = res['sm']['joint']['pf'], res['ss']['joint']['pf']
    smp = res['sm']['perfect']['pf']
    for k in J.CATS:
        r = SIM[(k['site'], k['name'])]
        o = k['ro']; s = r.runoff.reindex(o.index)
        rec = dict(site=k['site'], name=k['name'],
                   ro=dict(d=[str(x.date()) for x in o.index], o=list(np.round(o.cumsum().values, 2)), s=list(np.round(s.cumsum().values, 2))))
        so = k['ss_win']; ss_ = ssj(k)
        rec['ss'] = dict(d=[str(x.date()) for x in so.index], o=list(np.round(so.cumsum().values, 3)), s=list(np.round(ss_.cumsum().values, 3)))
        if 'sm_win' in k:
            mo = k['sm_win']; ms = smj(k); mp = smp(k)
            rec['sm'] = dict(d=[str(x.date()) for x in mo.index], o=list(np.round(mo.cumsum().values, 2)),
                             s=list(np.round(ms.cumsum().values, 2)), p=list(np.round(mp.cumsum().values, 2)))
        cum.append(rec)
    for g in res.values():
        for f in g.values(): f.pop('pf')
    json.dump(dict(runoff=R, sed=res, cum=cum, LS=J.LS), open(f'/home/claude/joint/joint_{MODE}_{OBJ}.json', 'w'), default=float)
