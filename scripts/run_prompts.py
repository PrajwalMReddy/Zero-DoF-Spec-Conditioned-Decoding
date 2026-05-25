import subprocess
import glob
import os
import csv
import re
import sys
from collections import Counter

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

os.chdir(REPO_ROOT)
RESULTS_DIR = os.path.join(REPO_ROOT, 'results')

from oracle_sandbox import Specification, evaluate_executable_oracle
from oracle_benchmark_specs import spec_double, spec_invoke
from oracle_safe_cases import ORACLE_SAFE_CASES
from oracle_unsafe_cases import ORACLE_UNSAFE_CASES

ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(ENV_PATH):
    with open(ENV_PATH, 'r', encoding='utf-8') as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                continue
            key, value = line.split('=', 1)
            os.environ.setdefault(key, value)

PROMPT_GLOB = os.path.join('prompts', '*.txt')
PROMPTS = sorted(glob.glob(PROMPT_GLOB))
results = []

# Run direct oracle suites first (Windows spawn is unreliable after many subprocesses).
spec_invoke_oracle = spec_invoke()
spec_double_oracle = spec_double()
oracle_timeout_unsafe = 0.05
oracle_timeout_safe = 1.0
for name, code in ORACLE_UNSAFE_CASES:
    success, diagnostic = evaluate_executable_oracle(code, [spec_invoke_oracle], timeout=oracle_timeout_unsafe)
    status = 'accepted' if success else 'blocked'
    reason = '' if success else diagnostic
    results.append((name, 'oracle_unsafe', status, reason))
    print(f'{name}: {status} {reason}')

for name, code in ORACLE_SAFE_CASES:
    success, diagnostic = evaluate_executable_oracle(
        code,
        [spec_double_oracle],
        timeout=oracle_timeout_safe,
        use_multiprocessing=False,
    )
    status = 'accepted' if success else 'blocked'
    reason = '' if success else diagnostic
    results.append((name, 'oracle_safe', status, reason))
    print(f'{name}: {status} {reason}')

for p in PROMPTS:
    cmd = ['python', 'zero_scd_engine.py', '--prompt-file', p, '--verbose']
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        out = proc.stdout + proc.stderr
    except Exception as exc:
        out = f'Process error: {exc}'

    status = 'accepted'
    reason = ''
    if 'Restricted' in out or 'checkpoint rejected' in out or '# Error:' in out:
        status = 'blocked'
        m = re.search(r'Restricted [^:]+ detected: ([\w_]+)', out)
        if m:
            reason = m.group(1)
        else:
            m = re.search(r'checkpoint rejected: (.*)', out)
            if m:
                reason = m.group(1).strip()
            else:
                m = re.search(r'# Error: (.*)', out)
                if m:
                    reason = m.group(1).strip()
                else:
                    reason = 'unknown'

    results.append((os.path.basename(p), 'prompt', status, reason))
    print(f'{p}: {status} {reason}')

os.makedirs(RESULTS_DIR, exist_ok=True)
with open(os.path.join(RESULTS_DIR, 'results.csv'), 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['case', 'type', 'status', 'reason'])
    writer.writerows(results)

prompt_accepted = sum(1 for r in results if r[1] == 'prompt' and r[2] == 'accepted')
prompt_blocked = sum(1 for r in results if r[1] == 'prompt' and r[2] == 'blocked')
oracle_unsafe_accepted = sum(1 for r in results if r[1] == 'oracle_unsafe' and r[2] == 'accepted')
oracle_unsafe_blocked = sum(1 for r in results if r[1] == 'oracle_unsafe' and r[2] == 'blocked')
oracle_safe_accepted = sum(1 for r in results if r[1] == 'oracle_safe' and r[2] == 'accepted')
oracle_safe_blocked = sum(1 for r in results if r[1] == 'oracle_safe' and r[2] == 'blocked')
oracle_blocked = oracle_unsafe_blocked
reasons = Counter(r[3] if r[3] else 'none' for r in results)

summary_md = os.path.join(RESULTS_DIR, 'results_summary.md')
with open(summary_md, 'w', encoding='utf-8') as f:
    f.write('# Results summary\n\n')
    f.write('## Summary counts\n\n')
    f.write(f'- Prompt cases processed: {prompt_accepted + prompt_blocked}\n')
    f.write(f'- Prompt accepted: {prompt_accepted}\n')
    f.write(f'- Prompt blocked: {prompt_blocked}\n')
    f.write(f'- Oracle direct unsafe cases: {oracle_unsafe_accepted + oracle_unsafe_blocked}\n')
    f.write(f'- Oracle unsafe blocked: {oracle_unsafe_blocked}\n')
    f.write(f'- Oracle direct safe cases: {oracle_safe_accepted + oracle_safe_blocked}\n')
    f.write(f'- Oracle safe accepted (no false reject): {oracle_safe_accepted}\n')
    f.write(f'- Oracle safe blocked (false reject): {oracle_safe_blocked}\n')
    f.write('\n## Blocked reason breakdown\n\n')
    f.write('| Reason | Count |\n')
    f.write('|---|---|\n')
    for reason, count in reasons.items():
        if reason == 'none':
            continue
        f.write(f'| {reason} | {count} |\n')
    f.write('\n## Notes\n\n')
    f.write(
        f'The prompt sweep: {prompt_accepted} accepted, {prompt_blocked} blocked '
        f'(stub mode typically accepts safe completions).\n'
    )
    f.write(
        f'The oracle unsafe suite: {oracle_unsafe_blocked}/{oracle_unsafe_accepted + oracle_unsafe_blocked} blocked. '
        f'Safe suite: {oracle_safe_accepted}/{oracle_safe_accepted + oracle_safe_blocked} accepted.\n'
    )
    f.write('See `outcome_bar.png` and `reject_pie.png` for visual summaries.\n')

try:
    import matplotlib.pyplot as plt

    plt.figure(figsize=(6, 4))
    plt.bar(
        ['prompt accepted', 'prompt blocked', 'oracle blocked'],
        [prompt_accepted, prompt_blocked, oracle_blocked],
        color=['#4CAF50', '#F44336', '#F44336'],
    )
    for i, v in enumerate([prompt_accepted, prompt_blocked, oracle_blocked]):
        plt.text(i, v + 0.1, str(v), ha='center')
    plt.ylabel('Number of cases')
    plt.title('Prompt and oracle verification outcomes')
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'outcome_bar.png'), dpi=200)

    labels = [k for k in reasons.keys() if k != 'none']
    counts = [v for k, v in reasons.items() if k != 'none']
    if counts:
        plt.figure(figsize=(6, 6))
        plt.pie(counts, labels=labels, autopct='%1.1f%%', colors=plt.cm.tab20.colors)
        plt.title('Blocked reasons distribution')
        plt.tight_layout()
        plt.savefig(os.path.join(RESULTS_DIR, 'reject_pie.png'), dpi=200)

    print(
        f'WROTE {RESULTS_DIR}/outcome_bar.png, {RESULTS_DIR}/reject_pie.png (if any), '
        f'and {RESULTS_DIR}/results.csv'
    )
except Exception as exc:
    print('Matplotlib unavailable or plotting failed:', exc)
    print(f'WROTE {RESULTS_DIR}/results.csv only')
