import pandas as pd
from datetime import datetime, timedelta

def transform_stock_levels(stock_levels_data, incoming_stock_data):
    # Convert stock_levels_data to a DataFrame
    stock_levels_df = pd.DataFrame([{
        "SKU": product["node"]["sku"],
        "On Hand": product["node"]["on_hand"],
        "Allocated": product["node"]["allocated"],
        "Available": product["node"]["available"],
        "Backorder": product["node"]["backorder"]
    } for product in stock_levels_data])

    # Merge stock_levels_df with incoming_stock_data on SKU
    stock_levels = stock_levels_df.merge(incoming_stock_data, how="left", left_on="SKU", right_on="sku")

    # Fill NaN values in the 'incoming' column with 0
    stock_levels = stock_levels.assign(incoming=stock_levels["incoming"].fillna(0))

    # Rename the 'incoming' column to 'Incoming Stock'
    stock_levels.rename(columns={"incoming": "Incoming Stock"}, inplace=True)

    # Drop the redundant 'sku' column
    stock_levels.drop(columns=["sku"], inplace=True)

    return stock_levels

def transform_product_metadata(product_metadata):

    if not product_metadata:
        print("No product metadata to transform")
        return None

    product_metadata_df = pd.DataFrame(product_metadata)
    print("Product metadata transformed successfully")

    # Convert all lists to strings
    product_metadata_df = product_metadata_df.applymap(lambda x: str(x) if isinstance(x, list) else x)

    return product_metadata_df

def transform_sales_data(sales_data):
    # Separate orders and line items
    orders = [item for item in sales_data if '__parentId' not in item]
    line_items = [item for item in sales_data if '__parentId' in item]

    # Process orders
    for order in orders:
        order['order_tags'] = ', '.join(order['tags'])
        order['order_date'] = datetime.strptime(order['createdAt'], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")
        del order['tags']
        del order['createdAt']

    # Create past week intervals
    past_week_intervals = []
    today = datetime.now()
    most_recent_sunday = today - timedelta(days=today.weekday() + 1)
    for i in range(12):
        week_end = most_recent_sunday - timedelta(days=i * 7)
        week_start = week_end - timedelta(days=6)
        past_week_intervals.append((week_start.strftime("%Y-%m-%d"), week_end.strftime("%Y-%m-%d"), i + 1))

    # Debugging: Print past week intervals
    print("Past Week Intervals:")
    for interval in past_week_intervals:
        print(interval)

    # Assign weeks_ago to orders
    for order in orders:
        order_date = datetime.strptime(order['order_date'], "%Y-%m-%d")
        order['weeks_ago'] = None  # Default to None
        for week_start, week_end, weeks_ago in past_week_intervals:
            if week_start <= order_date.strftime("%Y-%m-%d") <= week_end:
                # Find the Sunday of the week interval
                week_end_date = datetime.strptime(week_end, "%Y-%m-%d")
                sunday_date = week_end_date.strftime("%b%d")
                order['weeks_ago_string'] = f"{weeks_ago}_weeks_ago_{sunday_date}"
                break

    # Convert orders and line items to DataFrames
    orders_df = pd.DataFrame(orders)
    line_items_df = pd.DataFrame(line_items)

    # Convert quantity to integer
    line_items_df['quantity'] = line_items_df['quantity'].astype(int)

    # Rename columns
    orders_df.rename(columns={'name': 'order_number'}, inplace=True)

    # Merge orders and line items
    line_items_and_orders = pd.merge(line_items_df, orders_df, left_on='__parentId', right_on='id', suffixes=('_line', '_order'))

    # Create time series DataFrame
    sales_df = line_items_and_orders.pivot_table(
        index='sku',
        columns='weeks_ago_string',
        values='quantity',
        aggfunc='sum',
        fill_value=0
    )

    # Reset index to keep SKU as a column
    sales_df.reset_index(inplace=True)

    # Sort columns in descending order (most recent week first)
    sales_df = sales_df.reindex(sorted(sales_df.columns, reverse=True), axis=1)

    return sales_df