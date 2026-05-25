"""Build paper-style figures for the main findings document."""

import csv
import os
from collections import Counter

import matplotlib.pyplot as plt

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
RESULTS_DIR = os.path.join(REPO_ROOT, 'results')
CSV_PATH = os.path.join(RESULTS_DIR, 'results.csv')


def load_rows():
    with open(CSV_PATH, newline='', encoding='utf-8') as handle:
        return list(csv.DictReader(handle))


def figure1_outcomes(rows):
    prompt = [r for r in rows if r['type'] == 'prompt']
    oracle = [r for r in rows if r['type'] in ('oracle', 'oracle_unsafe', 'oracle_safe')]
    pa = sum(1 for r in prompt if r['status'] == 'accepted')
    pb = sum(1 for r in prompt if r['status'] == 'blocked')
    ob = sum(1 for r in oracle if r['status'] == 'blocked')

    fig, ax = plt.subplots(figsize=(7, 4.5))
    labels = [
        'Prompt sweep\naccepted',
        'Prompt sweep\nblocked',
        'Oracle direct\nunsafe blocked',
    ]
    values = [pa, pb, ob]
    colors = ['#2E7D32', '#C62828', '#1565C0']
    bars = ax.bar(labels, values, color=colors, edgecolor='#333333', linewidth=0.6)
    ax.set_ylabel('Number of cases', fontsize=11)
    ax.set_title('Figure 1. End-to-end and oracle-level verification outcomes (N=146)', fontsize=12)
    ymax = max(values) * 1.12 + 1
    ax.set_ylim(0, ymax)
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + ymax * 0.02,
            str(value),
            ha='center',
            va='bottom',
            fontsize=11,
            fontweight='bold',
        )
    ax.tick_params(axis='x', labelsize=10)
    fig.tight_layout()
    path = os.path.join(RESULTS_DIR, 'figure1_outcomes.png')
    fig.savefig(path, dpi=220)
    plt.close(fig)
    return path


def figure2_rejection_categories(rows):
    oracle_blocked = [
        r['reason']
        for r in rows
        if r['type'] in ('oracle', 'oracle_unsafe') and r['status'] == 'blocked'
    ]

    def bucket(reason: str) -> str:
        if reason.startswith('Halting'):
            return 'Halting timeout'
        if 'import detected' in reason:
            return 'Restricted import'
        if 'call detected' in reason:
            return 'Restricted call'
        if 'symbol detected' in reason:
            return 'Restricted symbol'
        if 'attribute detected' in reason:
            return 'Restricted attribute'
        return 'Other'

    counts = Counter(bucket(r) for r in oracle_blocked)
    labels = list(counts.keys())
    values = [counts[k] for k in labels]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars = ax.barh(labels, values, color='#5C6BC0', edgecolor='#333333', linewidth=0.6)
    ax.set_xlabel('Number of blocked oracle cases (N=52)', fontsize=11)
    ax.set_title('Figure 2. Oracle rejection categories (direct unsafe corpus)', fontsize=12)
    for bar, value in zip(bars, values):
        ax.text(value + 0.3, bar.get_y() + bar.get_height() / 2, str(value), va='center', fontsize=10)
    ax.set_xlim(0, max(values) + 4)
    fig.tight_layout()
    path = os.path.join(RESULTS_DIR, 'figure2_rejection_categories.png')
    fig.savefig(path, dpi=220)
    plt.close(fig)
    return path


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    rows = load_rows()
    f1 = figure1_outcomes(rows)
    f2 = figure2_rejection_categories(rows)
    print(f'Wrote {f1}')
    print(f'Wrote {f2}')


if __name__ == '__main__':
    main()
