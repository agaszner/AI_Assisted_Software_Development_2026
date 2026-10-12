# Deliberate defect: AC1 mean instead of median

Clearly labelled, **deliberately introduced** defect (homework requirement). Do not fix or modify.

| File | Content |
| --- | --- |
| `faulty_surplus.py` | Faulty `analyse_surplus`: monthly surplus averaged with the **mean** |
| `../../rules/surplus.py` | Fixed (real) implementation: **median** |
| `check_ac1_mean_vs_median.py` | Same AC1 test run against both versions |
| `run_faulty.txt`, `run_fixed.txt` | Saved test-run outputs |

## Defect
AC1: the monthly amount is 70% of the **median** monthly surplus of the last 6 complete months.
The faulty version uses the arithmetic mean, so one outlier month (e.g. a bonus) inflates the plan.

## Expected behaviour
Surpluses 100,000 / 120,000 / 80,000 / 110,000 / 90,000 / 300,000 HUF:
median 105,000 → monthly amount **73,500 HUF**.
Faulty: mean 133,333 → 93,333 HUF, ~27% more than the customer can safely save. The test fails on
`133333 == 105000`; the fixed version passes.

## Running
The file name does not match `test_*.py`, so `make test` does not collect it and stays green.

```bash
cd backend
uv run pytest tests/defects/check_ac1_mean_vs_median.py -v -k faulty   # fails
uv run pytest tests/defects/check_ac1_mean_vs_median.py -v -k fixed    # passes
```
