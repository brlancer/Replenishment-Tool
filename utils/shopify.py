import requests
import time
import json
from config import SHOPIFY_API_TOKEN, SHOPIFY_GRAPHQL_ENDPOINT


def start_bulk_operation(inner_query):
    """Start a Shopify bulk operation with the given query."""
    mutation = f"""
    mutation {{
      bulkOperationRunQuery(
        query: \"\"\"
        {inner_query}
        \"\"\"
      ) {{
        bulkOperation {{
          id
          status
        }}
        userErrors {{
          field
          message
        }}
      }}
    }}
    """
    
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_API_TOKEN,
        "Content-Type": "application/json"
    }
    
    response = requests.post(SHOPIFY_GRAPHQL_ENDPOINT, json={"query": mutation}, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(response.text)
        return result
    else:
        print("Failed to start bulk operation")
        print(response.text)
        return None

def check_bulk_operation_status():
    """Check the status of the current Shopify bulk operation."""
    query = """
    {
      currentBulkOperation {
        id
        status
        errorCode
        createdAt
        completedAt
        objectCount
        fileSize
        url
      }
    }
    """
    
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_API_TOKEN,
        "Content-Type": "application/json"
    }
    
    response = requests.post(SHOPIFY_GRAPHQL_ENDPOINT, json={"query": query}, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        return result
    else:
        print("Failed to check bulk operation status")
        print(response.text)
        return None

def download_bulk_operation_results(url):
    """Download the results of a completed Shopify bulk operation."""
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.text.splitlines()
        return [json.loads(line) for line in data]
    else:
        print("Failed to download bulk operation results")
        print(response.text)
        return None

def fetch_shopify_bulk_operation(inner_query):
    """Execute a Shopify bulk operation and return the results."""
    start_result = start_bulk_operation(inner_query)
    if not start_result:
        return None
    
    while True:
        status_result = check_bulk_operation_status()
        if not status_result:
            return None
        
        bulk_operation = status_result.get("data", {}).get("currentBulkOperation")
        if not bulk_operation:
            print("No current bulk operation found")
            return None
        
        status = bulk_operation.get("status")
        
        if status == "COMPLETED":
            print("Bulk operation completed")
            url = bulk_operation.get("url")
            return download_bulk_operation_results(url)
        elif status == "FAILED":
            print("Bulk operation failed")
            return None
        else:
            print(f"Bulk operation status: {status}")
            time.sleep(3)
