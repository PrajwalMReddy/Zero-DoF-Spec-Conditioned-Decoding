import pytest

from oracle_diagnostics import format_checkpoint_diagnostic
from oracle_pbt import run_pbt_oracle
from oracle_safe_cases import ORACLE_SAFE_CASES
from oracle_sandbox import Specification, evaluate_executable_oracle
from oracle_smt import check_structural_properties, run_smt_oracle
from oracle_static import check_restricted_syntax
from oracle_unsafe_cases import ORACLE_UNSAFE_CASES
from zero_scd_engine import retry_sampling_temperature


def double_predicate(namespace, sample):
    return namespace['synthesized_function'](sample['value']) == sample['value'] * 2


def test_retry_temperature_matches_paper_gamma():
    assert retry_sampling_temperature(0) == pytest.approx(0.2)
    assert retry_sampling_temperature(1) == pytest.approx(0.7)


def test_format_checkpoint_diagnostic_invariant():
    raw = "Invariant violated for input {'value': 3}: must double"
    assert 'invariant violated for input' in format_checkpoint_diagnostic(raw)


def test_smt_rejects_wrong_multiplier():
    code = "def synthesized_function(x):\n    return x * 3\n"
    ok, msg = run_smt_oracle(code, expected_multiplier=2)
    assert not ok
    assert 'multiplier' in msg


def test_smt_rejects_while_true():
    code = "def synthesized_function(x):\n    while True:\n        pass\n    return x * 2\n"
    ok, msg = check_structural_properties(code)
    assert not ok
    assert 'while True' in msg


@pytest.mark.parametrize('case_name,code', ORACLE_SAFE_CASES)
def test_oracle_safe_cases_accepted(case_name, code):
    spec = Specification(
        description='double values',
        predicate=double_predicate,
        sample_inputs=[{'value': 0}, {'value': 2}],
        pbt_case_count=10,
    )
    success, diagnostic = evaluate_executable_oracle(code, [spec], timeout=1.0)
    assert success, f'{case_name} should be accepted: {diagnostic}'


@pytest.mark.parametrize('case_name,code', ORACLE_UNSAFE_CASES[:5])
def test_static_still_blocks_subset(case_name, code):
    ok, _ = check_restricted_syntax(code)
    assert not ok
