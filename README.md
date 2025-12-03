# Culk Analytics

A Flask-based web application for preparing replenishment reports, sales analytics, and managing purchase orders.

## Overview

This tool performs several operations related to inventory management and purchase orders through a web interface.

## Requirements

- Python 3.x
- Dependencies (install via `pip install -r requirements.txt`)

## Usage

The application is run locally as a Flask web server. To start the server, execute:

```bash
python app.py
```

Once the server is running, open your web browser and navigate to `http://localhost:5000` to access the web interface.
# Culk Analytics

Flask-based tooling for preparing replenishment reports, sales analytics, and managing purchase orders. The app orchestrates multi-step workflows that fetch data from external services, transform and merge them, then export results to Google Sheets and Airtable.

## Requirements

- Python 3.x
- Install dependencies:

```bash
pip install -r requirements.txt
```

## Entry point and server

- Current entrypoint: `python main.py` (starts Flask server on port `5001`).
- Note: README previously referenced `app.py` and port `5000` — ignore that outdated reference.

```bash
python main.py
# then open http://localhost:5001
```

## UI / Webhook actions (what the UI buttons call)

The server exposes webhook routes that start background threads to run workflows. You can trigger them from the browser UI or via `curl`.

- `GET /webhook/prepare_replenishment`
	- Triggers `workflows.replenishment.prepare_replenishment(use_cache_stock_levels=False, use_cache_sales=False)` in a background thread.
	- Optional query params:
		- `use_cache_stock_levels=true` — use cached `cache/shiphero_stock_levels.pkl` when available
		- `use_cache_sales=true` — use cached sales data

- `GET /webhook/populate_production`
	- Runs `export.populate_production()` to read "To Order Qty" from the Google Sheet and create Airtable POs.

- `GET /webhook/push_pos_to_shiphero`
	- Pushes created POs to ShipHero.

- `GET /webhook/packing_slips`
	- Generates PDFs (uses `documents/packing_slips.py`).

- `GET /webhook/sync_shiphero_purchase_orders_to_airtable?created_from=YYYY-MM-DD`
	- Syncs ShipHero POs back to Airtable; `created_from` is optional filter passed into `workflows.sync_shiphero_purchase_orders_to_airtable`.

Examples (curl):

```bash
curl 'http://localhost:5001/webhook/prepare_replenishment'
curl 'http://localhost:5001/webhook/prepare_replenishment?use_cache_stock_levels=true&use_cache_sales=true'
curl 'http://localhost:5001/webhook/populate_production'
```

## Core workflow overview

- Orchestrator: `workflows/replenishment.py`
	- fetch: `fetch/` (ShipHero, Shopify, Airtable)
	- transform: `transform/` (e.g., `transform/stock_levels.py`)
	- merge: `transform/merged_replenishment.py`
	- export: `export/sheets_replenishment.py`

Key pattern: fetch → transform → merge → export.

## Caching & debugging

- ShipHero and Shopify fetchers support pickle caches in `cache/` (e.g., `cache/shiphero_stock_levels.pkl`). Use `use_cache=True` to skip fetching fresh data.
- Debug helpers in `utils/export.py`:

```python
from utils.export import export_df, export_json
export_df(df, 'label')  # writes timestamped CSV to output/
export_json(obj, 'label')
```

- Check `output/` for timestamped CSV/JSON produced by the code or tests.

## API / token handling

- Secrets and IDs live in `config.py` (gitignored). Do not commit credentials.
- Google Sheets uses `service-account.json` for `gspread` authentication; ensure the service account has access to the spreadsheet.
- ShipHero token + pagination helpers are in `utils/shiphero.py`:
	- `refresh_shiphero_token()` will update `config.py` with a new token via `update_config_file_with_new_shiphero_token()`.
	- `fetch_shiphero_with_throttling()` and `fetch_shiphero_paginated_data()` handle GraphQL calls, throttling, and pagination.

## Data conventions

- Source columns in DataFrames: uppercase with spaces (e.g., `On Hand`, `SKU`).
- Derived columns: mixed case (e.g., `Available`, `Backorder`).
- SKU is the canonical join key used across transforms (see `transform/stock_levels.py`).

## Tests

- Run tests (integration-style; may rely on cached data):

```bash
python -m pytest tests/
python tests/test_prepare_stock_levels.py
```

- Tests write intermediate outputs to `output/` for inspection.

## Key files to inspect when changing behavior

- `main.py` — Flask routes / server
- `workflows/replenishment.py` — main orchestrator
- `fetch/shiphero.py` — ShipHero fetcher and cache usage
- `transform/stock_levels.py` — example transform and column conventions
- `utils/shiphero.py` — token refresh, throttling, pagination helpers
- `export/sheets_replenishment.py` — Google Sheets export logic

## Notes / common pitfalls

- README previously referenced `app.py` and port `5000`. Use `main.py` and port `5001`.
- Google Sheets export clears the `Replenishment` worksheet and updates columns — make sure the sheet layout matches expectations before running exports.
- ShipHero GraphQL queries embed warehouse IDs and expect specific shapes; transforms assume node structure like `node.sku`, `node.on_hand` (see `fetch/shiphero.py` and `transform/stock_levels.py`).

If you'd like, I can also:

- run the test suite and report failures
- add short examples for debugging a single workflow locally
- expand the developer checklist for adding new data sources or exports

---

Edited to match current codebase (entry point, webhooks, caches, and helpers).
