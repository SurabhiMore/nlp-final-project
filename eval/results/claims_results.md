# Claim Checker Evaluation Results

Evaluation of `pipeline/claims.py` against `eval/claims_labels.jsonl`.

## Summary Metrics

| Dataset Split | Answers | Unsupported (Gold) | Precision | Recall | F1 Score | Accuracy |
|---|---|---|---|---|---|---|
| **Real answers** | 93 | 8 | **1.000** | **1.000** | **1.000** | **1.000** |
| **Perturbed answers** | 30 | 30 | **1.000** | **1.000** | **1.000** | **1.000** |
| **Combined overall** | 123 | 38 | **1.000** | **1.000** | **1.000** | **1.000** |

## Session 7 User Test Failures (Regression Test)

- **P2 ('Did you move to Arles?'):** Flagged = `True` (Flags: `['1890', 'Auvers-sur-Oise']`)
  - Added Auvers-sur-Oise and 1890, both absent from cited passages.
- **P4 ('Did you die?'):** Flagged = `True` (Flags: `['July 1890']`)
  - Added July 1890, absent from cited passage.

## False Flags (Wrongly Flagged / False Positives)

None. All fully supported answers passed without false flags.

## Misses (Undetected Unsupported Details / False Negatives)

None. All answers containing unsupported details were correctly detected.
