import pytest

from oracle_sandbox import (
    Specification,
    SAFE_GLOBALS,
    _check_restricted_syntax,
    evaluate_executable_oracle,
)


def test_check_restricted_syntax_blocks_eval():
    code = "eval('2 + 2')"
    allowed, diagnostic = _check_restricted_syntax(code)
    assert not allowed
    assert "Restricted call" in diagnostic or "Restricted symbol" in diagnostic


def test_check_restricted_syntax_allows_safe_code():
    code = "def foo(x):\n    return x + 1\n"
    allowed, diagnostic = _check_restricted_syntax(code)
    assert allowed
    assert diagnostic == ''


def double_predicate(ns, sample):
    return ns['synthesized_function'](sample['value']) == sample['value'] * 2


def test_evaluate_executable_oracle_accepts_good_function():
    spec = Specification(
        description='double values',
        predicate=double_predicate,
        sample_inputs=[{'value': 1}, {'value': 2}, {'value': -3}],
    )

    code = "def synthesized_function(value):\n    return value * 2\n"
    success, diagnostic = evaluate_executable_oracle(code, [spec], timeout=1.0)
    assert success
    assert 'All invariants passed' in diagnostic


def test_evaluate_executable_oracle_rejects_bad_function():
    spec = Specification(
        description='double values',
        predicate=double_predicate,
        sample_inputs=[{'value': 1}],
    )

    code = "def synthesized_function(value):\n    return value + 1\n"
    success, diagnostic = evaluate_executable_oracle(code, [spec], timeout=1.0)
    assert not success
    assert 'Invariant failed' in diagnostic or 'Runtime failure' in diagnostic


if __name__ == '__main__':
    pytest.main([__file__])
