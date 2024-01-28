# Welcome!

This application finds the second lowest cost silver plan (SLCSP) for a group of ZIP codes.

Using Python 3.9.11 or higher, run it with:

```bash
python slcsp.py
```

Note that it expects `plans.csv`, `slcsp.csv`, and `zips.csv` to be present in the same directory as `slcsp.py`.

## Testing, linting, and formatting

Unit tests are available in `test_slcsp.py`. Run them with

```bash
python -m unittest
```

Python files have been formatted with `black`, and `slcsp.py` has been annotated for static type checking with `mypy`.
