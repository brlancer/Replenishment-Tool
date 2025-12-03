import pandas as pd


def transform_stock_levels(stock_levels_data, incoming_stock_data, committed_stock_data):
    """
    Transform stock levels data into a DataFrame
    """

    # Convert stock_levels_data to a DataFrame with only SKU and On Hand
    stock_levels_df = pd.DataFrame([{
        "SKU": product["node"]["sku"],
        "On Hand": product["node"]["on_hand"]
    } for product in stock_levels_data])

    # Merge stock_levels_df with incoming_stock_data on SKU
    stock_levels = stock_levels_df.merge(incoming_stock_data, how="left", left_on="SKU", right_on="sku")

    # Fill NaN values in the 'incoming' column with 0
    stock_levels = stock_levels.assign(incoming=stock_levels["incoming"].fillna(0))

    # Rename the 'incoming' column to 'Incoming Stock'
    stock_levels.rename(columns={"incoming": "Incoming Stock"}, inplace=True)

    # Drop the redundant 'sku' column
    stock_levels.drop(columns=["sku"], inplace=True)

    # Create DataFrame from committed_stock_data with "id" and "sku"
    sku_df = pd.DataFrame([{
        "id": item["id"],
        "sku": item["sku"]
    } for item in committed_stock_data if "sku" in item])

    # Create DataFrame from committed_stock_data with "__parentId" and "committed"
    committed_df = pd.DataFrame([{
        "__parentId": item["__parentId"],
        "committed": next((q["quantity"] for q in item["quantities"] if q["name"] == "committed"), 0)
    } for item in committed_stock_data if "quantities" in item and item["location"]["id"] == "gid://shopify/Location/71392264438"])

    # Merge the two DataFrames on "id" and "__parentId"
    merged_df = committed_df.merge(sku_df, how="left", left_on="__parentId", right_on="id")

    # Create a DataFrame with "sku" and "committed"
    final_committed_df = merged_df[["sku", "committed"]]

    # Merge final_committed_df with stock_levels on SKU
    stock_levels = stock_levels.merge(final_committed_df, how="left", left_on="SKU", right_on="sku")

    # Fill NaN values in the 'committed' column with 0
    stock_levels = stock_levels.assign(committed=stock_levels["committed"].fillna(0))

    # Drop the redundant 'sku' column
    stock_levels.drop(columns=["sku"], inplace=True)

    # Create columns for 'Available'
    stock_levels["Available"] = stock_levels.apply(lambda row: max(0, row["On Hand"] - row["committed"]), axis=1)

    #  Create columns for 'Backorder'
    stock_levels["Backorder"] = stock_levels.apply(lambda row: min(0, row["On Hand"] - row["committed"]), axis=1)

    return stock_levels
