"""Static AST deny-list oracle (paper §3.4 — AST keyword blacklisting)."""

import ast
from typing import Tuple

BLOCKED_KEYWORDS = {
    '__import__',
    'eval',
    'exec',
    'open',
    'write',
    'compile',
    'execfile',
    'os',
    'sys',
    'subprocess',
    'requests',
    'socket',
    'shutil',
    'pathlib',
    'inspect',
}


def check_restricted_syntax(candidate_code: str) -> Tuple[bool, str]:
    """Return (allowed, diagnostic). allowed=True means no violation."""
    try:
        tree = ast.parse(candidate_code, mode='exec')
    except SyntaxError as exc:
        return False, f'Syntax error during static analysis: {exc}'

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name.split('.')[0]
                if name in BLOCKED_KEYWORDS:
                    return False, f'Restricted import detected: {name}'

        if isinstance(node, ast.ImportFrom):
            module_name = (node.module or '').split('.')[0]
            if module_name in BLOCKED_KEYWORDS:
                return False, f'Restricted import detected: {module_name}'

        if isinstance(node, ast.Name) and node.id in BLOCKED_KEYWORDS:
            return False, f'Restricted symbol detected: {node.id}'
        if isinstance(node, ast.Attribute) and node.attr in BLOCKED_KEYWORDS:
            return False, f'Restricted attribute detected: {node.attr}'
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in BLOCKED_KEYWORDS:
                return False, f'Restricted call detected: {func.id}'
            if isinstance(func, ast.Attribute) and func.attr in BLOCKED_KEYWORDS:
                return False, f'Restricted call detected: {func.attr}'

    return True, ''
