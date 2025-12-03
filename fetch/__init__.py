"""
Fetch module - Central import point for all data fetching functions.
This module provides backwards compatibility for imports from the original fetch_data.py file.
"""

from fetch.airtable import (
    fetch_airtable_incoming_stock,
    fetch_airtable_product_metadata,
)

from fetch.shiphero import (
    fetch_shiphero_stock_levels,
    fetch_purchase_orders_from_shiphero,
)

from fetch.shopify import (
    fetch_shopify_sales_data,
    fetch_shopify_inventory_data,
)

__all__ = [
    'fetch_airtable_incoming_stock',
    'fetch_airtable_product_metadata',
    'fetch_shiphero_stock_levels',
    'fetch_purchase_orders_from_shiphero',
    'fetch_shopify_sales_data',
    'fetch_shopify_inventory_data',
]
