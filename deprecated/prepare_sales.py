import pandas as pd
from fetch import fetch_shopify_sales_data
from transform import transform_sales_data
from utils import export_df

def prepare_sales():
    print("Preparing sales...")

    sales_data = fetch_shopify_sales_data()
    if not sales_data:
        print("No sales data fetched")
        return None

    sales_df = transform_sales_data(sales_data)
    if sales_df.empty:
        print("Sales DataFrame is empty")
        return None

    if sales_df is not None:
        print("Sales prepared successfully")
        print(sales_df.head())
        export_df(sales_df, "sales")

    return sales_df

# Test the function
if __name__ == "__main__":
    sales_df = prepare_sales()
    if sales_df is not None:
        print("Sales DataFrame:")
        print(sales_df.head())
    else:
        print("Failed to prepare sales DataFrame")