"""Format oracle failures for injection into committed context (paper §3.1)."""

import re


def format_checkpoint_diagnostic(raw_diagnostic: str) -> str:
    """Map internal oracle text to inline comment form used by Zero-SCD."""
    if not raw_diagnostic:
        return '// Error: unknown invariant violation.'

    match = re.search(r'Invariant violated for input (\{[^}]+\})', raw_diagnostic)
    if match:
        return f'// Error: invariant violated for input {match.group(1)}'

    match = re.search(r'Invariant failed for sample (\{[^}]+\})', raw_diagnostic)
    if match:
        return f'// Error: invariant violated for input {match.group(1)}'

    if raw_diagnostic.startswith('Restricted'):
        return f'// Error: security policy violation — {raw_diagnostic}'

    if raw_diagnostic.startswith('Halting Violation'):
        return f'// Error: {raw_diagnostic}'

    if raw_diagnostic.startswith('SMT'):
        return f'// Error: {raw_diagnostic}'

    return f'// Error: {raw_diagnostic}'
