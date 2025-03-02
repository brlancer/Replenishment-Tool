# PO Builder 3.0

A command-line tool for preparing replenishment reports and populating Airtable production database with new purchase orders.

## Overview

This tool performs two main operations:

1. Prepare replenishment reports by gathering data from multiple sources
2. Publish new purchase orders to the Production base in Airtable

## Requirements

- Python 3.x
- Dependencies (install via `pip install -r requirements.txt`)

## Usage

The script is executed from the terminal by selecting one of two operations:

```
python main.py <task>
```

Available tasks:

- `prepare_replenishment` - Prepares the replenishment report by:

  - Getting current stock levels from ShipHero
  - Getting past 8 weeks sales from Shopify
  - Transforming sales data into time series
  - Getting product metadata from Airtable
  - Uploading the dataset to the Replenishment worksheet in Drive

- `populate_airtable` - Publishes new POs to the Production base by:
  - Getting reorder quantities from the Replenishment worksheet
  - Transforming them into New Purchase Orders
  - Populating the Production base in Airtable

## Examples

```
# To prepare replenishment report
python main.py prepare_replenishment

# To populate Airtable with new purchase orders
python main.py populate_airtable
```

## Notes

The script will exit with an error message if an invalid task is provided or if no task is specified.
