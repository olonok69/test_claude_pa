import sqlite3
from datetime import datetime

def create_database():
    """Create the complete wheat production database with all tables"""
    
    conn = sqlite3.connect('wheat_production.db')
    cursor = conn.cursor()
    
    print("🗄️ Creating wheat database...")
    
    # Create all tables
    create_tables(cursor)
    
    # Insert all initial data
    insert_production_data(cursor)
    insert_export_data(cursor)
    insert_import_data(cursor)
    insert_stocks_data(cursor)
    insert_su_ratio_data(cursor)
    insert_acreage_data(cursor)
    insert_yield_data(cursor)
    insert_metadata(cursor)
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print("\n✅ Database created successfully!")
    print("📊 Tables created:")
    print("   - wheat_production")
    print("   - wheat_exports")
    print("   - wheat_imports")
    print("   - wheat_stocks")
    print("   - wheat_su_ratio")
    print("   - wheat_acreage")
    print("   - wheat_yield")
    print("   - metadata")
    print("   - audit_log")

def create_tables(cursor):
    """Create all database tables"""
    
    # wheat_production table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wheat_production (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT NOT NULL,
            year TEXT NOT NULL,
            production_value REAL NOT NULL,
            percentage_world REAL,
            change_value REAL,
            status TEXT DEFAULT 'estimate',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(country, year)
        )
    ''')
    
    # wheat_exports table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wheat_exports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT NOT NULL,
            year TEXT NOT NULL,
            export_value REAL NOT NULL,
            percentage_world REAL,
            change_value REAL,
            status TEXT DEFAULT 'estimate',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(country, year)
        )
    ''')
    
    # wheat_imports table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wheat_imports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT NOT NULL,
            year TEXT NOT NULL,
            import_value REAL NOT NULL,
            percentage_world REAL,
            change_value REAL,
            status TEXT DEFAULT 'estimate',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(country, year)
        )
    ''')
    
    # wheat_stocks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wheat_stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT NOT NULL,
            year TEXT NOT NULL,
            stock_value REAL NOT NULL,
            percentage_world REAL,
            change_value REAL,
            stock_to_use_ratio REAL,
            status TEXT DEFAULT 'estimate',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(country, year)
        )
    ''')
    
    # wheat_su_ratio table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wheat_su_ratio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT NOT NULL,
            year TEXT NOT NULL,
            su_ratio REAL NOT NULL,
            change_value REAL,
            category TEXT,
            status TEXT DEFAULT 'estimate',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(country, year)
        )
    ''')
    
    # wheat_acreage table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wheat_acreage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT NOT NULL,
            year TEXT NOT NULL,
            acreage_value REAL NOT NULL,
            percentage_world REAL,
            change_value REAL,
            yield_per_hectare REAL,
            status TEXT DEFAULT 'estimate',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(country, year)
        )
    ''')
    
    # wheat_yield table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wheat_yield (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT NOT NULL,
            year TEXT NOT NULL,
            yield_value REAL NOT NULL,
            change_value REAL,
            change_percentage REAL,
            yield_category TEXT,
            weather_impact TEXT,
            status TEXT DEFAULT 'estimate',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(country, year)
        )
    ''')
    
    # metadata table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # audit_log table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT NOT NULL,
            record_id TEXT NOT NULL,
            action TEXT NOT NULL,
            old_values TEXT,
            new_values TEXT,
            changed_by TEXT NOT NULL,
            changed_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

def insert_production_data(cursor):
    """Insert initial production data"""
    production_data = [
        # WORLD data
        ("WORLD", "2021/2022", 779.7, None, None, "act"),
        ("WORLD", "2022/2023", 803.9, None, 24.2, "act"),
        ("WORLD", "2023/2024", 795.0, None, -8.9, "estimate"),
        ("WORLD", "2024/2025", 798.0, None, 3.0, "projection"),
        
        # China
        ("China", "2021/2022", 137.0, 17.6, None, "act"),
        ("China", "2022/2023", 137.7, None, 0.7, "act"),
        ("China", "2023/2024", 136.0, None, -1.7, "estimate"),
        ("China", "2024/2025", 138.0, None, 2.0, "projection"),
        
        # European Union
        ("European Union (FR, DE)", "2021/2022", 138.4, 17.8, None, "act"),
        ("European Union (FR, DE)", "2022/2023", 134.7, None, -3.7, "act"),
        ("European Union (FR, DE)", "2023/2024", 134.0, None, -0.7, "estimate"),
        ("European Union (FR, DE)", "2024/2025", 126.0, None, -8.0, "projection"),
        
        # Add remaining countries...
        # (Include all the data from your original database_setup.py)
    ]
    
    for data in production_data:
        cursor.execute('''
            INSERT OR IGNORE INTO wheat_production 
            (country, year, production_value, percentage_world, change_value, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', data)
    
    print(f"✅ Inserted {len(production_data)} production records")

def insert_export_data(cursor):
    """Insert initial export data"""
    # Include export data from your original files
    pass

def insert_import_data(cursor):
    """Insert initial import data"""
    # Include import data from your original files
    pass

def insert_stocks_data(cursor):
    """Insert initial stocks data"""
    # Include stocks data from your original files
    pass

def insert_su_ratio_data(cursor):
    """Insert initial S/U ratio data"""
    # Include S/U ratio data from your original files
    pass

def insert_acreage_data(cursor):
    """Insert initial acreage data"""
    # Include acreage data from your original files
    pass

def insert_yield_data(cursor):
    """Insert initial yield data"""
    # Include yield data from your original files
    pass

def insert_metadata(cursor):
    """Insert metadata"""
    metadata = [
        ("production_last_updated", "19 Sept'24"),
        ("production_next_update", "17 Oct'24"),
        ("export_last_updated", "19 Sept'24"),
        ("export_next_update", "17 Oct'24"),
        ("import_last_updated", "19 Sept'24"),
        ("import_next_update", "17 Oct'24"),
        ("stocks_last_updated", "19 Sept'24"),
        ("stocks_next_update", "17 Oct'24"),
        ("su_ratio_last_updated", "19 Sept'24"),
        ("su_ratio_next_update", "17 Oct'24"),
        ("acreage_last_updated", "19 Sept'24"),
        ("acreage_next_update", "17 Oct'24"),
        ("yield_last_updated", "19 Sept'24"),
        ("yield_next_update", "17 Oct'24"),
        ("database_version", "2.0"),
        ("created_date", datetime.now().isoformat())
    ]
    
    for key, value in metadata:
        cursor.execute('''
            INSERT OR IGNORE INTO metadata (key, value)
            VALUES (?, ?)
        ''', (key, value))
    
    print(f"✅ Inserted {len(metadata)} metadata entries")

if __name__ == "__main__":
    create_database()