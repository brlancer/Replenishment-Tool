import requests
import os
import time
from datetime import datetime, timedelta
from config import SHIPHERO_API_TOKEN, SHIPHERO_REFRESH_TOKEN, SHIPHERO_REFRESH_ENDPOINT, SHIPHERO_GRAPHQL_ENDPOINT, SHIPHERO_TOKEN_EXPIRATION


def refresh_shiphero_token():
    """Refresh the ShipHero API token using the refresh token."""
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "refresh_token": SHIPHERO_REFRESH_TOKEN
    }
    response = requests.post(SHIPHERO_REFRESH_ENDPOINT, json=data, headers=headers)
    if response.status_code == 200:
        response_data = response.json()
        new_token = response_data.get("access_token")
        expires_in = response_data.get("expires_in")  # Assuming the API returns the expiration time in seconds
        if new_token and expires_in:
            expiration_time = datetime.now() + timedelta(seconds=expires_in)
            print("ShipHero API token refreshed successfully.")
            update_config_file_with_new_shiphero_token(new_token, expiration_time)
            return new_token, expiration_time
    print("Failed to refresh ShipHero API token.")
    return None, None

def update_config_file_with_new_shiphero_token(new_token, expiration_time):
    """Update the config.py file with a new ShipHero API token."""
    config_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.py'))
    with open(config_file_path, 'r') as file:
        lines = file.readlines()
    
    with open(config_file_path, 'w') as file:
        for line in lines:
            if line.startswith('SHIPHERO_API_TOKEN'):
                file.write(f'SHIPHERO_API_TOKEN = "{new_token}"\n')
            elif line.startswith('SHIPHERO_TOKEN_EXPIRATION'):
                file.write(f'SHIPHERO_TOKEN_EXPIRATION = "{expiration_time.isoformat()}"\n')
            else:
                file.write(line)

def is_token_expired():
    """Check if the ShipHero API token has expired."""
    expiration_time = datetime.fromisoformat(SHIPHERO_TOKEN_EXPIRATION)
    return datetime.now() >= expiration_time

def fetch_shiphero_with_throttling(query, variables):
    """Fetch data from ShipHero with automatic token refresh and throttle handling."""
    global SHIPHERO_API_TOKEN, SHIPHERO_TOKEN_EXPIRATION

    if is_token_expired():
        print("Token is expired. Refreshing token...")
        new_token, new_expiration = refresh_shiphero_token()
        if not new_token:
            raise Exception("Failed to refresh ShipHero API token.")
        SHIPHERO_API_TOKEN = new_token
        SHIPHERO_TOKEN_EXPIRATION = new_expiration.isoformat()
    
    headers = {
        "Authorization": f"Bearer {SHIPHERO_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    while True:
        response = requests.post(SHIPHERO_GRAPHQL_ENDPOINT, json={"query": query, "variables": variables}, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            # Print the result for debugging purposes
            print(result)
            
            if "errors" in result:
                error = result["errors"][0]
                if error["code"] == 30:
                    wait_time_str = error["time_remaining"]
                    wait_time = int(wait_time_str.split()[0])
                    print(f"Throttling detected. Waiting for {wait_time} seconds before retrying...")
                    time.sleep(wait_time)
                    continue
            return result
        else:
            print("Failed to fetch data")
            print(response.text)
            raise Exception("Failed to fetch data from ShipHero API")

def fetch_shiphero_paginated_data(query, variables, data_key):
    """Fetch paginated data from ShipHero GraphQL API."""
    data_list = []
    has_next_page = True
    after_cursor = None

    while has_next_page:
        variables["after"] = after_cursor
        # print(f"Sending request with variables: {variables}")
        result = fetch_shiphero_with_throttling(query, variables)
        
        if result:
            data = result.get("data", {}).get(data_key, {}).get("data", {})
            if data and "edges" in data:
                data_list.extend(data["edges"])
                page_info = result.get("data", {}).get(data_key, {}).get("data", {}).get("pageInfo")
                if page_info:
                    has_next_page = page_info.get("hasNextPage", False)
                    after_cursor = page_info.get("endCursor")
                else:
                    print("No 'pageInfo' found in the response")
                    print("Response data:", result)
                    has_next_page = False
            else:
                print("No data found in the response or 'edges' key is missing")
                print("Response data:", result)
                has_next_page = False
        else:
            print("Failed to fetch data")
            has_next_page = False

    return data_list

def execute_shiphero_graphql_query(query):
    """Execute a GraphQL query against ShipHero and return the response."""
    url = "https://public-api.shiphero.com/graphql"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SHIPHERO_API_TOKEN}"
    }
    print("Executing GraphQL query:")
    print(query)
    response = requests.post(url, json=query, headers=headers)
    print("Response status code:", response.status_code)
    print("Response content:", response.content)
    response.raise_for_status()
    return response.json()
