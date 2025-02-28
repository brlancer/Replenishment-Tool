import pandas as pd
from pyairtable import Table
import config
import numpy as np
from prepare_replenishment import prepare_replenishment

def get_variant_record_ids_by_sku(variants_table, skus):
    """Fetch the record IDs for the given SKUs from the Variants table."""
    print("Fetching all records from the Variants table...")
    all_records = variants_table.all()
    print(f"Fetched {len(all_records)} records from the Variants table.")

    record_ids = {}
    for record in all_records:
        sku = record['fields'].get('SKU')
        if sku in skus:
            record_ids[sku] = record['id']
    
    return record_ids

def export_airtable_replenishment(replenishment_df):
    
    # Write structure of replenishment_df to output/replenishment_schema.csv
    replenishment_df.dtypes.to_csv("output/replenishment_schema.csv", header=False)

    # Keep only the columns that are present in Airtable
    # sku, sales_8_weeks_ago ... sales_1_week_ago, on_hand, allocated, available, backorder, incoming_stock, updated_at
    replenishment_df = replenishment_df[['sku', 'sales_8_weeks_ago', 'sales_7_weeks_ago', 'sales_6_weeks_ago', 'sales_5_weeks_ago', 'sales_4_weeks_ago', 'sales_3_weeks_ago', 'sales_2_weeks_ago', 'sales_1_week_ago', 'on_hand', 'allocated', 'available', 'backorder', 'incoming_stock', 'updated_at']]

    # Initialize Airtable tables
    print("Initializing Airtable tables...")
    replenishment_table = Table(config.AIRTABLE_API_KEY, config.AIRTABLE_PRODUCTION_DEV_BASE_ID, "Replenishment")
    variants_table = Table(config.AIRTABLE_API_KEY, config.AIRTABLE_PRODUCTION_DEV_BASE_ID, "Variants")

    # Delete all existing records in the Replenishment table
    print("Fetching existing records from the Replenishment table...")
    existing_records = replenishment_table.all()
    record_ids = [record['id'] for record in existing_records]
    print(f"Found {len(record_ids)} records to delete.")
    replenishment_table.batch_delete(record_ids)
    print("Deleted existing records.")

    # Get the record IDs for the SKUs in the Variants table
    print("Fetching record IDs for SKUs from the Variants table...")
    skus = replenishment_df['sku'].unique()
    variant_record_ids = get_variant_record_ids_by_sku(variants_table, skus)
    print(f"Found record IDs for {len(variant_record_ids)} SKUs.")

    # Prepare records to be inserted
    print("Preparing records to be inserted...")
    records_to_insert = []
    for _, row in replenishment_df.iterrows():
        record = row.replace({np.nan: None}).to_dict()  # Replace NaN with None
        sku = record['sku']  # Access the SKU value directly
        variant_id = variant_record_ids.get(sku)
        if variant_id:
            record['Variant'] = [variant_id]
        records_to_insert.append(record)
    print(f"Prepared {len(records_to_insert)} records for insertion.")

    # Insert new records into the Replenishment table using batch_create
    print("Inserting new records into the Replenishment table...")
    batch_size = 10  # Adjust the batch size as needed
    for i in range(0, len(records_to_insert), batch_size):
        batch = records_to_insert[i:i + batch_size]
        replenishment_table.batch_create(batch)
    print("Inserted new records.")

    print("Replenishment data exported to Airtable")

# Test the function
if __name__ == "__main__":
    # Sample DataFrames for testing
    stock_levels_df = pd.read_csv("output/stock_levels_2025-17-01 17-46-18.csv")
    sales_df = pd.read_csv("output/sales_2025-17-01 17-46-42.csv")
    product_metadata_df = pd.read_csv("output/product_metadata_2025-17-01 16-43-59.csv")

    replenishment_df = prepare_replenishment(stock_levels_df, sales_df, product_metadata_df)

    export_airtable_replenishment(replenishment_df)