import requests, time, json, os
from urllib.parse import urlencode
from config import AIRTABLE_API_KEY, AIRTABLE_VARIANTS_ENDPOINT, AIRTABLE_PRODUCTION_DEV_BASE_ID, SHIPHERO_API_TOKEN, SHIPHERO_REFRESH_TOKEN, SHIPHERO_REFRESH_ENDPOINT, SHIPHERO_GRAPHQL_ENDPOINT, SHOPIFY_API_TOKEN, SHOPIFY_GRAPHQL_ENDPOINT
import pandas as pd
from pyairtable import Table
from datetime import datetime, timedelta
from utils import fetch_shiphero_paginated_data, fetch_shopify_bulk_operation

# Airtable functions

def fetch_airtable_incoming_stock():
    print("Initializing Airtable table...")
    line_items_table = Table(AIRTABLE_API_KEY, AIRTABLE_PRODUCTION_DEV_BASE_ID, "Line Items")

    print("Fetching records with PO Status = 'Open'...")
    records = line_items_table.all(formula="{PO Status} = 'Open'", fields=['Position - PO # - SKU', 'sku', 'Quantity Ordered', 'Quantity Received (ShipHero)'])
    print(f"Fetched {len(records)} records.")
    print("First 5 records:")
    for record in records[:5]:
        print(record)

    print("Extracting relevant fields...")
    data = []
    for record in records:
        fields = record['fields']
        data.append({
            'Position - PO # - SKU': fields.get('Position - PO # - SKU', ''),
            'sku': fields.get('sku', ''),
            'ordered': fields.get('ordered', 0),
            'received': fields.get('received', 0)
        })
    print(f"Extracted data for {len(data)} records.")

    print("Converting data to DataFrame...")
    df = pd.DataFrame(data)
    print("DataFrame created:")
    print(df.head())

    print("Calculating 'pending' field...")
    df['incoming'] = df['ordered'] - df['received']
    print("Calculated 'pending' field:")
    print(df.head())

    print("Grouping by 'sku' and summing 'incoming'...")
    grouped_df = df.groupby('sku')['incoming'].sum().reset_index()
    print("Grouped DataFrame:")
    print(grouped_df.head())

    return grouped_df

def fetch_airtable_product_metadata():
    headers = {
        'Authorization': f'Bearer {AIRTABLE_API_KEY}'
    }
    params = {
        'view': 'Data for PO Builder',
        'fields[]': [
            'SKU', 
            'product_num',
            'Product Name', 
            'Option1 Value', 
            'Position',
            'Supplier Name - ShipHero', 
            'Status Shopify (Shopify)',
            'Decoration Group (Plain Text)',
            'Artwork (Title)',
            'Cost-Production: Total', 
            'Category', 
            'Subcategory', 
            'Product Type (Internal)'
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

# Shiphero functions

def fetch_shiphero_stock_levels():
    query = """
    query ($first: Int!, $after: String) {
      warehouse_products(warehouse_id: "V2FyZWhvdXNlOjEwMTU4Mw==", active: true) { 
        complexity 
        request_id 
        data(first: $first, after: $after) { 
          pageInfo {
            hasNextPage
            endCursor
          }
          edges { 
            node { 
              id 
              sku
              on_hand
              allocated
              available
              backorder
            }
          }
        }
      }
    }
    """
    
    variables = {
        "first": 100,
        "after": None
    }
    
    stock_levels = fetch_shiphero_paginated_data(query, variables, "warehouse_products")
    return stock_levels

def fetch_shiphero_incoming_stock():  # Not currently functional
    query = """
    query ($first: Int!, $after: String) {
      purchase_orders(warehouse_id: "V2FyZWhvdXNlOjEwMTU4Mw==", fulfillment_status: "Pending") { 
        complexity 
        request_id 
        data(first: $first, after: $after) { 
          pageInfo {
            hasNextPage
            endCursor
          }
          edges { 
            node { 
              id 
              po_number
              created_at
              po_date
              fulfillment_status
              line_items {
                edges {
                  node {
                    id
                    sku
                    quantity
                    quantity_received
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    
    variables = {
        "first": 5,
        "after": None
    }
    
    purchase_orders_data = fetch_shiphero_paginated_data(query, variables, "purchase_orders")
    
    if purchase_orders_data:
        incoming_stock = {}
        
        for order in purchase_orders_data:
            for item in order["node"]["line_items"]["edges"]:
                sku = item["node"]["sku"]
                quantity = item["node"]["quantity"]
                if sku in incoming_stock:
                    incoming_stock[sku] += quantity
                else:
                    incoming_stock[sku] = quantity
        
        return incoming_stock
    else:
        return None

# Shopify functions

def fetch_shopify_sales_data():
    # Calculate the date 9 weeks before today
    nine_weeks_ago = datetime.now() - timedelta(weeks=9)
    formatted_date = nine_weeks_ago.strftime("%Y-%m-%d")
    
    inner_query = f"""
    {{
      orders(query: "created_at:>={formatted_date} AND (fulfillment_status:shipped OR fulfillment_status:unfulfilled OR fulfillment_status:partial) AND (financial_status:paid OR financial_status:pending) AND -tag:'Exclude from Forecast'") {{
        edges {{
          node {{
            id
            name
            createdAt
            tags
            displayFulfillmentStatus
            displayFinancialStatus
            cancelledAt
            lineItems(first: 100) {{
              edges {{
                node {{
                  id
                  sku
                  variantTitle
                  quantity
                  unfulfilledQuantity
                }}
              }}
            }}
          }}
        }}
      }}
    }}
    """
    
    sales_data = fetch_shopify_bulk_operation(inner_query)
    return sales_data