"""Per-site refit of Cona and CN2 with kl removed, U = 0 and no-stress PAW fraction 0.75 for every run.
Input-file mode (revised vege files, no soil water resets). CN reduction at full cover and zero-till offset stay at the
shared A2 values. For each trial Cona, CN2 is solved so the site's cumulative runoff P:O = 1; Cona is chosen to minimise
the site's PAW RMSE. Usage: COVER=vegefile VEGE_REV=1 python3 nokl_fit.py <Site>"""
import sys, json, time
import numpy as np
from scipy.optimize import brentq, minimize_scalar
import nokl_eval as E
import joint_setup as J

SITE = sys.argv[1]
SWP = 0.75
cats = [k for k in J.CATS if k['site'] == SITE]
P0 = E.a2_params()[SITE]
P0.update(kl=None, U=0.0)
log = open(f'/home/claude/joint/nokl_fit_{SITE}.log', 'w')

def stats(cona, cn2):
    P = {SITE: dict(P0, cona=cona, cn2=cn2)}
    d = E.evaluate(P, sw_prop=SWP, cats=cats, sed=False)
    po = d.ro_pred.sum() / d.ro_obs.sum()
    n = np.array([len(k['paw_obs']) for k in cats])
    rmse = float(np.sqrt((d.paw_rmse.values ** 2 * n).sum() / n.sum()))
    return po, rmse, d

def cn2_for(cona):
    f = lambda c: stats(cona, c)[0] - 1.0
    return brentq(f, 50.0, 99.0, xtol=0.02)

cache = {}
def obj(cona):
    try:
        cn2 = cn2_for(cona)
    except ValueError:                       # no CN2 in range gives P:O = 1 at this Cona
        print(f'cona {cona:.3f} no CN2 gives P:O = 1', file=log, flush=True)
        return 1e3 + cona
    if False: pass
    po, rmse, _ = stats(cona, cn2)
    cache[round(cona, 4)] = (cn2, rmse)
    print(f'cona {cona:.3f} cn2 {cn2:.2f} P:O {po:.3f} PAW RMSE {rmse:.2f}', file=log, flush=True)
    return rmse

t0 = time.time()
r = minimize_scalar(obj, bounds=(float(sys.argv[2]) if len(sys.argv) > 2 else 1.0, 9.0), method='bounded', options=dict(xatol=0.05))
cona = float(r.x); cn2 = cn2_for(cona)
json.dump(dict(site=SITE, cona=cona, cn2=cn2, U=0.0, sw_prop=SWP, paw_rmse=float(r.fun), secs=time.time() - t0,
               trials={str(k): v for k, v in cache.items()}), open(f'/home/claude/joint/nokl_fit_{SITE}.json', 'w'), indent=1)
print('done', SITE, cona, cn2, r.fun, file=log, flush=True)
