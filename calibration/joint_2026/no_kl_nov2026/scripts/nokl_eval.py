"""Evaluate Watbal2026 in input-file mode (revised vege files, no soil water resets) for a parameter configuration.
Run with COVER=vegefile VEGE_REV=1."""
import json
import numpy as np, pandas as pd
import joint_setup as J

SITES = ['Greenmount', 'Greenwood', 'Wallumbilla']
NM = json.load(open('/home/claude/joint/new_model_parameters.json'))
SH = NM['shared']
B_SM, B_SS = SH['sediment_cover_coef_b'], SH['suspended_cover_coef_b']

def a2_params():
    """Adopted A2 joint model (Nov 2026)."""
    P = {}
    for s in SITES:
        sw = NM['site_soil_water_from_reference_calibration'][s]
        P[s] = dict(cn2=NM['site'][s]['cn2'], cn_red=SH['cn_reduction_full_cover'], zt_cn2_offset=SH['zero_till_cn2_offset'],
                    amc_mode='howleaky', cona=sw['cona'], U=sw['U'], ksat_bot=sw['bottom_drain_mm_day'], kl=sw.get('kl'),
                    K=NM['site'][s]['K'] or 0.4, A=NM['site'][s]['suspended_bare_conc_g_L'])
    return P

def r3(x): return x.rolling(3, center=True, min_periods=1).sum()

def obs_yield(k):
    c, mod = k['c'], k['mod']
    if 'yield_obs' in c:
        return pd.Series(c['yield_obs']).dropna() if not isinstance(c['yield_obs'], pd.Series) else c['yield_obs'].dropna()
    if hasattr(mod, 'yield_obs'):
        return mod.yield_obs
    return pd.Series([s[2] for s in mod.seasons], index=[s[1] for s in mod.seasons]).dropna()

def run_cat(k, p, sw_prop=None):
    o = {kk: v for kk, v in p.items() if kk not in ('A',)}
    o['vege_matrix'] = k['vm']; o['sw_prop'] = sw_prop if sw_prop is not None else k['vm']['sw_prop']
    q = dict(J.SITEP[k['site']]); q.update(o)
    if k['name'] == 'Zero till' and q.get('zt_cn2_offset'):
        q['cn2'] = q['cn2'] + q['zt_cn2_offset']
    q['sed_cover_coef'] = None; q['sed_winter_frac'] = 1.0
    soil = J.WB_SOIL if k['site'] == 'Wallumbilla' else k['mod'].SOIL
    from wb_watbal import run
    r, y, T = run(soil, k['c']['forcing'], k['mod'].seasons, q, {}, paw0=None)
    return r, pd.Series(y, index=[s[1] for s in k['mod'].seasons]), pd.Series(T, index=[s[1] for s in k['mod'].seasons])

def evaluate(P, sw_prop=None, cats=None, sed=True):
    rows = []
    for k in (cats or J.CATS):
        s = k['site']; p = P[s]
        r, y, T = run_cat(k, p, sw_prop)
        o = k['ro']; q = r.runoff.reindex(o.index)
        po = k['paw_obs']; ps = r.paw.reindex(po.index)
        # end-of-crop = original reset dates (measured just after harvest); model day before
        ec = [d for d in k['c'].get('resets_orig', {})] if 'resets_orig' in k['c'] else []
        row = dict(site=s, name=k['name'], ro_obs=float(o.sum()), ro_pred=float(q.sum()), ro_po=float(q.sum() / o.sum()),
                   ro_nse3=J.nse(r3(o), r3(q)), paw_rmse=float(np.sqrt(np.nanmean((ps - po) ** 2))),
                   paw_bias=float(np.nanmean(ps - po)))
        if ec:
            pe = pd.Series({d: r.paw.get(d - pd.Timedelta(days=1)) for d in ec}); oe = pd.Series(k['c']['resets_orig'])
            row.update(eoc_pred=float(pe.mean()), eoc_obs=float(oe.mean()))
        yo = obs_yield(k); yp = y.reindex(yo.index)
        m = yo.notna() & yp.notna()
        row.update(yield_obs=float(yo[m].mean()) if m.any() else np.nan, yield_pred=float(yp[m].mean()) if m.any() else np.nan,
                   T_mean=float(T.mean()))
        win = r.loc[o.index]
        row.update(soil_evap=float(win.soil_evap.sum()), transp=float(win.transp.sum()), drainage=float(win.drainage.sum()),
                   rain=float(win.rain.sum()), years=len(o) / 365.25)
        if sed:
            if 'sm_win' in k:
                idx = k['sm_win'].index; rr = r.reindex(idx); qq = rr.runoff.values; cov = np.minimum(100, rr.total_cover.values * 100)
                sm = pd.Series(np.where(qq > 1, 16.52 * np.exp(-B_SM * cov) * J.LS[s] * p['K'] * qq / 10, 0.0), index=idx)
                row.update(sm_obs=float(k['sm_win'].sum()), sm_pred=float(sm.sum()), sm_po=float(sm.sum() / k['sm_win'].sum()))
            idx = k['ss_win'].index; rr = r.reindex(idx); qq = rr.runoff.values; cov = np.minimum(100, rr.total_cover.values * 100)
            ss = pd.Series(np.where(qq > 1, p['A'] * np.exp(-B_SS * cov) * qq / 100, 0.0), index=idx)
            row.update(ss_obs=float(k['ss_win'].sum()), ss_pred=float(ss.sum()), ss_po=float(ss.sum() / k['ss_win'].sum()))
        rows.append(row)
    return pd.DataFrame(rows)

# keep the original reset dates (end-of-crop profiles) for scoring before joint_setup cleared them
for k in J.CATS:
    if 'paw_obs' in k:
        src = {'Greenmount': J.GM, 'Greenwood': J.GW, 'Wallumbilla': J.WB}[k['site']]
        orig = next(c for c in src.CATS if c['name'] == k['name'])
        k['c']['resets_orig'] = dict(orig['resets'])
