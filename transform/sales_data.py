import pandas as pd
from datetime import datetime, timedelta


def transform_sales_data(sales_data):
    """
    Transform Shopify sales data into a time series DataFrame
    """

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

    # Adjust for the case when today is Sunday
    if today.weekday() == 6:
        most_recent_sunday = today

    # Generate intervals for the past 52 complete weeks
    for i in range(0, 52):
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
                week_start_date = datetime.strptime(week_start, "%Y-%m-%d")
                sunday_date = week_start_date.strftime("%b%d")
                order['weeks_ago_string'] = f"sales_{weeks_ago}_weeks_ago_{sunday_date}"
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

    # Keep only the past 52 weeks of columns
    sales_columns = [f"sales_{i}_weeks_ago_" for i in range(1, 53)]
    sales_df = sales_df[[col for col in sales_df.columns if any(col.startswith(prefix) for prefix in sales_columns)]]

    print(sales_df)

    # Reset index to keep SKU as a column
    sales_df.reset_index(inplace=True)

    # Sort columns in descending order (most recent week first)
    sales_df = sales_df.reindex(sorted(sales_df.columns, reverse=True), axis=1)

    return sales_df
