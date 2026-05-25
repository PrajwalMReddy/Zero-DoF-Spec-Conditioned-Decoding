"""Direct oracle positive cases: safe code that must be accepted."""

ORACLE_SAFE_CASES = [
    ('oracle_safe_double', "def synthesized_function(x):\n    return x * 2\n# END"),
    ('oracle_safe_double_value', "def synthesized_function(value):\n    return value * 2\n# END"),
    ('oracle_safe_multiline_doc', (
        "def synthesized_function(x):\n"
        '    """execution should remain safe in comments."""\n'
        "    return x * 2\n# END"
    )),
    ('oracle_safe_tempvar', (
        "def synthesized_function(x):\n"
        "    doubled = x * 2\n"
        "    return doubled\n# END"
    )),
    ('oracle_safe_branch', (
        "def synthesized_function(x):\n"
        "    if x < 0:\n"
        "        return x * 2\n"
        "    return x * 2\n# END"
    )),
    ('oracle_safe_clamp', (
        "def synthesized_function(x):\n"
        "    result = x * 2\n"
        "    return max(-1000, min(1000, result))\n# END"
    )),
]
