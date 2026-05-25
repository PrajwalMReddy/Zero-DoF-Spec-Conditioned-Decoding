"""Picklable specifications for benchmark scripts (Windows multiprocessing)."""

from oracle_sandbox import Specification


def oracle_invoke_predicate(namespace, sample):
    fn = namespace.get('synthesized_function')
    if not callable(fn):
        return False
    fn(sample.get('value', 0))
    return True


def oracle_double_predicate(namespace, sample):
    fn = namespace.get('synthesized_function')
    if not callable(fn):
        return False
    return fn(sample.get('value', 0)) == sample['value'] * 2


def spec_invoke() -> Specification:
    return Specification(
        description='invoke synthesized_function',
        predicate=oracle_invoke_predicate,
        sample_inputs=[{'value': 0}],
    )


def spec_double() -> Specification:
    return Specification(
        description='synthesized_function should double integer inputs',
        predicate=oracle_double_predicate,
        sample_inputs=[{'value': x} for x in [0, 1, -1, 10]],
        pbt_case_count=20,
    )
