import ast
import builtins
import multiprocessing
import random
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

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

SAFE_BUILTINS = {
    name: getattr(builtins, name)
    for name in (
        'abs',
        'all',
        'any',
        'bool',
        'dict',
        'float',
        'int',
        'len',
        'list',
        'max',
        'min',
        'range',
        'reversed',
        'round',
        'set',
        'sorted',
        'str',
        'sum',
        'tuple',
        'zip',
    )
}
SAFE_GLOBALS = {'__builtins__': SAFE_BUILTINS}


@dataclass
class Specification:
    description: str
    predicate: Callable[[Dict[str, Any], Dict[str, Any]], bool]
    sample_inputs: Optional[List[Dict[str, Any]]] = field(default_factory=list)
    generator: Optional[Callable[[], Dict[str, Any]]] = None

    def generate_cases(self, count: int = 50) -> Iterable[Dict[str, Any]]:
        if self.sample_inputs:
            for sample in self.sample_inputs:
                yield sample

        if self.generator:
            for _ in range(count):
                yield self.generator()
            return

        boundaries = [0, 1, -1, 2, -2, 10, -10, 100, -100]
        for value in boundaries:
            yield {'value': value}

        for _ in range(count - len(boundaries)):
            yield {'value': random.randint(-100, 100)}


def _check_restricted_syntax(candidate_code: str) -> Tuple[bool, str]:
    try:
        tree = ast.parse(candidate_code, mode='exec')
    except SyntaxError as exc:
        return False, f'Syntax error during static analysis: {exc}'

    for node in ast.walk(tree):
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

    lower = candidate_code.lower()
    for forbidden in BLOCKED_KEYWORDS:
        if forbidden in lower:
            return False, f'Restricted keyword substring detected: {forbidden}'

    return True, ''


def _evaluate_candidate(candidate_code: str, specifications: List[Specification]) -> Tuple[bool, str]:
    namespace: Dict[str, Any] = {}
    exec(candidate_code, SAFE_GLOBALS, namespace)

    for spec in specifications:
        for input_case in spec.generate_cases():
            try:
                if not spec.predicate(namespace, input_case):
                    return False, f'Invariant failed for sample {input_case}: {spec.description}'
            except Exception as exc:
                return False, f'Runtime failure for sample {input_case}: {exc}'

    return True, 'All invariants passed.'


def _sandbox_worker(candidate_code: str, specifications: List[Specification], result_queue: multiprocessing.Queue) -> None:
    try:
        success, diagnostic = _evaluate_candidate(candidate_code, specifications)
    except Exception:
        result_queue.put((False, 'Sandbox exception: ' + traceback.format_exc()))
        return

    result_queue.put((success, diagnostic))


def evaluate_executable_oracle(
    candidate_code: str,
    specifications: List[Specification],
    timeout: float = 0.02,
) -> Tuple[bool, str]:
    is_clean, diagnostic = _check_restricted_syntax(candidate_code)
    if not is_clean:
        return False, diagnostic

    result_queue: multiprocessing.Queue = multiprocessing.Queue(1)
    proc = multiprocessing.Process(
        target=_sandbox_worker,
        args=(candidate_code, specifications, result_queue),
    )
    proc.start()
    proc.join(timeout)

    if proc.is_alive():
        proc.terminate()
        proc.join()
        return False, f'Halting Violation: execution exceeded {timeout * 1000:.0f}ms timeout.'

    if result_queue.empty():
        return False, 'Sandbox failed to return a result.'

    success, diagnostic = result_queue.get()
    return success, diagnostic
