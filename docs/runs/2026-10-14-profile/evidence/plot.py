"""Plot saved measurement summaries with matplotlib; never estimates missing data."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

p = argparse.ArgumentParser()
p.add_argument('directory', type=Path)
a = p.parse_args()
root = a.directory
d = json.loads((root / 'analysis.json').read_text())
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                     'axes.spines.top': False, 'axes.spines.right': False})
fig, (ax, bx) = plt.subplots(2, 1, figsize=(10, 7.6), gridspec_kw={'height_ratios': [1.1, 1]})
fig.suptitle('HeteroMosaic on Ryzen AI HX 370: where prefill time goes', fontsize=15, x=.12, ha='left')
keys = ['gpu_native', 'gpu_matched', 'hetero_serial', 'hetero_pipeline']
labels = ['GPU, 1024-token chunk', 'GPU, matched 512-token chunks',
          'GPU + NPU, serial chunks', 'GPU + NPU, two inflight chunks']
colors = ['#9ba9be', '#4f6e9f', '#db792e', '#b24e25']
for i, (key, label, color) in enumerate(zip(keys, labels, colors)):
    r = d['measurements'][key + '-baseline-none']['prefill_ms']
    ax.barh(i, r['median'], color=color, height=.58)
    ax.errorbar(r['median'], i, xerr=[[r['median'] - r['min']], [r['max'] - r['median']]],
                color='#202b3b', capsize=4, linewidth=1.2)
    ax.text(r['max'] + 23, i, f"{r['median']:,.0f} ms", va='center', fontsize=10)
ax.set_yticks(range(4), labels)
ax.invert_yaxis()
ax.set_xlim(0, 2070)
ax.set_xlabel('Prefill latency (ms); median and observed range of five measured runs')
ax.set_title('Normal execution: fixed 1024-token input, full 32-layer model', loc='left', pad=12, fontsize=11)
ax.grid(axis='x', alpha=.18)
ax.set_axisbelow(True)

stages = [('G1', 'Norm / QKV / RoPE / KV', '#4f6e9f'),
          ('A', 'Attention', '#52a0a0'), ('O_projection', 'Output projection + residual', '#8898ab'),
          ('FFN_norm', 'FFN norm', '#bfc9d4'), ('FFN_gate_up', 'FFN gate + up', '#e9a13b'),
          ('FFN_pointwise', 'SiLU + gating', '#72a978'), ('FFN_down', 'FFN down + residual', '#c95646')]
for i, key in enumerate(['gpu_matched-detail-sync', 'hetero_serial-detail-sync']):
    left = 0
    for stage, label, color in stages:
        value = d['stages'][key]['prefill/' + stage]['ms']['median']
        bx.barh(i, value, left=left, color=color, height=.48, label=label if i == 0 else None)
        if value > 250:
            bx.text(left + value / 2, i, f'{value:.0f}', ha='center', va='center', color='white', weight='bold')
        left += value
    total = d['measurements'][key]['prefill_ms']['median']
    bx.barh(i, max(0, total - left), left=left, color='#edf0f3', height=.48,
            label='Other / trace gaps' if i == 0 else None)
bx.set_yticks([0, 1], ['GPU, matched chunks', 'GPU + NPU, serial'])
bx.invert_yaxis()
bx.set_xlim(0, 1950)
bx.set_xlabel('Completion-aware diagnostic stage time (ms); two measured runs')
bx.set_title('FFN is the largest budget: about 68% of heterogeneous prefill', loc='left', fontsize=11, pad=12)
bx.grid(axis='x', alpha=.18)
bx.set_axisbelow(True)
bx.legend(loc='upper center', bbox_to_anchor=(.45, -.34), ncol=3, frameon=False, fontsize=8)
fig.text(.12, .016, 'Experimental compatibility port. Random-weight NPU numerical checks remain unresolved.\n'
         'Stage barriers perturb execution; host wait sums are not hardware utilization or additive latency.',
         fontsize=8, color='#566273')
fig.subplots_adjust(left=.32, right=.97, top=.89, bottom=.22, hspace=.70)
fig.savefig(root / 'prefill-profile.png', dpi=170, bbox_inches='tight')
fig.savefig(root / 'prefill-profile.svg', bbox_inches='tight')
print('Saved prefill-profile.png and prefill-profile.svg')

