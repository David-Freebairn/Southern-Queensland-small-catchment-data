"""Original vs new Watbal2026, both driven by the revised vege files (no soil water resets, vege planting dates).

Original model: original soil files as they are (CN2, CN reduction, U, Cona, K, bottom drainage), engine-default
capped AMC, no zero-till offset, PERFECT sediment curve (conc x LS x K x P); no suspended sediment model.
New model: agreed improvements fitted jointly on cumulative P:O (runoff_Vr.json, sed_Vr_log2.log):
HowLeaky AMC, shared CN-cover reduction and zero-till offset, site CN2, site-calibrated soil water parameters,
exponential sediment curve with shared b and site K, suspended sediment with shared b and site bare-soil
concentration, seasonal sediment factor off.
Run with COVER=vegefile VEGE_REV=1."""
import json, re
import numpy as np, pandas as pd
import joint_setup as J
from joint_sed import perfect_conc

SITES = ['Greenmount', 'Greenwood', 'Wallumbilla']
ORIG = {'Greenmount': dict(cn2=83.0, cn_red=15.0, U=4.0, cona=4.0, K=0.35, ksat_bot=12.0),
        'Greenwood': dict(cn2=86.0, cn_red=15.0, U=0.0, cona=6.0, K=0.40, ksat_bot=12.0),
        'Wallumbilla': dict(cn2=86.0, cn_red=10.0, U=4.0, cona=4.0, K=0.40, ksat_bot=0.1)}
for o in ORIG.values():
    o.update(amc_mode='capped', kl=None, zt_cn2_offset=0.0)

R = json.load(open('/home/claude/joint/runoff_Vr.json'))
log = open('/home/claude/joint/sed_Vr_log2.log').read()
xs = lambda tag: [float(v) for v in re.search(tag + r' \[([^\]]+)\]', log).group(1).split()]
smx, ssx = xs('SM joint_siteK'), xs('SS siteA')
NEW = dict(cn2={s: R['params'][s]['cn2'] for s in SITES}, cn_red=R['x'][3], zt=R['x'][4],
           b_sm=smx[0], K={'Greenmount': float(np.exp(smx[1])), 'Greenwood': float(np.exp(smx[2]))},
           b_ss=ssx[3], A=dict(zip(SITES, [float(np.exp(v)) for v in ssx[:3]])))

def nse(o, s): return J.nse(o, s)
def r3(x): return x.rolling(3, center=True, min_periods=1).sum()
def monthly(d):
    df = pd.DataFrame(d).cumsum()
    m = df.resample('MS').last()
    m = pd.concat([df.iloc[[0]], m, df.iloc[[-1]]]); m = m[~m.index.duplicated(keep='last')].ffill()
    return dict(d=[x.strftime('%Y-%m-%d') for x in m.index], **{k: [round(float(v), 3) for v in m[k]] for k in m})

stats, cum, pts = [], [], []
for k in J.CATS:
    s = k['site']
    r_old = J.simulate(k, ORIG[s]); r_new = J.simulate(k, R['params'][s])
    o = k['ro']; q_old = r_old.runoff.reindex(o.index); q_new = r_new.runoff.reindex(o.index)
    po = k['paw_obs']
    row = dict(site=s, name=k['name'], ro_obs=float(o.sum()),
               ro_po_old=float(q_old.sum() / o.sum()), ro_po_new=float(q_new.sum() / o.sum()),
               ro_nse_old=nse(r3(o), r3(q_old)), ro_nse_new=nse(r3(o), r3(q_new)),
               paw_rmse_old=float(np.sqrt(np.nanmean((r_old.paw.reindex(po.index) - po) ** 2))),
               paw_rmse_new=float(np.sqrt(np.nanmean((r_new.paw.reindex(po.index) - po) ** 2))))
    rec = dict(site=s, name=k['name'], ro=monthly({'o': o, 'old': q_old, 'new': q_new}))
    cover_w = float((r_new.total_cover.reindex(o.index) * o).sum() / o.sum() * 100)   # runoff-weighted vege cover
    if 'sm_win' in k:
        idx = k['sm_win'].index
        def sm(r, new):
            rr = r.reindex(idx); qq = rr.runoff.values; cov = np.minimum(100, rr.total_cover.values * 100)
            conc = 16.52 * np.exp(-NEW['b_sm'] * cov) if new else perfect_conc(cov)
            KK = NEW['K'][s] if new else ORIG[s]['K']
            return pd.Series(np.where(qq > 1, conc * J.LS[s] * KK * qq / 10, 0.0), index=idx)
        so, sn = sm(r_old, False), sm(r_new, True)
        row.update(sm_obs=float(k['sm_win'].sum()), sm_po_old=float(so.sum() / k['sm_win'].sum()),
                   sm_po_new=float(sn.sum() / k['sm_win'].sum()),
                   sm_nse_old=nse(r3(k['sm_win']), r3(so)), sm_nse_new=nse(r3(k['sm_win']), r3(sn)))
        rec['sm'] = monthly({'o': k['sm_win'], 'old': so, 'new': sn})
        qo = k['ro'].reindex(idx).fillna(0).sum()
        pts.append(dict(kind='sm', site=s, name=k['name'], cover=cover_w, conc=float(100 * k['sm_win'].sum() / qo)))
    idx = k['ss_win'].index; rr = r_new.reindex(idx); qq = rr.runoff.values; cov = np.minimum(100, rr.total_cover.values * 100)
    ssn = pd.Series(np.where(qq > 1, NEW['A'][s] * np.exp(-NEW['b_ss'] * cov) * qq / 1e5, 0.0), index=idx)
    row.update(ss_obs=float(k['ss_win'].sum()), ss_po_new=float(ssn.sum() / k['ss_win'].sum()),
               ss_nse_new=nse(r3(k['ss_win']), r3(ssn)))
    rec['ss'] = monthly({'o': k['ss_win'], 'new': ssn})
    qo = k['ro'].reindex(idx).fillna(0).sum()
    pts.append(dict(kind='ss', site=s, name=k['name'], cover=cover_w, conc=float(100 * k['ss_win'].sum() / qo)))
    stats.append(row); cum.append(rec)

df = pd.DataFrame(stats)
pd.set_option('display.width', 250)
print(df.round(2).to_string())
print(pd.DataFrame(pts).round(2).to_string())
curves = dict(LS=J.LS, orig=ORIG, new=NEW)
json.dump(dict(stats=stats, cum=cum, pts=pts, curves=curves), open('/home/claude/joint/final_compare.json', 'w'), default=float)
print(json.dumps(NEW, default=float))
