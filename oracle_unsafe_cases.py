"""Direct oracle negative cases: code snippets that must be blocked by the sandbox.

Used by scripts/run_prompts.py for statistically significant oracle rejection counts.
Each entry is (case_name, source_code).
"""

ORACLE_UNSAFE_CASES = [
    # --- eval ---
    ('oracle_unsafe_eval_return', "def synthesized_function(x):\n    return eval('x*2')\n# END"),
    ('oracle_unsafe_eval_str', "def synthesized_function(x):\n    return eval(str(x))\n# END"),
    ('oracle_unsafe_eval_expr', "def synthesized_function(x):\n    expr = 'x * 2'\n    return eval(expr)\n# END"),
    ('oracle_unsafe_eval_builtin', "def synthesized_function(x):\n    return eval('1+1')\n# END"),
    # --- exec ---
    ('oracle_unsafe_exec_assign', "def synthesized_function(x):\n    exec('y = x * 2')\n    return y\n# END"),
    ('oracle_unsafe_exec_multiline', "def synthesized_function(x):\n    exec('def inner(v):\\n    return v*2')\n    return x * 2\n# END"),
    ('oracle_unsafe_exec_globals', "def synthesized_function(x):\n    exec('result = x * 2', {'x': x})\n    return x * 2\n# END"),
    # --- compile ---
    ('oracle_unsafe_compile_eval', "def synthesized_function(x):\n    code = compile('x*2', '<string>', 'eval')\n    return eval(code)\n# END"),
    ('oracle_unsafe_compile_only', "def synthesized_function(x):\n    compile('x*2', '<string>', 'eval')\n    return x * 2\n# END"),
    ('oracle_unsafe_compile_exec_mode', "def synthesized_function(x):\n    compile('y=x*2', '<string>', 'exec')\n    return x * 2\n# END"),
    # --- execfile ---
    ('oracle_unsafe_execfile', "def synthesized_function(x):\n    execfile('script.py')\n    return x * 2\n# END"),
    ('oracle_unsafe_execfile_path', "def synthesized_function(x):\n    execfile('/tmp/evil.py')\n    return x * 2\n# END"),
    # --- open / write ---
    ('oracle_unsafe_open_read', "def synthesized_function(x):\n    f = open('data.txt', 'r')\n    return x * 2\n# END"),
    ('oracle_unsafe_open_write_mode', "def synthesized_function(x):\n    f = open('out.txt', 'w')\n    return x * 2\n# END"),
    ('oracle_unsafe_open_with', "def synthesized_function(x):\n    with open('out.txt', 'w') as f:\n        pass\n    return x * 2\n# END"),
    ('oracle_unsafe_write_call', "def synthesized_function(x):\n    buf = []\n    buf.write('leak')\n    return x * 2\n# END"),
    ('oracle_unsafe_write_method', "def synthesized_function(x):\n    class W:\n        def write(self, s):\n            pass\n    W().write('x')\n    return x * 2\n# END"),
    # --- __import__ ---
    ('oracle_unsafe_dunder_import_os', "def synthesized_function(x):\n    mod = __import__('os')\n    return x * 2\n# END"),
    ('oracle_unsafe_dunder_import_sys', "def synthesized_function(x):\n    mod = __import__('sys')\n    return x * 2\n# END"),
    ('oracle_unsafe_dunder_import_subprocess', "def synthesized_function(x):\n    mod = __import__('subprocess')\n    return x * 2\n# END"),
    # --- import os ---
    ('oracle_unsafe_import_os', "import os\n\ndef synthesized_function(x):\n    return x * 2\n# END"),
    ('oracle_unsafe_from_os_path', "from os import path\n\ndef synthesized_function(x):\n    return x * 2\n# END"),
    ('oracle_unsafe_import_os_alias', "import os as operating_system\n\ndef synthesized_function(x):\n    return x * 2\n# END"),
    ('oracle_unsafe_os_system', "import os\n\ndef synthesized_function(x):\n    os.system('echo hi')\n    return x * 2\n# END"),
    ('oracle_unsafe_os_name_symbol', "def synthesized_function(x):\n    return os.name\n# END"),
    # --- import sys ---
    ('oracle_unsafe_import_sys', "import sys\n\ndef synthesized_function(x):\n    return x * 2\n# END"),
    ('oracle_unsafe_sys_exit', "import sys\n\ndef synthesized_function(x):\n    sys.exit(0)\n    return x * 2\n# END"),
    ('oracle_unsafe_sys_modules', "import sys\n\ndef synthesized_function(x):\n    return len(sys.modules)\n# END"),
    # --- subprocess ---
    ('oracle_unsafe_import_subprocess', "import subprocess\n\ndef synthesized_function(x):\n    return x * 2\n# END"),
    ('oracle_unsafe_subprocess_run', "import subprocess\n\ndef synthesized_function(x):\n    subprocess.run(['echo', 'hi'])\n    return x * 2\n# END"),
    ('oracle_unsafe_subprocess_popen', "import subprocess\n\ndef synthesized_function(x):\n    subprocess.Popen(['ls'])\n    return x * 2\n# END"),
    ('oracle_unsafe_subprocess_call', "import subprocess\n\ndef synthesized_function(x):\n    subprocess.call('echo hi', shell=True)\n    return x * 2\n# END"),
    # --- requests ---
    ('oracle_unsafe_import_requests', "import requests\n\ndef synthesized_function(x):\n    return x * 2\n# END"),
    ('oracle_unsafe_requests_get', "import requests\n\ndef synthesized_function(x):\n    requests.get('http://example.com')\n    return x * 2\n# END"),
    ('oracle_unsafe_requests_post', "import requests\n\ndef synthesized_function(x):\n    requests.post('http://example.com', data={})\n    return x * 2\n# END"),
    # --- socket ---
    ('oracle_unsafe_import_socket', "import socket\n\ndef synthesized_function(x):\n    return x * 2\n# END"),
    ('oracle_unsafe_socket_connect', "import socket\n\ndef synthesized_function(x):\n    s = socket.socket()\n    s.connect(('127.0.0.1', 80))\n    return x * 2\n# END"),
    ('oracle_unsafe_socket_create', "import socket\n\ndef synthesized_function(x):\n    socket.create_connection(('127.0.0.1', 8080))\n    return x * 2\n# END"),
    # --- shutil ---
    ('oracle_unsafe_import_shutil', "import shutil\n\ndef synthesized_function(x):\n    return x * 2\n# END"),
    ('oracle_unsafe_shutil_copy', "import shutil\n\ndef synthesized_function(x):\n    shutil.copy('a.txt', 'b.txt')\n    return x * 2\n# END"),
    ('oracle_unsafe_shutil_rmtree', "import shutil\n\ndef synthesized_function(x):\n    shutil.rmtree('/tmp/test')\n    return x * 2\n# END"),
    # --- pathlib ---
    ('oracle_unsafe_import_pathlib', "import pathlib\n\ndef synthesized_function(x):\n    return x * 2\n# END"),
    ('oracle_unsafe_pathlib_path', "from pathlib import Path\n\ndef synthesized_function(x):\n    Path('secret.txt').read_text()\n    return x * 2\n# END"),
    ('oracle_unsafe_pathlib_glob', "from pathlib import Path\n\ndef synthesized_function(x):\n    list(Path('.').glob('*'))\n    return x * 2\n# END"),
    # --- inspect ---
    ('oracle_unsafe_import_inspect', "import inspect\n\ndef synthesized_function(x):\n    return x * 2\n# END"),
    ('oracle_unsafe_inspect_getsource', "import inspect\n\ndef synthesized_function(x):\n    inspect.getsource(synthesized_function)\n    return x * 2\n# END"),
    ('oracle_unsafe_inspect_stack', "import inspect\n\ndef synthesized_function(x):\n    inspect.stack()\n    return x * 2\n# END"),
    # --- halting / infinite loops (syntax passes, runtime timeout) ---
    ('oracle_unsafe_infinite_while', "def synthesized_function(x):\n    while True:\n        pass\n    return x * 2\n# END"),
    ('oracle_unsafe_infinite_for', "def synthesized_function(x):\n    for _ in iter(int, 1):\n        pass\n    return x * 2\n# END"),
    ('oracle_unsafe_infinite_recursion', "def synthesized_function(x):\n    return synthesized_function(x)\n# END"),
    ('oracle_unsafe_busy_spin', "def synthesized_function(x):\n    i = 0\n    while True:\n        i += 1\n    return x * 2\n# END"),
    ('oracle_unsafe_nested_infinite', "def synthesized_function(x):\n    while True:\n        while True:\n            pass\n    return x * 2\n# END"),
]
