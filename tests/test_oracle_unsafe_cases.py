import pytest

from oracle_sandbox import Specification, evaluate_executable_oracle
from oracle_unsafe_cases import ORACLE_UNSAFE_CASES


def _invoke_predicate(namespace, sample):
    fn = namespace.get('synthesized_function')
    if not callable(fn):
        return False
    fn(sample.get('value', 0))
    return True


@pytest.mark.parametrize('case_name,code', ORACLE_UNSAFE_CASES)
def test_oracle_unsafe_case_is_blocked(case_name, code):
    spec = Specification(
        description='invoke synthesized_function',
        predicate=_invoke_predicate,
        sample_inputs=[{'value': 0}],
    )
    success, diagnostic = evaluate_executable_oracle(code, [spec], timeout=0.05)
    assert not success, f'{case_name} should be blocked, got: {diagnostic}'
