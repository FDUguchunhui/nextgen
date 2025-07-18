#!/usr/bin/env python3
"""
Script to read protein_level_Citrullination.csv and add a measurement table
to the existing SQLite database test.db.
"""

import sqlite3
import csv
import sys
from typing import List, Dict

def get_column_names(csv_file: str) -> List[str]:
    """Extract column names from the first line of the CSV file."""
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        return next(reader)

def create_measurement_table_schema(columns: List[str]) -> str:
    """Create the SQL CREATE TABLE statement for measurement table."""
    # Clean column names - replace spaces and special characters, and convert to lowercase
    clean_columns = []
    for col in columns:
        # Replace problematic characters and convert to lowercase
        clean_col = col.replace(' ', '_').replace('(', '').replace(')', '').replace('[', '').replace(']', '').replace('-', '_').replace('.', '_').lower()
        # Remove multiple underscores
        clean_col = '_'.join(filter(None, clean_col.split('_')))
        clean_columns.append(clean_col)
    
    # Define column types based on the data structure (using lowercase names)
    sql_columns = []
    for i, col in enumerate(clean_columns):
        if col == 'protein_group':
            sql_columns.append(f'"{col}" TEXT')
        elif col == 'protein_ids':
            sql_columns.append(f'"{col}" TEXT')
        elif col == 'genes':
            sql_columns.append(f'"{col}" TEXT')
        elif col == 'citrullination_r':
            sql_columns.append(f'"{col}" BOOLEAN')
        elif col == 'run':
            sql_columns.append(f'"{col}" TEXT')
        elif col == 'intensity':
            sql_columns.append(f'"{col}" REAL')
        else:
            sql_columns.append(f'"{col}" TEXT')
    
    return f"CREATE TABLE measurement (\n    {',\n    '.join(sql_columns)}\n)"

def validate_data(csv_file: str) -> bool:
    """Basic validation of CSV data structure."""
    print("Validating CSV data structure...")
    
    row_count = 0
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)  # Skip header
        
        for row in reader:
            row_count += 1
            # Basic validation - ensure row has expected number of columns
            if len(row) != len(headers):
                print(f"Warning: Row {row_count} has {len(row)} columns, expected {len(headers)}")
    
    print(f"Processed {row_count} rows from CSV")
    return True

def add_measurement_table(db_file: str, csv_file: str):
    """Main function to add the measurement table."""

    
    
    print("Reading column names from CSV file...")
    columns = get_column_names(csv_file)
    print(f"Found {len(columns)} columns: {columns}")
    
    # Create database schema
    create_table_sql = create_measurement_table_schema(columns)
    print(f"CREATE TABLE SQL:\n{create_table_sql}")
    
    # Clean column names for insertion
    clean_columns = []
    for col in columns:
        clean_col = col.replace(' ', '_').replace('(', '').replace(')', '').replace('[', '').replace(']', '').replace('-', '_').replace('.', '_').lower()
        clean_col = '_'.join(filter(None, clean_col.split('_')))
        clean_columns.append(clean_col)
    
    print("Connecting to existing SQLite database...")
    
    # Connect to existing database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Validate data before proceeding
    if not validate_data(csv_file):
        print("\nCSV data validation failed!")
        print("Please fix the data or modify the validation logic.")
        conn.close()
        return False
    
    print("CSV data validation passed!")
    
    # Check if measurement table already exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='measurement'")
    if cursor.fetchone():
        print("Table 'measurement' already exists. Dropping it...")
        cursor.execute("DROP TABLE measurement")
    
    # Create table
    cursor.execute(create_table_sql)
    print("Table 'measurement' created successfully")
    
    # Prepare insert statement
    placeholders = ','.join(['?' for _ in columns])
    column_list = ",".join([f'"{col}"' for col in clean_columns])
    insert_sql = f'INSERT INTO measurement ({column_list}) VALUES ({placeholders})'
    print(f"Insert SQL: {insert_sql}")
    
    print("Reading and inserting data...")
    
    # Read and insert data
    inserted_count = 0
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            
            batch_size = 1000
            batch = []
            
            for row_num, row in enumerate(reader, 1):
                # Pad row with empty strings if needed
                while len(row) < len(columns):
                    row.append('')
                
                # Truncate row if too long
                row = row[:len(columns)]
                
                # Convert data types
                processed_row = []
                for i, value in enumerate(row):
                    if clean_columns[i] == 'citrullination_r':
                        # Convert TRUE/FALSE to boolean
                        processed_row.append(value.upper() == 'TRUE' if value else False)
                    elif clean_columns[i] == 'intensity':
                        # Convert to float
                        try:
                            processed_row.append(float(value) if value else None)
                        except ValueError:
                            processed_row.append(None)
                    else:
                        processed_row.append(value)
                
                batch.append(processed_row)
                
                if len(batch) >= batch_size:
                    cursor.executemany(insert_sql, batch)
                    inserted_count += len(batch)
                    batch = []
                    print(f"Inserted {inserted_count} rows...")
            
            # Insert remaining rows
            if batch:
                cursor.executemany(insert_sql, batch)
                inserted_count += len(batch)
                print(f"Inserted {inserted_count} rows...")
    
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return False
    
    # Commit changes
    conn.commit()
    
    # Verify the data
    cursor.execute("SELECT COUNT(*) FROM measurement")
    count = cursor.fetchone()[0]
    print(f"Total records in measurement table: {count}")
    
    # Show a sample record
    cursor.execute("SELECT protein_group, genes, citrullination_r, run, intensity FROM measurement LIMIT 1")
    sample = cursor.fetchone()
    if sample:
        print(f"Sample record: {sample}")
    
    # Show table schema
    cursor.execute("PRAGMA table_info(measurement)")
    schema = cursor.fetchall()
    print("Table schema:")
    for col in schema:
        print(f"  {col}")
    
    conn.close()
    print(f"Measurement table added to database '{db_file}' successfully!")
    return True

if __name__ == "__main__":
    add_measurement_table('database/nextgen.db', 'data/protein_level_Citrullination_expanded.csv') 