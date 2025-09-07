# Data Requirements

This project expects batch CSV inputs with the following schema:

- Columns: `time`, `species`, `concentration`
- Types: `time` (numeric), `species` (string), `concentration` (numeric)
- No missing values in `time` or `concentration`.

Limits (configurable via environment variables):
- `OW_SC_MAX_CSV_BYTES`: maximum CSV file size in bytes (default 10,485,760).
- `OW_SC_MAX_CSV_ROWS`: maximum number of rows (default 1,000,000).

Examples
- Minimal row: `0,SO4,1.0`
- Full file example lives under `data/` (you can generate with `scripts/generate_demo_data.py`).

Validation
- Files exceeding configured limits or missing required columns will be rejected.
- Non-numeric `time`/`concentration` or NaNs will raise validation errors.

Recommendations
- Use UTF-8 encoding and include a header row.
- Keep `species` codes consistent across datasets (e.g., `SO4`, `As`, `Ni`).
- Use `artifacts/` for outputs and `reports/` for generated certificates.
