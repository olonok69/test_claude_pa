import sqlite3
from datetime import datetime

def create_database():
    """Create the wheat production database with all necessary tables"""
    
    conn = sqlite3.connect('wheat_production.db')
    cursor = conn.cursor()
    
    # Create wheat_production table
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
    
    # Create wheat_exports table
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
    
    # Create metadata table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create audit_log table
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
    
    # Insert initial production data
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
        
        # India
        ("India", "2021/2022", 107.7, 13.8, None, "act"),
        ("India", "2022/2023", 110.6, None, 2.9, "act"),
        ("India", "2023/2024", 113.2, None, 2.6, "estimate"),
        ("India", "2024/2025", 112.0, None, -1.2, "projection"),
        
        # Russia
        ("Russia", "2021/2022", 76.1, 9.8, None, "act"),
        ("Russia", "2022/2023", 104.2, None, 28.1, "act"),
        ("Russia", "2023/2024", 91.0, None, -13.2, "estimate"),
        ("Russia", "2024/2025", 88.0, None, -3.0, "projection"),
        
        # United States
        ("United States", "2021/2022", 44.8, 5.7, None, "act"),
        ("United States", "2022/2023", 44.9, None, 0.1, "act"),
        ("United States", "2023/2024", 49.3, None, 4.4, "estimate"),
        ("United States", "2024/2025", 51.4, None, 2.1, "projection"),
        
        # Australia
        ("Australia", "2021/2022", 36.3, 4.7, None, "act"),
        ("Australia", "2022/2023", 40.0, None, 3.7, "act"),
        ("Australia", "2023/2024", 26.2, None, -13.8, "estimate"),
        ("Australia", "2024/2025", 31.0, None, 4.8, "projection"),
        
        # Canada
        ("Canada", "2021/2022", 21.7, 2.8, None, "act"),
        ("Canada", "2022/2023", 33.8, None, 12.1, "act"),
        ("Canada", "2023/2024", 32.2, None, -1.6, "estimate"),
        ("Canada", "2024/2025", 34.0, None, 1.8, "projection"),
        
        # Ukraine
        ("Ukraine", "2021/2022", 33.0, 4.2, None, "act"),
        ("Ukraine", "2022/2023", 19.5, None, -13.5, "act"),
        ("Ukraine", "2023/2024", 22.5, None, 3.0, "estimate"),
        ("Ukraine", "2024/2025", 22.5, None, 0.0, "projection"),
        
        # Argentina
        ("Argentina", "2021/2022", 22.4, 2.9, None, "act"),
        ("Argentina", "2022/2023", 12.5, None, -9.9, "act"),
        ("Argentina", "2023/2024", 15.5, None, 3.0, "estimate"),
        ("Argentina", "2024/2025", 16.5, None, 1.0, "projection"),
        
        # Kazakhstan
        ("Kazakhstan", "2021/2022", 11.8, 1.5, None, "act"),
        ("Kazakhstan", "2022/2023", 16.5, None, 4.7, "act"),
        ("Kazakhstan", "2023/2024", 16.7, None, 0.2, "estimate"),
        ("Kazakhstan", "2024/2025", 16.5, None, -0.2, "projection"),
        
        # Turkey
        ("Turkey", "2021/2022", 17.7, 2.3, None, "act"),
        ("Turkey", "2022/2023", 19.8, None, 2.1, "act"),
        ("Turkey", "2023/2024", 18.5, None, -1.3, "estimate"),
        ("Turkey", "2024/2025", 19.0, None, 0.5, "projection"),
        
        # Pakistan
        ("Pakistan", "2021/2022", 26.2, 3.4, None, "act"),
        ("Pakistan", "2022/2023", 26.2, None, 0.0, "act"),
        ("Pakistan", "2023/2024", 27.0, None, 0.8, "estimate"),
        ("Pakistan", "2024/2025", 28.0, None, 1.0, "projection"),
        
        # Brazil
        ("Brazil", "2021/2022", 7.9, 1.0, None, "act"),
        ("Brazil", "2022/2023", 10.2, None, 2.3, "act"),
        ("Brazil", "2023/2024", 8.1, None, -2.1, "estimate"),
        ("Brazil", "2024/2025", 8.0, None, -0.1, "projection"),
        
        # United Kingdom
        ("United Kingdom", "2021/2022", 13.0, 1.7, None, "act"),
        ("United Kingdom", "2022/2023", 15.5, None, 2.5, "act"),
        ("United Kingdom", "2023/2024", 14.0, None, -1.5, "estimate"),
        ("United Kingdom", "2024/2025", 12.0, None, -2.0, "projection"),
        
        # Iran
        ("Iran", "2021/2022", 10.0, 1.3, None, "act"),
        ("Iran", "2022/2023", 12.0, None, 2.0, "act"),
        ("Iran", "2023/2024", 14.5, None, 2.5, "estimate"),
        ("Iran", "2024/2025", 14.5, None, 0.0, "projection"),
        
        # Others
        ("Others", "2021/2022", 66.4, 8.5, None, "act"),
        ("Others", "2022/2023", 68.9, None, 2.5, "act"),
        ("Others", "2023/2024", 72.9, None, 4.0, "estimate"),
        ("Others", "2024/2025", 71.4, None, -1.5, "projection"),
    ]
    
    # Insert initial export data
    export_data = [
        # Argentina
        ("Argentina", "2021/2022", 14.5, 7.3, None, "act"),
        ("Argentina", "2022/2023", 5.5, None, -9.0, "act"),
        ("Argentina", "2023/2024", 12.5, None, 7.0, "estimate"),
        ("Argentina", "2024/2025", 12.5, None, 0.0, "projection"),
        
        # Australia
        ("Australia", "2021/2022", 27.5, 13.9, None, "act"),
        ("Australia", "2022/2023", 31.9, None, 4.4, "act"),
        ("Australia", "2023/2024", 18.0, None, -13.9, "estimate"),
        ("Australia", "2024/2025", 24.0, None, 6.0, "projection"),
        
        # Canada
        ("Canada", "2021/2022", 15.4, 7.8, None, "act"),
        ("Canada", "2022/2023", 25.1, None, 9.7, "act"),
        ("Canada", "2023/2024", 24.0, None, -1.1, "estimate"),
        ("Canada", "2024/2025", 24.5, None, 0.5, "projection"),
        
        # European Union
        ("European Union", "2021/2022", 37.5, 18.9, None, "act"),
        ("European Union", "2022/2023", 34.6, None, -2.9, "act"),
        ("European Union", "2023/2024", 35.0, None, 0.4, "estimate"),
        ("European Union", "2024/2025", 30.0, None, -5.0, "projection"),
        
        # Russia
        ("Russia", "2021/2022", 32.1, 16.2, None, "act"),
        ("Russia", "2022/2023", 45.5, None, 13.4, "act"),
        ("Russia", "2023/2024", 51.0, None, 5.5, "estimate"),
        ("Russia", "2024/2025", 48.0, None, -3.0, "projection"),
        
        # Ukraine
        ("Ukraine", "2021/2022", 19.0, 9.6, None, "act"),
        ("Ukraine", "2022/2023", 10.0, None, -9.0, "act"),
        ("Ukraine", "2023/2024", 16.5, None, 6.5, "estimate"),
        ("Ukraine", "2024/2025", 16.0, None, -0.5, "projection"),
        
        # United States
        ("United States", "2021/2022", 21.8, 11.0, None, "act"),
        ("United States", "2022/2023", 21.5, None, -0.3, "act"),
        ("United States", "2023/2024", 21.1, None, -0.4, "estimate"),
        ("United States", "2024/2025", 21.8, None, 0.7, "projection"),
        
        # TOTAL MAJOR EXPORTERS
        ("TOTAL MAJOR EXPORTERS", "2021/2022", 167.8, 84.6, None, "act"),
        ("TOTAL MAJOR EXPORTERS", "2022/2023", 184.1, None, 16.3, "act"),
        ("TOTAL MAJOR EXPORTERS", "2023/2024", 182.1, None, -2.0, "estimate"),
        ("TOTAL MAJOR EXPORTERS", "2024/2025", 176.8, None, -5.3, "projection"),
    ]
    
    # Insert production data
    for data in production_data:
        cursor.execute('''
            INSERT OR IGNORE INTO wheat_production 
            (country, year, production_value, percentage_world, change_value, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', data)
    
    # Insert export data
    for data in export_data:
        cursor.execute('''
            INSERT OR IGNORE INTO wheat_exports 
            (country, year, export_value, percentage_world, change_value, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', data)
    
    # Insert metadata
    metadata = [
        ("production_last_updated", "19 Sept'24"),
        ("production_next_update", "17 Oct'24"),
        ("export_last_updated", "19 Sept'24"),
        ("export_next_update", "17 Oct'24"),
        ("database_version", "2.0"),
        ("created_date", datetime.now().isoformat())
    ]
    
    for key, value in metadata:
        cursor.execute('''
            INSERT OR IGNORE INTO metadata (key, value)
            VALUES (?, ?)
        ''', (key, value))
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print("✅ Database created successfully!")
    print("📊 Tables created:")
    print("   - wheat_production")
    print("   - wheat_exports")
    print("   - metadata")
    print("   - audit_log")
    print(f"📈 Inserted {len(production_data)} production records")
    print(f"📦 Inserted {len(export_data)} export records")
    print(f"🔧 Inserted {len(metadata)} metadata entries")

if __name__ == "__main__":
    create_database()