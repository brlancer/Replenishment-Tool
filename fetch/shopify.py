import os
import pickle
from datetime import datetime, timedelta
from utils import fetch_shopify_bulk_operation


def fetch_shopify_sales_data(use_cache=False):
    """
    Fetches sales data from Shopify and processes it into a list of dictionaries.
    This function retrieves sales data from the Shopify GraphQL API and paginates
    through the results to fetch all available data. It then processes the data into
    a list of dictionaries, where each dictionary represents an order or a line item
    within an order and contains relevant fields.
    Returns:
      list: A list of dictionaries containing the sales data for each order and line item.
    """
    
    CACHE_FILE = 'cache/shopify_sales_data.pkl'
    cached_data = []
    most_recent_order_date = None

    # Load cached data if it exists and use_cache is True
    if use_cache and os.path.exists(CACHE_FILE):
        print("Loading cached sales data...")
        with open(CACHE_FILE, 'rb') as f:
            cached_data = pickle.load(f)
        
        # Find the most recent order date in the cache
        order_dates = [
            datetime.strptime(item['createdAt'], "%Y-%m-%dT%H:%M:%SZ")
            for item in cached_data
            if '__parentId' not in item and 'createdAt' in item
        ]
        if order_dates:
            most_recent_order_date = max(order_dates)
            print(f"Most recent cached order: {most_recent_order_date.strftime('%Y-%m-%d %H:%M:%S')}")

    # Determine the start date for fetching new orders
    if most_recent_order_date:
        # Fetch orders created after the most recent cached order
        start_date = most_recent_order_date.strftime("%Y-%m-%d")
        print(f"Fetching new orders since {start_date}...")
    else:
        # If no cache, fetch the past 53 weeks
        fifty_three_weeks_ago = datetime.now() - timedelta(weeks=53)
        start_date = fifty_three_weeks_ago.strftime("%Y-%m-%d")
        print("Fetching fresh sales data from Shopify (past 53 weeks)...")

    inner_query = f"""
    {{
      orders(query: "created_at:>={start_date} AND (fulfillment_status:shipped OR fulfillment_status:unfulfilled OR fulfillment_status:partial) AND (financial_status:paid OR financial_status:pending) AND -tag:'Exclude from Forecast'") {{
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
    
    new_data = fetch_shopify_bulk_operation(inner_query)
    
    # Merge new data with cached data, removing duplicates by order ID
    if cached_data and new_data:
        # Get set of order IDs from new data (orders are items without __parentId)
        new_order_ids = {item['id'] for item in new_data if '__parentId' not in item}
        
        # Keep cached items that are not in the new data (avoid duplicates)
        deduplicated_cache = [item for item in cached_data if item.get('id') not in new_order_ids]
        
        # Combine deduplicated cache with new data
        sales_data = deduplicated_cache + new_data
        print(f"Merged {len(new_data)} new items with {len(deduplicated_cache)} cached items")
    else:
        sales_data = new_data if new_data else cached_data

    # Save the merged data to cache
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, 'wb') as f:
        pickle.dump(sales_data, f)

    return sales_data

def fetch_shopify_inventory_data(use_cache=False):
    """
    Fetches inventory data from Shopify and processes it into a pandas DataFrame.
    This function retrieves inventory data from the Shopify GraphQL API and processes
    it into a pandas DataFrame. It fetches data for products and their variants, including
    inventory levels at different locations. It then processes the data into a DataFrame
    with columns for product ID, product title, variant ID, variant title, SKU, location ID,
    location name, and inventory quantities (available, incoming, committed, on hand).
    Returns:
      pandas.DataFrame: A DataFrame containing the inventory data for products and variants.
    """
    
    CACHE_FILE = 'cache/shopify_inventory_data.pkl'

    if use_cache and os.path.exists(CACHE_FILE):
        print("Loading cached inventory data...")
        with open(CACHE_FILE, 'rb') as f:
          return pickle.load(f)
        
    print("Fetching fresh inventory data from Shopify...")

    query = """
    query GetCommittedInventory {
      products(first:50, query: "status:ACTIVE") {
        edges {
          node {
            id
            title
            variants(first:50) {
              edges {
                node {
                  id
                  title
                  sku
                  inventoryItem {
                    id
                    inventoryLevels(first: 10) {
                      edges {
                        node {
                          location {
                            id
                            name
                          }
                          quantities(names: ["available","incoming","committed","on_hand"]) {
                            name
                            quantity
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    
    inventory_data = fetch_shopify_bulk_operation(query)

    # Save the fetched data to cache
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, 'wb') as f:
      pickle.dump(inventory_data, f)

    return inventory_data
