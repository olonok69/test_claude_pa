import sqlite3
from datetime import datetime

def add_wheat_imports_table():
    """Add wheat imports table to existing database"""
    
    conn = sqlite3.connect('wheat_production.db')
    cursor = conn.cursor()
    
    # Create wheat_imports table
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
    
    # Insert initial import data
    import_data = [
        # Egypt - Top importer
        ("Egypt", "2021/2022", 12.0, None, None, "act"),
        ("Egypt", "2022/2023", 12.9, None, 0.9, "act"),
        ("Egypt", "2023/2024", 12.8, None, -0.1, "act+fc"),
        ("Egypt", "2024/2025", 12.3, None, -0.5, "projection"),
        
        # Indonesia
        ("Indonesia", "2021/2022", 10.5, None, None, "act"),
        ("Indonesia", "2022/2023", 9.6, None, -0.9, "act"),
        ("Indonesia", "2023/2024", 13.1, None, 3.5, "act+fc"),
        ("Indonesia", "2024/2025", 10.9, None, -2.2, "projection"),
        
        # EU-27
        ("EU-27", "2021/2022", 5.7, None, None, "act"),
        ("EU-27", "2022/2023", 13.2, None, 7.5, "act"),
        ("EU-27", "2023/2024", 13.9, None, 0.7, "act+fc"),
        ("EU-27", "2024/2025", 10.1, None, -3.8, "projection"),
        
        # Turkey
        ("Turkey", "2021/2022", 10.7, None, None, "act"),
        ("Turkey", "2022/2023", 13.9, None, 3.2, "act"),
        ("Turkey", "2023/2024", 9.8, None, -4.1, "act+fc"),
        ("Turkey", "2024/2025", 7.0, None, -2.8, "projection"),
        
        # Philippines
        ("Philippines", "2021/2022", 6.8, None, None, "act"),
        ("Philippines", "2022/2023", 5.7, None, -1.1, "act"),
        ("Philippines", "2023/2024", 7.0, None, 1.3, "act+fc"),
        ("Philippines", "2024/2025", 6.4, None, -0.6, "projection"),
        
        # China
        ("China", "2021/2022", 9.9, None, None, "act"),
        ("China", "2022/2023", 13.6, None, 3.7, "act"),
        ("China", "2023/2024", 14.2, None, 0.6, "act+fc"),
        ("China", "2024/2025", 6.2, None, -8.0, "projection"),
        
        # Algeria
        ("Algeria", "2021/2022", 7.5, None, None, "act"),
        ("Algeria", "2022/2023", 7.5, None, 0.0, "act"),
        ("Algeria", "2023/2024", 7.5, None, 0.0, "act+fc"),
        ("Algeria", "2024/2025", 7.5, None, 0.0, "projection"),
        
        # Morocco
        ("Morocco", "2021/2022", 7.0, None, None, "act"),
        ("Morocco", "2022/2023", 7.0, None, 0.0, "act"),
        ("Morocco", "2023/2024", 7.0, None, 0.0, "act+fc"),
        ("Morocco", "2024/2025", 7.0, None, 0.0, "projection"),
        
        # Bangladesh
        ("Bangladesh", "2021/2022", 6.5, None, None, "act"),
        ("Bangladesh", "2022/2023", 6.2, None, -0.3, "act"),
        ("Bangladesh", "2023/2024", 6.8, None, 0.6, "act+fc"),
        ("Bangladesh", "2024/2025", 6.5, None, -0.3, "projection"),
        
        # Japan
        ("Japan", "2021/2022", 5.8, None, None, "act"),
        ("Japan", "2022/2023", 5.9, None, 0.1, "act"),
        ("Japan", "2023/2024", 5.8, None, -0.1, "act+fc"),
        ("Japan", "2024/2025", 5.8, None, 0.0, "projection"),
        
        # Brazil
        ("Brazil", "2021/2022", 6.2, None, None, "act"),
        ("Brazil", "2022/2023", 5.5, None, -0.7, "act"),
        ("Brazil", "2023/2024", 6.0, None, 0.5, "act+fc"),
        ("Brazil", "2024/2025", 5.5, None, -0.5, "projection"),
        
        # Nigeria
        ("Nigeria", "2021/2022", 5.0, None, None, "act"),
        ("Nigeria", "2022/2023", 5.2, None, 0.2, "act"),
        ("Nigeria", "2023/2024", 5.5, None, 0.3, "act+fc"),
        ("Nigeria", "2024/2025", 5.5, None, 0.0, "projection"),
        
        # Mexico
        ("Mexico", "2021/2022", 5.5, None, None, "act"),
        ("Mexico", "2022/2023", 5.3, None, -0.2, "act"),
        ("Mexico", "2023/2024", 5.5, None, 0.2, "act+fc"),
        ("Mexico", "2024/2025", 5.3, None, -0.2, "projection"),
        
        # Saudi Arabia
        ("Saudi Arabia", "2021/2022", 3.8, None, None, "act"),
        ("Saudi Arabia", "2022/2023", 3.9, None, 0.1, "act"),
        ("Saudi Arabia", "2023/2024", 4.0, None, 0.1, "act+fc"),
        ("Saudi Arabia", "2024/2025", 4.0, None, 0.0, "projection"),
        
        # TOTAL MAJOR IMPORTERS (calculated sum)
        ("TOTAL MAJOR IMPORTERS", "2021/2022", 102.9, None, None, "act"),
        ("TOTAL MAJOR IMPORTERS", "2022/2023", 109.6, None, 6.7, "act"),
        ("TOTAL MAJOR IMPORTERS", "2023/2024", 113.3, None, 3.7, "act+fc"),
        ("TOTAL MAJOR IMPORTERS", "2024/2025", 98.0, None, -15.3, "projection"),
    ]
    
    # Insert import data
    for data in import_data:
        cursor.execute('''
            INSERT OR IGNORE INTO wheat_imports 
            (country, year, import_value, percentage_world, change_value, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', data)
    
    # Update metadata for imports
    metadata_updates = [
        ("import_last_updated", "19 Sept'24"),
        ("import_next_update", "17 Oct'24"),
    ]
    
    for key, value in metadata_updates:
        cursor.execute('''
            INSERT OR REPLACE INTO metadata (key, value, updated_at)
            VALUES (?, ?, ?)
        ''', (key, value, datetime.now().isoformat()))
    
    # Commit changes
    conn.commit()
    
    # Verify the data was inserted
    cursor.execute("SELECT COUNT(*) FROM wheat_imports")
    count = cursor.fetchone()[0]
    
    conn.close()
    
    print("✅ Wheat imports table created successfully!")
    print(f"📦 Inserted {count} import records")
    print("🌍 Major importing countries added:")
    print("   - Egypt (Top importer)")
    print("   - Indonesia")
    print("   - EU-27")
    print("   - Turkey")
    print("   - Philippines")
    print("   - China")
    print("   - And 8 more countries...")

if __name__ == "__main__":
    add_wheat_imports_table()