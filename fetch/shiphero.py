import os
import pickle
from config import SHIPHERO_WAREHOUSE_ID
from datetime import datetime
from utils import fetch_shiphero_paginated_data


def fetch_shiphero_stock_levels(use_cache=False):
    """
    Fetches stock levels data from ShipHero and processes it into a list of dictionaries.
    This function retrieves stock levels data from the ShipHero GraphQL API and paginates
    through the results to fetch all available data. It then processes the data into a list
    of dictionaries, where each dictionary represents a product and contains relevant fields.
    Returns:
      list: A list of dictionaries containing the stock levels data for each product.
    """
    
    CACHE_FILE = 'cache/shiphero_stock_levels.pkl'

    if use_cache and os.path.exists(CACHE_FILE):
        print("Loading cached stock levels data...")
        with open(CACHE_FILE, 'rb') as f:
          return pickle.load(f)
        
    print("Fetching fresh stock levels data from ShipHero...")

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

    # Save the fetched data to cache
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, 'wb') as f:
      pickle.dump(stock_levels, f)
        
    return stock_levels

def fetch_purchase_orders_from_shiphero(created_from: str = None):
  """Fetch active purchase orders from ShipHero."""
  
  if not created_from:
    raise ValueError("The 'created_from' parameter is required.")
  
  # Convert created_from to ISODateTime format
  try:
    created_from_iso = datetime.strptime(created_from, "%Y-%m-%d").isoformat()
    created_from = created_from_iso + "Z"
  except ValueError as e:
    raise ValueError(f"Invalid date format for 'created_from': {created_from}. Expected format: YYYY-MM-DD") from e

  query = """
  query ($first: Int!, $after: String, $created_from: ISODateTime, $warehouse_id: String){
    purchase_orders(created_from: $created_from, warehouse_id: $warehouse_id) {
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
    "first": 10,
    "after": None,
    "created_from": created_from,
    "warehouse_id": SHIPHERO_WAREHOUSE_ID
  }

  # print the query and variables
  print(query)
  print(variables)
  purchase_orders = fetch_shiphero_paginated_data(query, variables, "purchase_orders")
  
  return purchase_orders
