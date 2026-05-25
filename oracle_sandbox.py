import builtins
import multiprocessing
import random
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from oracle_pbt import run_pbt_oracle
from oracle_smt import run_smt_oracle
from oracle_static import BLOCKED_KEYWORDS, check_restricted_syntax

# Re-export for backward compatibility
_check_restricted_syntax = check_restricted_syntax

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
    pbt_case_count: int = 50
    expected_multiplier: int = 2

    def generate_cases(self, count: Optional[int] = None) -> Iterable[Dict[str, Any]]:
        case_count = count if count is not None else self.pbt_case_count
        if self.sample_inputs:
            for sample in self.sample_inputs:
                yield sample

        if self.generator:
            for _ in range(case_count):
                yield self.generator()
            return

        boundaries = [0, 1, -1, 2, -2, 10, -10, 100, -100]
        for value in boundaries:
            yield {'value': value}

        remaining = max(0, case_count - len(boundaries))
        for _ in range(remaining):
            yield {'value': random.randint(-100, 100)}


def _evaluate_candidate(
    candidate_code: str,
    specifications: List[Specification],
    *,
    enable_smt: bool = True,
    enable_pbt: bool = True,
) -> Tuple[bool, str]:
    if enable_smt and specifications:
        expected = specifications[0].expected_multiplier
        ok, diagnostic = run_smt_oracle(candidate_code, expected_multiplier=expected)
        if not ok:
            return False, diagnostic

    namespace: Dict[str, Any] = {}
    exec(candidate_code, SAFE_GLOBALS, namespace)

    if enable_pbt:
        return run_pbt_oracle(namespace, specifications, max_cases=specifications[0].pbt_case_count if specifications else 50)

    return True, 'All invariants passed.'


def _sandbox_worker(
    candidate_code: str,
    specifications: List[Specification],
    result_queue: multiprocessing.Queue,
    enable_smt: bool,
) -> None:
    try:
        success, diagnostic = _evaluate_candidate(
            candidate_code,
            specifications,
            enable_smt=enable_smt,
        )
    except Exception:
        result_queue.put((False, 'Sandbox exception: ' + traceback.format_exc()))
        return

    result_queue.put((success, diagnostic))


def evaluate_executable_oracle(
    candidate_code: str,
    specifications: List[Specification],
    timeout: float = 0.02,
    *,
    enable_smt: bool = True,
    use_multiprocessing: bool = True,
) -> Tuple[bool, str]:
    """Run static, SMT (structural/optional Z3), then sandboxed PBT oracles."""
    is_clean, diagnostic = check_restricted_syntax(candidate_code)
    if not is_clean:
        return False, diagnostic

    if not use_multiprocessing:
        try:
            return _evaluate_candidate(candidate_code, specifications, enable_smt=enable_smt)
        except Exception:
            return False, 'Sandbox exception: ' + traceback.format_exc()

    result_queue: multiprocessing.Queue = multiprocessing.Queue(1)
    proc = multiprocessing.Process(
        target=_sandbox_worker,
        args=(candidate_code, specifications, result_queue, enable_smt),
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
