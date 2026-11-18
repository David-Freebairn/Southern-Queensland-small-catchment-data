"""Paper figures: cumulative runoff, soil movement, suspended sediment; observed vs predicted scatter; PAW."""
import pickle
import numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

ts = pickle.load(open('/home/claude/paper/series.pkl', 'rb'))
OUT = '/home/claude/paper/figures/'
import os; os.makedirs(OUT, exist_ok=True)
C_OBS, C_OLD, C_NEW = '#1a1814', '#d55e00', '#0072b2'   # Okabe-Ito orange / blue: colour-blind safe
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.edgecolor': '#555', 'axes.labelcolor': '#222',
                     'xtick.color': '#444', 'ytick.color': '#444', 'axes.spines.top': False, 'axes.spines.right': False})
ORDER = [('Greenmount', 'Burnt'), ('Greenmount', 'Incorporated'), ('Greenmount', 'Mulch'), ('Greenmount', 'Zero till'),
         ('Greenwood', 'Burnt'), ('Greenwood', 'Incorporated'), ('Greenwood', 'Mulch'), ('Greenwood', 'Zero till'),
         ('Wallumbilla', 'Tilled'), ('Wallumbilla', 'Min till')]

def save(fig, name):
    fig.savefig(OUT + name + '.png', dpi=300, bbox_inches='tight'); fig.savefig(OUT + name + '.pdf', bbox_inches='tight'); plt.close(fig)

