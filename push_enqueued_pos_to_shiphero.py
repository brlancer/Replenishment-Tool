import requests
from pyairtable import Table
import config
import json

def fetch_purchase_orders_to_sync(purchase_orders_table):
    """Fetch purchase orders with ShipHero Sync Status = 'Queued'."""
    print("Fetching purchase orders to sync...")
    records = purchase_orders_table.all(formula="{ShipHero Sync Status} = 'Queued'")
    print(f"Fetched {len(records)} purchase orders to sync.")
    return records

def fetch_line_items_for_po(line_items_table, po_number):
    """Fetch line items for a given purchase order number."""
    print(f"Fetching line items for purchase order number: {po_number}...")
    records = line_items_table.all(formula=f"AND({{PO #}} = '{po_number}', {{ShipHero Sync Status}} = 'Queued')")
    print(f"Fetched {len(records)} line items for purchase order number: {po_number}.")
    return records

def prepare_graphql_query(po_record, line_items):
    """Prepare the GraphQL query for the purchase_order_create mutation."""
    po_number = po_record['fields']['PO #']
    vendor_id = po_record['fields']['ShipHero Vendor ID'][0]
    warehouse_id = config.SHIPHERO_WAREHOUSE_ID

    line_items_data = [
        {
            "sku": item['fields']['sku'],
            "quantity": item['fields']['Quantity Ordered'],
            "price": f"{item['fields']['Total Unit Cost (active)']:.2f}",
            "expected_weight_in_lbs": "0.0" # Placeholder for now
        }
        for item in line_items
    ]

    # Calculate subtotal as the sum of (quantity * price) for all line items
    subtotal = sum([float(item['quantity']) * float(item['price']) for item in line_items_data])

    # Convert line_items_data to a JSON string
    line_items_json = json.dumps(line_items_data)

    # Remove quotes around keys in the JSON string
    line_items_json = line_items_json.replace('"sku"', 'sku').replace('"quantity"', 'quantity').replace('"price"', 'price').replace('"expected_weight_in_lbs"', 'expected_weight_in_lbs')

    query = {
        "query": f"""
        mutation {{
            purchase_order_create(
                data: {{
                    po_number: "{po_number}",
                    vendor_id: "{vendor_id}",
                    warehouse_id: "{warehouse_id}",
                    subtotal: "{subtotal:.2f}",
                    shipping_price: "0.00",
                    total_price: "{subtotal:.2f}",
                    line_items: {line_items_json}
                }}
            ) {{
                request_id
                complexity
                purchase_order {{
                    id
                }}
            }}
        }}
        """
    }

    return query

def execute_graphql_query(query):
    """Execute the GraphQL query and return the response."""
    url = "https://public-api.shiphero.com/graphql"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.SHIPHERO_API_TOKEN}"
    }
    print("Executing GraphQL query:")
    print(query)
    response = requests.post(url, json=query, headers=headers)
    print("Response status code:", response.status_code)
    print("Response content:", response.content)
    response.raise_for_status()
    return response.json()

def update_airtable_status(purchase_orders_table, po_id, status):
    """Update the ShipHero Sync Status field in Airtable."""
    print(f"Updating ShipHero Sync Status for purchase order ID: {po_id} to {status}...")
    purchase_orders_table.update(po_id, {"ShipHero Sync Status": status})
    print(f"Updated ShipHero Sync Status for purchase order ID: {po_id}.")

def push_enqueued_pos_to_shiphero():
    # Initialize Airtable tables
    print("Initializing Airtable tables...")
    purchase_orders_table = Table(config.AIRTABLE_API_KEY, config.AIRTABLE_PRODUCTION_DEV_BASE_ID, "Purchase Orders")
    line_items_table = Table(config.AIRTABLE_API_KEY, config.AIRTABLE_PRODUCTION_DEV_BASE_ID, "Line Items")

    # Fetch purchase orders to sync
    purchase_orders = fetch_purchase_orders_to_sync(purchase_orders_table)

    for po_record in purchase_orders:
        po_id = po_record['id']
        po_number = po_record['fields']['PO #']

        # Fetch line items for the purchase order
        line_items = fetch_line_items_for_po(line_items_table, po_number)

        # Prepare the GraphQL query
        query = prepare_graphql_query(po_record, line_items)

        try:
            # Execute the GraphQL query
            response = execute_graphql_query(query)
            print(f"Successfully synced purchase order: {po_number} to ShipHero.")
            print(response)

            # Update Airtable status to "Synced"
            update_airtable_status(purchase_orders_table, po_id, "Synced")
        except requests.exceptions.RequestException as e:
            print(f"Failed to sync purchase order: {po_number} to ShipHero. Error: {e}")
            # Update Airtable status to "Failed"
            update_airtable_status(purchase_orders_table, po_id, "Failed")

# Test the function
if __name__ == "__main__":
    push_enqueued_pos_to_shiphero()