import pandas as pd


def transform_product_metadata(product_metadata):
    """
    Transform product metadata into a DataFrame
    """

    if not product_metadata:
        print("No product metadata to transform")
        return None

    product_metadata_df = pd.DataFrame(product_metadata)
    print("Product metadata transformed successfully")

    # Convert all lists to strings
    product_metadata_df = product_metadata_df.applymap(lambda x: str(x) if isinstance(x, list) else x)

    return product_metadata_df
