import os
from pathlib import Path
from src.config import BRONZE_DIR, SILVER_DIR
from src.ingestion.csv_parser import parse_csv
from src.processing.silver_layer import save_to_silver

def process_bronze_layer():
    bronze_path = Path(BRONZE_DIR)
    
    if not bronze_path.exists():
        print(f"Bronze directory not found: {bronze_path}")
        return

    for csv_file in bronze_path.glob("*.csv"):
        print(f"Processing file: {csv_file.name}")
        df = parse_csv(csv_file)
        if df is not None:
            save_to_silver(df, csv_file.name, SILVER_DIR)

    # TODO: Add logic for OFX and PDF processing later
    print("Successfully processed all CSV files in the Bronze layer.")

if __name__ == "__main__":
    process_bronze_layer()
