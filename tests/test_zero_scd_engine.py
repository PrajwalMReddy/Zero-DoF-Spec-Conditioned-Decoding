from zero_scd_engine import run_zero_scd_synthesis, default_specification
from raw_generation_baseline import run_baseline


def test_run_zero_scd_synthesis_stubbed():
    output = run_zero_scd_synthesis(
        '# Complete the function implementation below',
        [default_specification()],
        max_retries=3,
    )

    assert 'synthesized_function' in output
    assert '# END' in output


def test_raw_generation_baseline_stubbed():
    output = run_baseline('# Baseline synthesis prompt\n', temperature=0.2, max_tokens=64)
    assert output
    assert '# END' in output or 'synthesized_function' in output
