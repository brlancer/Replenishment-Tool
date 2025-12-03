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

    if use_cache and os.path.exists(CACHE_FILE):
        print("Loading cached sales data...")
        with open(CACHE_FILE, 'rb') as f:
          return pickle.load(f)
        
    print("Fetching fresh sales data from Shopify...")

    # Calculate the date 53 weeks before today (52 complete weeks + 1 week buffer)
    fifty_three_weeks_ago = datetime.now() - timedelta(weeks=53)
    formatted_date = fifty_three_weeks_ago.strftime("%Y-%m-%d")
    
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

    # Save the fetched data to cache
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
