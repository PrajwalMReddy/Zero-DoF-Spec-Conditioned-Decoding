"""Property-based testing oracle (paper §3.2 — PBT oracles)."""

from typing import Any, Dict, List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from oracle_sandbox import Specification


def run_pbt_oracle(
    namespace: Dict[str, Any],
    specifications: List['Specification'],
    *,
    max_cases: int = 50,
) -> Tuple[bool, str]:
    """Execute predicates over generated input cases (fuzzed boundaries + random draws)."""
    for spec in specifications:
        for input_case in spec.generate_cases(count=max_cases):
            try:
                if not spec.predicate(namespace, input_case):
                    return (
                        False,
                        f'Invariant violated for input {input_case}: {spec.description}',
                    )
            except Exception as exc:
                return False, f'Runtime failure for input {input_case}: {exc}'

    return True, 'PBT: all sampled invariants passed.'
