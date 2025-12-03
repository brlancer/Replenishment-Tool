import requests
from urllib.parse import urlencode
from config import AIRTABLE_API_KEY, AIRTABLE_VARIANTS_ENDPOINT, AIRTABLE_PRODUCTION_DEV_BASE_ID
import pandas as pd
from pyairtable import Table


def fetch_airtable_incoming_stock():
    """
    Fetches incoming stock data from Airtable and processes it into a pandas DataFrame.
    This function retrieves records from the "Line Items" table in Airtable where the 
    "PO Status" is either 'Open' or 'Draft'. It extracts relevant fields from these records, 
    calculates the incoming stock by subtracting the received quantity from the ordered quantity, 
    and groups the data by SKU to sum the incoming stock for each SKU.
    Returns:
      pandas.DataFrame: A DataFrame containing the SKU and the summed incoming stock for each SKU.
    """

    print("Fetching incoming stock data from Airtable...")
    
    # print("Initializing Airtable table...")
    line_items_table = Table(AIRTABLE_API_KEY, AIRTABLE_PRODUCTION_DEV_BASE_ID, "Line Items")

    # print("Fetching records with PO Status = 'Open'...")
    records = line_items_table.all(formula="OR({PO Status} = 'Open', {PO Status} = 'Draft')", fields=['Position - PO # - SKU', 'sku', 'Quantity Ordered', 'Quantity Received'])
    # print(f"Fetched {len(records)} records.")
    # print("First 5 records:")
    # for record in records[:5]:
    #     print(record)

    # print("Extracting relevant fields...")
    data = []
    for record in records:
        fields = record['fields']
        data.append({
            'Position - PO # - SKU': fields.get('Position - PO # - SKU', ''),
            'sku': fields.get('sku', ''),
            'ordered': fields.get('Quantity Ordered', 0),
            'received': fields.get('Quantity Received', 0)
        })
    # print(f"Extracted data for {len(data)} records.")

    # print("Converting data to DataFrame...")
    df = pd.DataFrame(data)
    # print("DataFrame created:")
    # print(df.head())

    # print("Ensuring 'sku' column contains only strings and cleaning 'sku' values...")
    df['sku'] = df['sku'].apply(lambda x: str(x[0]) if isinstance(x, list) and len(x) > 0 else str(x) if not isinstance(x, str) else x)

    # print("Calculating 'pending' field...")
    df['incoming'] = df['ordered'] - df['received']
    # print("Calculated 'pending' field:")
    # print(df.head())

    # print("Grouping by 'sku' and summing 'incoming'...")
    grouped_df = df.groupby('sku')['incoming'].sum().reset_index()
    # print("Grouped DataFrame:")
    # print(grouped_df.head())

    return grouped_df

def fetch_airtable_product_metadata():
    """
    Fetches product metadata from Airtable and processes it into a pandas DataFrame.
    This function retrieves records from the "Variants" table in Airtable and extracts
    relevant fields from these records. It then converts the data into a DataFrame.
    Returns:
      pandas.DataFrame: A DataFrame containing the relevant product metadata fields.
    """

    headers = {
        'Authorization': f'Bearer {AIRTABLE_API_KEY}'
    }
    params = {
        'view': 'Data for PO Builder',
        'fields[]': [
            'SKU', 
            'Product Number',
            'Product Name', 
            'Option1 Value', 
            'Position',
            'Supplier (Plain Text)', 
            'Status Shopify (Shopify)',
            'Stocked Status',
            'Decoration Group (Plain Text)',
            'Artwork (Title)',
            'Cost-Production: Total', 
            'Category', 
            'Subcategory', 
            'Product Type (Internal)',
            'Component Brand',
            'Component Style Number',
            'Component Style Name',
            'Component Color',
            'Blank Preferred Supplier',
            'Blank Backup Supplier(s)'
        ]
    }
    
    all_records = []
    offset = None

    while True:
        if offset:
            params['offset'] = offset
        encoded_params = urlencode(params, doseq=True)
        url = f"{AIRTABLE_VARIANTS_ENDPOINT}?{encoded_params}"
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            records = data.get('records', [])
            all_records.extend([record['fields'] for record in records])
            offset = data.get('offset')
            if not offset:
                break
        else:
            print(f"Failed to fetch data: {response.status_code}")
            print("Response Content:", response.content)
            return None

    return all_records
