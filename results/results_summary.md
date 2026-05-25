# Results summary

## Summary counts

- Prompt cases processed: 37
- Prompt accepted: 37
- Prompt blocked: 0
- Oracle direct unsafe cases: 7
- Oracle blocked: 7

## Blocked reason breakdown

| Reason | Count |
|---|---|
| Restricted import detected: os | 1 |
| Restricted call detected: eval | 1 |
| Restricted call detected: open | 1 |
| Restricted import detected: subprocess | 1 |
| Restricted call detected: compile | 1 |
| Restricted call detected: exec | 1 |
| Restricted call detected: __import__ | 1 |

## Notes

The prompt sweep accepted all prompt cases in this run.
The oracle direct tests blocked explicit unsafe candidate code patterns.
See `outcome_bar.png` and `reject_pie.png` for visual summaries.
