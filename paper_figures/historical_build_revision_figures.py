from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd
from pypdf import PdfReader
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE = Path(__file__).parent
PROJECT = HERE / 'project' / 'causal_lab_proposal_subpapers_tex'
DATA = Path(r'D:\study\zzh科研\experiment\new_version\results')
plt.rcParams.update({'font.family': 'sans-serif', 'font.sans-serif': ['Arial', 'DejaVu Sans'],
                     'font.size': 8, 'axes.titlesize': 9, 'legend.fontsize': 7.5,
                     'axes.spines.top': False, 'axes.spines.right': False,
                     'legend.frameon': False, 'pdf.fonttype': 42})

# Keep the main-text image's physical aspect ratio unchanged.
old = PdfReader(PROJECT / 'experiments/causal_atlas_bridge/figures/manylabs2_framing_loso.pdf').pages[0]
width = 5.06
height = width * float(old.mediabox.height) / float(old.mediabox.width)
hold = pd.read_csv(DATA / 'full/manylabs_holdouts.csv')
front = pd.read_csv(DATA / 'full/manylabs_frontier.csv')
summary = pd.read_csv(DATA / 'full/manylabs_summary.csv').set_index('method')
assert round(summary.loc['random', 'reference_mae'], 4) == .0801
assert summary.loc['random', 'n_released_015'] == 6
assert round(summary.loc['random', 'released_mae_015'], 4) == .0489
fig, axes = plt.subplots(1, 2, figsize=(width, height))
fig.subplots_adjust(left=.115, right=.98, bottom=.22, top=.81, wspace=.43)
g = hold[hold.method.eq('random')]
release = g.radius.le(.15)
axes[0].scatter(g.loc[~release, 'target_reference'], g.loc[~release, 'estimate'],
                color='#767676', marker='x', s=18, linewidths=.9, label='Refused (51)')
axes[0].scatter(g.loc[release, 'target_reference'], g.loc[release, 'estimate'],
                color='#0F4D92', marker='o', s=22, label='Released (6)')
axes[0].plot([-.2, .6], [-.2, .6], '--', color='#B64342', lw=.8)
axes[0].set(xlim=(-.2, .6), ylim=(-.2, .6), xlabel='Held-out noisy reference',
            ylabel='Frozen prediction', title='A  Random-effects predictions')
axes[0].legend(loc='upper left')
for method, label, color, style in [('fixed', 'Fixed effect', '#767676', '--'),
                                    ('random', 'Random effects', '#0F4D92', '-')]:
    g = front[front.method.eq(method) & front.n_released.gt(0)]
    axes[1].plot(g.release_rate, g.reference_mae, color=color, ls=style, label=label, lw=1.1)
axes[1].set(xlim=(0, 1), xlabel='Fraction released', ylabel='MAE among released sources',
            title='B  Risk-release frontier')
axes[1].legend(loc='lower right')
fig.savefig(PROJECT / 'revision_manylabs.pdf')
fig.savefig(HERE / 'revision_manylabs.png', dpi=180)
plt.close(fig)

sources = pd.read_csv(DATA / 'full/manylabs_sources.csv').sort_values('effect', ascending=False)
fig, axes = plt.subplots(1, 2, figsize=(5.5, 5.7))
fig.subplots_adjust(left=.20, right=.99, top=.95, bottom=.11, wspace=1.0)
for ax, rows, title in zip(axes, [sources.iloc[:29], sources.iloc[29:]], ['Sources 1-29', 'Sources 30-57']):
    y = np.arange(len(rows))
    ax.errorbar(rows.effect, y, xerr=1.96*np.sqrt(rows.variance), fmt='o', ms=2.5,
                color='#0F4D92', elinewidth=.6, capsize=0)
    ax.axvline(.17286449173759633, color='#42949E', ls='--', lw=.9)
    ax.axvline(0, color='#767676', ls=':', lw=.6)
    ax.set(yticks=y, yticklabels=rows.source, title=title, xlabel='Source risk difference',
           xlim=(-.4, .85), ylim=(28.7, -.7), xticks=[-.4, 0, .4, .8])
    ax.tick_params(axis='y', labelsize=7, length=0)
fig.savefig(PROJECT / 'revision_sources.pdf')
fig.savefig(HERE / 'revision_sources.png', dpi=180)
plt.close(fig)

pooled = pd.read_csv(DATA / 'workflow_full/pooled_summary.csv')
methods = [('r2_targeted', 'Targeted R2', '#0F4D92', '-', 'o'),
           ('rinf_targeted', 'Targeted R-infinity', '#9A4D8E', '--', 's'),
           ('r2_random', 'Random R2', '#B64342', '-.', '^'),
           ('r2_nearest', 'Nearest R2', '#42949E', ':', 'D'),
           ('r2_static', 'Archive only R2', '#767676', '--', 'x'),
           ('target_only', 'Target trial', '#272727', ':', '+')]
fig, axes = plt.subplots(2, 3, figsize=(5.5, 3.8), sharex=True, sharey=True)
fig.subplots_adjust(left=.11, right=.985, bottom=.28, top=.92, hspace=.30, wspace=.19)
for col, scenario in enumerate(['bridgeable', 'already_supported', 'unreachable']):
    if scenario not in set(pooled.scenario):
        scenario = [s for s in pooled.scenario.unique() if s not in ['bridgeable', 'unreachable']][0]
    for row, tolerance in enumerate([.2, .3]):
        ax = axes[row, col]
        for method, label, color, style, marker in methods:
            g = pooled[pooled.scenario.eq(scenario) & pooled.method.eq(method) & pooled.tolerance.eq(tolerance)].sort_values('budget')
            assert len(g) == 4
            x = g.budget.to_numpy() * 96
            ax.plot(x, g.released, color=color, ls=style, marker=marker, ms=4, lw=1.1,
                    markerfacecolor='none', label=label)
            ax.fill_between(x, g.released_lower, g.released_upper, color=color, alpha=.07)
        ax.set(xticks=[0, 96, 192, 288], yticks=[0, .5, 1], ylim=(-.03, 1.04))
        ax.tick_params(labelsize=7)
        if row == 0:
            ax.set_title(scenario.replace('_', ' ').capitalize(), fontsize=8)
        if col == 0:
            ax.set_ylabel(f'Tolerance {tolerance:g}\nFraction released', fontsize=8)
handles = [Line2D([], [], color=c, ls=s, marker=m, ms=4, markerfacecolor='none', label=l)
           for _, l, c, s, m in methods]
fig.supxlabel('Available new participants', fontsize=8, y=.16)
fig.legend(handles=handles, loc='lower center', ncol=3, fontsize=7.5, bbox_to_anchor=(.52, .01))
fig.savefig(PROJECT / 'revision_workflow.pdf')
fig.savefig(HERE / 'revision_workflow.png', dpi=180)
plt.close(fig)

used = [DATA / 'full/manylabs_holdouts.csv', DATA / 'full/manylabs_frontier.csv',
        DATA / 'full/manylabs_summary.csv', DATA / 'workflow_full/pooled_summary.csv']
(HERE / 'figure_provenance.json').write_text(json.dumps({str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in used}, indent=2))
print('Generated both figures from saved CSVs; main figure aspect ratio preserved.')
