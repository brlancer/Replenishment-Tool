# Culk Analytics — AI Coding Agent Instructions

Short, repo-specific notes for an AI coding agent to be productive quickly.

1) Big picture
- Flask app (`main.py`) exposes webhook routes that start background threads calling workflow functions in `workflows/` (e.g. `workflows/replenishment.prepare_replenishment`).
- Core flow: fetch (`fetch/`) → transform (`transform/`) → merge (`transform/merged_replenishment.py`) → export (`export/` or `export/sheets_replenishment.py`).

2) Key files & examples
- Orchestrator: `workflows/replenishment.py` (calls `fetch/*`, `transform/*`, `export/*`).
- ShipHero fetcher: `fetch/shiphero.py` (uses `cache/shiphero_stock_levels.pkl`, argument `use_cache=True`).
- Transform example: `transform/stock_levels.py` (creates `SKU`, `On Hand`, `Available`, `Backorder`).
- Google Sheets export: `export/sheets_replenishment.py` (uses `service-account.json`, sheet key `1L35Drb5FZfPsV7...`, worksheets `Data - Replenishment` and `Replenishment`).

3) Runtime & useful commands
- Start server: `python main.py` — server listens on port `5001` (README references `app.py`; ignore that).
- Trigger workflows (examples):
  - Prepare (fresh): `curl 'http://localhost:5001/webhook/prepare_replenishment'`
  - Prepare (use caches): `curl 'http://localhost:5001/webhook/prepare_replenishment?use_cache_stock_levels=true&use_cache_sales=true'`
  - Populate production: `curl 'http://localhost:5001/webhook/populate_production'`

4) Caching & debugging
- ShipHero and Shopify fetchers support pickle caches under `cache/`. Use `use_cache=True` when calling fetch functions to reuse cached data.
- Debug helpers: `utils/export.py` provides `export_df(df, label)` and `export_json(data, label)` which write timestamped files into `output/` and print the data.
- Many functions print progress; inspect `output/` and `cache/` when diagnosing issues.

5) API/token patterns to know
- Secrets live in `config.py` (gitignored in normal workflow); `service-account.json` is used for Google APIs.
- ShipHero token refresh & pagination live in `utils/shiphero.py`: `refresh_shiphero_token()`, `fetch_shiphero_with_throttling()` and `fetch_shiphero_paginated_data()` — code updates `config.py` via `update_config_file_with_new_shiphero_token()`.

6) Data & naming conventions (concrete)
- Source columns: uppercase with spaces (e.g., `On Hand`, `SKU`).
- Derived columns in transforms: mixed case (e.g., `Available`, `Backorder`).
- Merges: SKU is the canonical join key across `transform/stock_levels.py` and related transforms; drop redundant join columns after merge.

7) Tests
- Tests are integration-style and may rely on cached data. Run:
  - `python -m pytest tests/` or `python tests/test_prepare_stock_levels.py`
- Tests write intermediate CSV/JSON to `output/` for inspection.

8) Common pitfalls / local setup notes
- README contains outdated references (`app.py` and port 5000) — use `main.py` and `http://localhost:5001`.
- Google Sheets: ensure `service-account.json` has access to the spreadsheet; `export/sheets_replenishment.py` clears and updates worksheets.
- ShipHero queries embed warehouse IDs and expect specific shapes (see `fetch/shiphero.py` query and `transform/stock_levels.py` assumptions about fields).

If anything here looks ambiguous or you want me to expand a specific area (example runs, debugging checklist, or adding more file-level examples), tell me which part to iterate on.
