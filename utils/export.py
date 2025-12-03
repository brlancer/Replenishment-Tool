import os
import json
from datetime import datetime


def export_df(df, label):
    """Export a pandas DataFrame to a CSV file with timestamp."""
    timestamp = datetime.now().strftime("%Y-%d-%m %H-%M-%S")
    output_dir = "output"
    output_path = os.path.join(output_dir, f"{label}_{timestamp}.csv")
    
    # Check if the directory exists and create it if not
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print(f"{label}:")
    print(df)
    
    df.to_csv(output_path, index=False)
    print(f"{label} saved to {output_path}")

def export_json(data, label):
    """Export data as JSON to a file with timestamp."""
    timestamp = datetime.now().strftime("%Y-%d-%m %H-%M-%S")
    output_dir = "output"
    output_path = os.path.join(output_dir, f"{label}_{timestamp}.json")
    
    # Check if the directory exists and create it if not
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print(f"{label}:")
    print(data)
    
    with open(output_path, 'w') as file:
        json.dump(data, file, indent=4)
    
    print(f"{label} saved to {output_path}")
