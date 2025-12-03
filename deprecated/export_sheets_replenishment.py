import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import re

# Define the scope
SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']

# Path to your service account key file
SERVICE_ACCOUNT_FILE = 'service-account.json'  # Update this path

# Authenticate and create the service
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(credentials)

def export_sheets_replenishment(replenishment_df):
    file_id = '1L35Drb5FZfPsV7kk73wZzsqCQ9k6x7KSoKJMYFhefeQ'  # Google Drive file name: PO BUILDER 3.0

    # Open the template file with gspread
    sh = gc.open_by_key(file_id)

    # Get the "Data" worksheet
    worksheet_data = sh.worksheet("Data - Replenishment")

    # Clear the existing content in the "Replenishment" tab
    worksheet_data.clear()

    # Add a blank row in replenishment_df between each product_num
    replenishment_df = pd.concat(
        [replenishment_df.iloc[[i]] if i == 0 or replenishment_df.iloc[i]['product_num'] == replenishment_df.iloc[i-1]['product_num'] else pd.concat([pd.DataFrame([[''] * len(replenishment_df.columns)], columns=replenishment_df.columns), replenishment_df.iloc[[i]]]) for i in range(len(replenishment_df))]
    ).reset_index(drop=True)

    # Replace NaN and Infinity values with an empty string
    replenishment_df = replenishment_df.replace([pd.NA, pd.NaT, float('inf'), float('-inf')], '')

    # Ensure all values are strings to avoid JSON serialization issues
    replenishment_df = replenishment_df.astype(str)

    # Replace all "nan" values with an empty string
    replenishment_df = replenishment_df.replace("nan", "")

    # Debugging: Print the DataFrame to verify its contents
    print("DataFrame to be written to Google Sheet:")
    print(replenishment_df)

    # Write the DataFrame to the "Replenishment" tab
    worksheet_data.update([replenishment_df.columns.values.tolist()] + replenishment_df.values.tolist())

    print("Replenishment data exported to Google Sheet")

    # Get the Replenishment worksheet
    worksheet_replenishment = sh.worksheet("Replenishment")

    # Find the column labeled "To Order Qty"
    to_order_qty_cell = worksheet_replenishment.find("To Order Qty")
    # Extract column from the cell address with a regular expression (e.g., "A1" -> "A")
    to_order_qty_col = re.search(r"([A-Z]+)", to_order_qty_cell.address).group(1)

    print(f"Found 'To Order Qty' at column {to_order_qty_col}")

    print(f"Clearing all data from {to_order_qty_col}2:{to_order_qty_col}")

    # Clear all data from the "To Order Qty" column 
    worksheet_replenishment.batch_clear([f"{to_order_qty_col}2:{to_order_qty_col}"])

# Test the function
if __name__ == "__main__":
    # Load the CSV file for testing
    replenishment_df = pd.read_csv("output/replenishment_2025-01-24 06-37-28.csv")
    
    # Debugging: Print the DataFrame to verify its contents
    print("Loaded DataFrame from CSV:")
    print(replenishment_df)

    export_sheets_replenishment(replenishment_df)