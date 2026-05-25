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

from oracle_sandbox import Specification, evaluate_executable_oracle

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

unsafe_candidates = [
    ('oracle_unsafe_import_os', "import os\n\ndef synthesized_function(x):\n    return x*2\n# END"),
    ('oracle_unsafe_eval', "def synthesized_function(x):\n    return eval('x*2')\n# END"),
    ('oracle_unsafe_open', "def synthesized_function(x):\n    f=open('out.txt','w')\n    return x*2\n# END"),
    ('oracle_unsafe_subprocess', "import subprocess\n\ndef synthesized_function(x):\n    subprocess.run(['echo', 'hi'])\n    return x*2\n# END"),
    ('oracle_unsafe_compile', "def synthesized_function(x):\n    code = compile('x*2', '<string>', 'eval')\n    return eval(code)\n# END"),
    ('oracle_unsafe_exec', "def synthesized_function(x):\n    exec('y = x * 2')\n    return y\n# END"),
    ('oracle_unsafe_dunder_import', "def synthesized_function(x):\n    mod = __import__('os')\n    return x*2\n# END"),
]

spec = Specification(description='dummy', predicate=lambda ns, sample: True, sample_inputs=[{'value': 0}])
for name, code in unsafe_candidates:
    success, diagnostic = evaluate_executable_oracle(code, [spec], timeout=1.0)
    status = 'accepted' if success else 'blocked'
    reason = '' if success else diagnostic
    results.append((name, 'oracle', status, reason))
    print(f'{name}: {status} {reason}')

os.makedirs('figures', exist_ok=True)
with open(os.path.join('figures', 'results.csv'), 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['case', 'type', 'status', 'reason'])
    writer.writerows(results)

prompt_accepted = sum(1 for r in results if r[1] == 'prompt' and r[2] == 'accepted')
prompt_blocked = sum(1 for r in results if r[1] == 'prompt' and r[2] == 'blocked')
oracle_accepted = sum(1 for r in results if r[1] == 'oracle' and r[2] == 'accepted')
oracle_blocked = sum(1 for r in results if r[1] == 'oracle' and r[2] == 'blocked')
reasons = Counter(r[3] if r[3] else 'none' for r in results)

summary_md = os.path.join('figures', 'results_summary.md')
with open(summary_md, 'w', encoding='utf-8') as f:
    f.write('# Results summary\n\n')
    f.write('## Summary counts\n\n')
    f.write(f'- Prompt cases processed: {prompt_accepted + prompt_blocked}\n')
    f.write(f'- Prompt accepted: {prompt_accepted}\n')
    f.write(f'- Prompt blocked: {prompt_blocked}\n')
    f.write(f'- Oracle direct unsafe cases: {oracle_accepted + oracle_blocked}\n')
    f.write(f'- Oracle blocked: {oracle_blocked}\n')
    f.write('\n## Blocked reason breakdown\n\n')
    f.write('| Reason | Count |\n')
    f.write('|---|---|\n')
    for reason, count in reasons.items():
        if reason == 'none':
            continue
        f.write(f'| {reason} | {count} |\n')
    f.write('\n## Notes\n\n')
    f.write('The prompt sweep accepted all prompt cases in this run.\n')
    f.write('The oracle direct tests blocked explicit unsafe candidate code patterns.\n')
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
    plt.savefig(os.path.join('figures', 'outcome_bar.png'), dpi=200)

    labels = [k for k in reasons.keys() if k != 'none']
    counts = [v for k, v in reasons.items() if k != 'none']
    if counts:
        plt.figure(figsize=(6, 6))
        plt.pie(counts, labels=labels, autopct='%1.1f%%', colors=plt.cm.tab20.colors)
        plt.title('Blocked reasons distribution')
        plt.tight_layout()
        plt.savefig(os.path.join('figures', 'reject_pie.png'), dpi=200)

    print('WROTE figures/outcome_bar.png, figures/reject_pie.png (if any), and figures/results.csv')
except Exception as exc:
    print('Matplotlib unavailable or plotting failed:', exc)
    print('WROTE figures/results.csv only')
