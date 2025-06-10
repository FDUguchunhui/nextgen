#!/usr/bin/env python3
"""
Script to read human_canonical_proteins.tsv and create a SQLite database
with a proteins table where Entry is the primary key.
"""

import sqlite3
import csv
import sys
from typing import List, Dict

def get_column_names(tsv_file: str) -> List[str]:
    """Extract column names from the first line of the TSV file."""
    with open(tsv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        return next(reader)

def create_database_schema(columns: List[str]) -> str:
    """Create the SQL CREATE TABLE statement."""
    # Clean column names - replace spaces and special characters
    clean_columns = []
    for col in columns:
        # Replace problematic characters
        clean_col = col.replace(' ', '_').replace('(', '').replace(')', '').replace('[', '').replace(']', '').replace('-', '_')
        # Remove multiple underscores
        clean_col = '_'.join(filter(None, clean_col.split('_')))
        clean_columns.append(clean_col)
    
    # Make Entry the primary key
    sql_columns = []
    for i, col in enumerate(clean_columns):
        if col == 'Entry':
            sql_columns.append(f'"{col}" TEXT PRIMARY KEY')
        else:
            sql_columns.append(f'"{col}" TEXT')
    
    return f"CREATE TABLE proteins (\n    {',\n    '.join(sql_columns)}\n)"

def create_proteins_database():
    """Main function to create the database."""
    tsv_file = "human_canonical_proteins.tsv"
    db_file = "test.db"
    
    print("Reading column names from TSV file...")
    columns = get_column_names(tsv_file)
    print(f"Found {len(columns)} columns")
    
    # Create database schema
    create_table_sql = create_database_schema(columns)
    
    # Clean column names for insertion
    clean_columns = []
    for col in columns:
        clean_col = col.replace(' ', '_').replace('(', '').replace(')', '').replace('[', '').replace(']', '').replace('-', '_')
        clean_col = '_'.join(filter(None, clean_col.split('_')))
        clean_columns.append(clean_col)
    
    print("Creating SQLite database...")
    
    # Connect to database and create table
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Drop table if it exists
    cursor.execute("DROP TABLE IF EXISTS proteins")
    
    # Create table
    cursor.execute(create_table_sql)
    print("Table 'proteins' created successfully")
    
    # Prepare insert statement
    placeholders = ','.join(['?' for _ in columns])
    column_list = ",".join([f'"{col}"' for col in clean_columns])
    insert_sql = f'INSERT INTO proteins ({column_list}) VALUES ({placeholders})'
    
    print("Reading and inserting data...")
    
    # Read and insert data
    inserted_count = 0
    try:
        with open(tsv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            next(reader)  # Skip header
            
            batch_size = 1000
            batch = []
            
            for row_num, row in enumerate(reader, 1):
                # Pad row with empty strings if needed
                while len(row) < len(columns):
                    row.append('')
                
                # Truncate row if too long
                row = row[:len(columns)]
                
                batch.append(row)
                
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
        print(f"Error reading TSV file: {e}")
        return False
    
    # Commit changes
    conn.commit()
    
    # Verify the data
    cursor.execute("SELECT COUNT(*) FROM proteins")
    count = cursor.fetchone()[0]
    print(f"Total records in database: {count}")
    
    # Show a sample record
    cursor.execute("SELECT Entry, Entry_Name, Protein_names FROM proteins LIMIT 1")
    sample = cursor.fetchone()
    if sample:
        print(f"Sample record: {sample}")
    
    conn.close()
    print(f"Database '{db_file}' created successfully!")
    return True

if __name__ == "__main__":
    create_proteins_database() 