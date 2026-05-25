"""Structural / optional Z3 SMT oracle (paper §3.2 — SMT solver oracles)."""

import ast
from typing import Optional, Tuple

try:
    import z3

    Z3_AVAILABLE = True
except ImportError:
    z3 = None
    Z3_AVAILABLE = False


def _is_while_true(node: ast.AST) -> bool:
    if not isinstance(node, ast.While):
        return False
    test = node.test
    if isinstance(test, ast.Constant) and test.value is True:
        return True
    return False


def _extract_return_multiplier(func_def: ast.FunctionDef) -> Optional[int]:
    """If body is only `return <name> * <int>`, return the integer multiplier."""
    if len(func_def.body) != 1 or not isinstance(func_def.body[0], ast.Return):
        return None
    value = func_def.body[0].value
    if not isinstance(value, ast.BinOp) or not isinstance(value.op, ast.Mult):
        return None
    left, right = value.left, value.right
    if isinstance(right, ast.Constant) and isinstance(right.value, int):
        if isinstance(left, ast.Name):
            return int(right.value)
    if isinstance(left, ast.Constant) and isinstance(left.value, int):
        if isinstance(right, ast.Name):
            return int(left.value)
    return None


def check_structural_properties(candidate_code: str, *, expected_multiplier: int = 2) -> Tuple[bool, str]:
    """AST-level structural checks (always on)."""
    try:
        tree = ast.parse(candidate_code, mode='exec')
    except SyntaxError as exc:
        return False, f'SMT structural: syntax error: {exc}'

    for node in ast.walk(tree):
        if _is_while_true(node):
            return False, 'SMT structural: unbounded while True loop detected.'

    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == 'synthesized_function':
            mult = _extract_return_multiplier(node)
            if mult is not None and mult != expected_multiplier:
                return (
                    False,
                    f'SMT structural: return multiplier {mult} != required {expected_multiplier}.',
                )

    return True, ''


def check_z3_algebraic(
    candidate_code: str,
    *,
    expected_multiplier: int = 2,
) -> Tuple[bool, str]:
    """Optional Z3 check: exists input where f(x) != expected_multiplier * x."""
    if not Z3_AVAILABLE:
        return True, ''

    try:
        tree = ast.parse(candidate_code, mode='exec')
    except SyntaxError:
        return True, ''

    func_def = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == 'synthesized_function':
            func_def = node
            break
    if func_def is None:
        return True, ''

    mult = _extract_return_multiplier(func_def)
    if mult is None:
        return True, ''

    x = z3.Int('x')
    solver = z3.Solver()
    solver.add(z3.Exists([x], mult * x != expected_multiplier * x))
    if solver.check() == z3.sat:
        model = solver.model()
        witness = model.eval(x)
        return False, f'SMT solver: counterexample input x={witness}'

    return True, ''


def run_smt_oracle(
    candidate_code: str,
    *,
    expected_multiplier: int = 2,
    use_z3: bool = True,
) -> Tuple[bool, str]:
    ok, msg = check_structural_properties(candidate_code, expected_multiplier=expected_multiplier)
    if not ok:
        return ok, msg
    if use_z3:
        ok, msg = check_z3_algebraic(candidate_code, expected_multiplier=expected_multiplier)
        if not ok:
            return ok, msg
    return True, 'SMT: structural and algebraic checks passed.'
