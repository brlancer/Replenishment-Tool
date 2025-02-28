from fetch_airtable_product_metadata import fetch_airtable_product_metadata
from transform_product_metadata import transform_product_metadata
from export import export_df

def prepare_product_metadata():
    print("Preparing product metadata...")

    product_metadata = fetch_airtable_product_metadata()
    if not product_metadata:
        print("Failed to fetch product metadata")
        return None

    product_metadata_df = transform_product_metadata(product_metadata)
    if product_metadata_df.empty:
        print("Failed to transform product metadata")
        return None
    
    if product_metadata_df is not None:
        print("Product metadata prepared successfully")
        print(product_metadata_df.head())
        export_df(product_metadata_df, "product_metadata")
        return product_metadata_df

    

# Test the function
if __name__ == "__main__":
    prepare_product_metadata()