def cumulative(var, okey, ylabel, name, title, keys):
    n = len(keys); ncol = 4; nrow = int(np.ceil(n / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(12, 2.9 * nrow), squeeze=False)
    for ax in axes.flat[n:]: ax.set_visible(False)
    for ax, k in zip(axes.flat, keys):
        m, ob = ts[k]; o = ob[okey]
        ax.plot(o.index, o.cumsum(), color=C_OBS, lw=2, label='Observed')
        ax.plot(o.index, m['old'][var].reindex(o.index).cumsum(), color=C_OLD, lw=1.6, ls='--', label='Original')
        ax.plot(o.index, m['new'][var].reindex(o.index).cumsum(), color=C_NEW, lw=1.6, label='Revised')
        po_o = m['old'][var].reindex(o.index).sum() / o.sum(); po_n = m['new'][var].reindex(o.index).sum() / o.sum()
        ax.set_title(f'{k[0]} {k[1].lower()}', loc='left', fontsize=9.5, fontweight='bold')
        ax.text(0.02, 0.97, f'P:O  original {po_o:.2f}\n        revised  {po_n:.2f}', transform=ax.transAxes, va='top', fontsize=8, color='#333')
        ax.grid(True, color='#e5e5e5', lw=0.6); ax.set_axisbelow(True)
        span = (o.index[-1] - o.index[0]).days / 365.25
        ax.xaxis.set_major_locator(mdates.YearLocator(1 if span < 7 else 2 if span < 14 else 4))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.tick_params(axis='x', labelsize=8)
    for ax in axes[:, 0]: ax.set_ylabel(ylabel)
    h, l = axes.flat[0].get_legend_handles_labels()
    fig.legend(h, l, loc='upper right', ncol=3, frameon=False, bbox_to_anchor=(1.0, 1.02))
    fig.suptitle(title, x=0.01, ha='left', fontsize=11, fontweight='bold', y=1.02)
    fig.tight_layout(); save(fig, name)

cumulative('runoff', 'ro', 'Cumulative runoff (mm)', 'Fig1_cumulative_runoff', 'Cumulative runoff, measured periods', ORDER)
cumulative('sm', 'sm', 'Cumulative soil movement (t/ha)', 'Fig2_cumulative_soil_movement', 'Cumulative soil movement, measured periods', ORDER[:8])
cumulative('ss', 'ss', 'Cumulative suspended sediment (t/ha)', 'Fig3_cumulative_suspended_sediment', 'Cumulative suspended sediment, measured periods', ORDER)

# observed vs predicted monthly totals, all catchments pooled
MK = {'Greenmount': 'o', 'Greenwood': 's', 'Wallumbilla': '^'}
fig, axes = plt.subplots(3, 2, figsize=(8.5, 12))
for row, (var, okey, lab) in enumerate([('runoff', 'ro', 'Monthly runoff (mm)'), ('sm', 'sm', 'Monthly soil movement (t/ha)'),
                                        ('ss', 'ss', 'Monthly suspended sediment (t/ha)')]):
    for col, (v, name, c) in enumerate([('old', 'Original', C_OLD), ('new', 'Revised', C_NEW)]):
        ax = axes[row, col]; O, P = [], []
        for k in ORDER:
            m, ob = ts[k]
            if ob[okey] is None: continue
            o = ob[okey].resample('MS').sum(); p = m[v][var].reindex(ob[okey].index).resample('MS').sum()
            p_o = m['old'][var].reindex(ob[okey].index).resample('MS').sum(); p_n = m['new'][var].reindex(ob[okey].index).resample('MS').sum()
            keep = (o > 0) | (p_o > 0) | (p_n > 0)          # same months for both models
            ax.scatter(o[keep], p[keep], s=16, marker=MK[k[0]], facecolor='none', edgecolor=c, lw=0.8, alpha=0.8)
            O.append(o[keep]); P.append(p[keep])
        o, p = pd.concat(O), pd.concat(P)
        hi = max(o.max(), p.max()) * 1.05
        ax.plot([0, hi], [0, hi], color='#888', lw=1, ls=':')
        r2 = np.corrcoef(o, p)[0, 1] ** 2; nse = 1 - ((o - p) ** 2).sum() / ((o - o.mean()) ** 2).sum()
        ax.text(0.03, 0.97, f'{name}\nR² {r2:.2f}   NSE {nse:.2f}\nP:O {p.sum() / o.sum():.2f}   n {len(o)}', transform=ax.transAxes, va='top', fontsize=8.5)
        ax.set_xlim(0, hi); ax.set_ylim(0, hi); ax.set_aspect('equal')
        ax.set_xlabel('Observed ' + lab[0].lower() + lab[1:]); ax.set_ylabel('Predicted ' + lab[0].lower() + lab[1:])
        ax.grid(True, color='#eee', lw=0.6); ax.set_axisbelow(True)
for s, mk in MK.items():
    axes[0, 0].scatter([], [], marker=mk, facecolor='none', edgecolor='#555', label=s)
axes[0, 0].legend(loc='lower right', frameon=False, fontsize=8)
fig.suptitle('Observed vs predicted monthly totals (months with observed or predicted runoff, all catchments)', x=0.01, ha='left', fontsize=11, fontweight='bold')
fig.tight_layout(); save(fig, 'Fig4_monthly_obs_vs_pred')

# PAW observed vs predicted
fig, axes = plt.subplots(1, 2, figsize=(9, 4.6))
for ax, (v, name, c) in zip(axes, [('old', 'Original', C_OLD), ('new', 'Revised', C_NEW)]):
    O, P = [], []
    for k in ORDER:
        m, ob = ts[k]; o = ob['paw']; p = m[v].paw.reindex(o.index); mm = o.notna() & p.notna()
        ax.scatter(o[mm], p[mm], s=16, marker=MK[k[0]], facecolor='none', edgecolor=c, lw=0.8, alpha=0.85)
        O.append(o[mm]); P.append(p[mm])
    o, p = pd.concat(O), pd.concat(P)
    ax.plot([0, 320], [0, 320], color='#888', lw=1, ls=':')
    rmse = np.sqrt(((p - o) ** 2).mean()); bias = (p - o).mean(); r2 = np.corrcoef(o, p)[0, 1] ** 2
    ax.text(0.03, 0.97, f'{name}\nRMSE {rmse:.0f} mm   bias {bias:+.0f} mm\nR² {r2:.2f}   n {len(o)}', transform=ax.transAxes, va='top', fontsize=8.5)
    ax.set_xlim(0, 320); ax.set_ylim(0, 320); ax.set_aspect('equal')
    ax.set_xlabel('Observed PAW (mm)'); ax.set_ylabel('Predicted PAW (mm)'); ax.grid(True, color='#eee', lw=0.6)
for s, mk in MK.items():
    axes[0].scatter([], [], marker=mk, facecolor='none', edgecolor='#555', label=s)
axes[0].legend(loc='lower right', frameon=False, fontsize=8)
fig.suptitle('Plant available water (0-150 cm), observed vs predicted', x=0.01, ha='left', fontsize=11, fontweight='bold')
fig.tight_layout(); save(fig, 'Fig5_PAW_obs_vs_pred')
print('done')
