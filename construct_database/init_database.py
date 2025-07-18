#!/usr/bin/env python3
"""
Script to initialize a SQLite database for protein data.
"""

import sqlite3
from pathlib import Path

def init_database(db_file: str) -> bool:
    """
    Initialize a new SQLite database.
    
    Args:
        db_file (str): Path to the database file to create
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create database directory if it doesn't exist
        db_path = Path(db_file)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Connect to database (this will create it if it doesn't exist)
        conn = sqlite3.connect(db_file)
        conn.close()
        
        print(f"Database '{db_file}' initialized successfully!")
        return True
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False

if __name__ == "__main__":
    init_database('database/nextgen.db')