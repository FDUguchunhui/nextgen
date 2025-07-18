#!/usr/bin/env python3
"""
Script to read metadata.csv and add a sample table
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

def create_sample_table_schema(columns: List[str]) -> str:
    """Create the SQL CREATE TABLE statement for sample table."""
    # Clean column names - replace spaces and special characters, and convert to lowercase
    clean_columns = []
    for col in columns:
        # Replace problematic characters and convert to lowercase
        clean_col = col.replace(' ', '_').replace('(', '').replace(')', '').replace('[', '').replace(']', '').replace('-', '_').replace('.', '_').replace(';', '_').lower()
        # Remove multiple underscores
        clean_col = '_'.join(filter(None, clean_col.split('_')))
        clean_columns.append(clean_col)
    
    # Define column types based on the data structure (using lowercase names)
    sql_columns = []
    for i, col in enumerate(clean_columns):
        if col == 'run':
            # Primary key
            sql_columns.append(f'"{col}" TEXT PRIMARY KEY')
        elif col in ['is_case', 'check']:
            # Boolean columns
            sql_columns.append(f'"{col}" BOOLEAN')
        elif col in ['sex_1_male_0_female', 'age']:
            # Numeric columns
            sql_columns.append(f'"{col}" INTEGER')
        else:
            # All other columns as TEXT
            sql_columns.append(f'"{col}" TEXT')
    
    return f"CREATE TABLE sample (\n    {',\n    '.join(sql_columns)}\n)"

def add_sample_table(db_file: str, csv_file: str):
    """Main function to add the sample table."""
    
    print("Reading column names from CSV file...")
    columns = get_column_names(csv_file)
    print(f"Found {len(columns)} columns: {columns}")
    
    # Create database schema
    create_table_sql = create_sample_table_schema(columns)
    print(f"CREATE TABLE SQL:\n{create_table_sql}")
    
    # Clean column names for insertion
    clean_columns = []
    for col in columns:
        clean_col = col.replace(' ', '_').replace('(', '').replace(')', '').replace('[', '').replace(']', '').replace('-', '_').replace('.', '_').replace(';', '_').lower()
        clean_col = '_'.join(filter(None, clean_col.split('_')))
        clean_columns.append(clean_col)
    
    print("Connecting to existing SQLite database...")
    
    # Connect to existing database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Enable foreign key constraints (disabled by default in SQLite)
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Check if sample table already exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sample'")
    if cursor.fetchone():
        print("Table 'sample' already exists. Dropping it...")
        cursor.execute("DROP TABLE sample")
    
    # Create table
    cursor.execute(create_table_sql)
    print("Table 'sample' created successfully")
    
    # Prepare insert statement
    placeholders = ','.join(['?' for _ in columns])
    column_list = ",".join([f'"{col}"' for col in clean_columns])
    insert_sql = f'INSERT INTO sample ({column_list}) VALUES ({placeholders})'
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
                    if clean_columns[i] in ['is_case', 'check']:
                        # Convert to boolean - handle various formats
                        if value.upper() in ['TRUE', '1']:
                            processed_row.append(True)
                        elif value.upper() in ['FALSE', '0']:
                            processed_row.append(False)
                        else:
                            processed_row.append(None)
                    elif clean_columns[i] in ['sex_1_male_0_female', 'age']:
                        # Convert to integer
                        try:
                            processed_row.append(int(float(value)) if value and value != 'NA' and value != '-' else None)
                        except ValueError:
                            processed_row.append(None)
                    else:
                        # Keep as text, but handle NA/NULL values
                        processed_row.append(value if value and value != 'NA' else None)
                
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
    cursor.execute("SELECT COUNT(*) FROM sample")
    count = cursor.fetchone()[0]
    print(f"Total records in sample table: {count}")
    
    # Show a sample record
    cursor.execute('SELECT run, ipas, is_case, sex_1_male_0_female, cancer_type, "group" FROM sample LIMIT 1')
    sample = cursor.fetchone()
    if sample:
        print(f"Sample record: {sample}")
    
    # Show table schema
    cursor.execute("PRAGMA table_info(sample)")
    schema = cursor.fetchall()
    print("Table schema:")
    for col in schema:
        print(f"  {col}")
    
    conn.close()
    print(f"Sample table added to database '{db_file}' successfully!")
    return True

if __name__ == "__main__":
    add_sample_table('database/nextgen.db', 'data/metadata.csv') 