# Results summary

## Summary counts

- Prompt cases processed: 94
- Prompt accepted: 94
- Prompt blocked: 0
- Oracle direct unsafe cases: 52
- Oracle unsafe blocked: 52
- Oracle direct safe cases: 6
- Oracle safe accepted (no false reject): 6
- Oracle safe blocked (false reject): 0

## Blocked reason breakdown

| Reason | Count |
|---|---|
| Restricted call detected: eval | 4 |
| Restricted call detected: exec | 3 |
| Restricted call detected: compile | 3 |
| Restricted call detected: execfile | 2 |
| Restricted call detected: open | 3 |
| Restricted call detected: write | 2 |
| Restricted call detected: __import__ | 3 |
| Restricted import detected: os | 4 |
| Restricted symbol detected: os | 1 |
| Restricted import detected: sys | 3 |
| Restricted import detected: subprocess | 4 |
| Restricted import detected: requests | 3 |
| Restricted import detected: socket | 3 |
| Restricted import detected: shutil | 3 |
| Restricted import detected: pathlib | 3 |
| Restricted import detected: inspect | 3 |
| Halting Violation: execution exceeded 50ms timeout. | 5 |

## Notes

The prompt sweep: 94 accepted, 0 blocked (stub mode typically accepts safe completions).
The oracle unsafe suite: 52/52 blocked. Safe suite: 6/6 accepted.
See `outcome_bar.png` and `reject_pie.png` for visual summaries.
