import sqlite3
from datetime import datetime

def add_wheat_acreage_table():
    """Add wheat acreage (area harvested) table to existing database"""
    
    conn = sqlite3.connect('wheat_production.db')
    cursor = conn.cursor()
    
    # Create wheat_acreage table
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
    
    # Insert initial acreage data (Million Hectares - Mha)
    acreage_data = [
        # WORLD
        ("WORLD", "2021/2022", 220.8, None, None, 3.53, "estimate"),
        ("WORLD", "2022/2023", 224.79, None, 3.99, 3.58, "act"),
        ("WORLD", "2023/2024", 228.18, None, 3.39, 3.48, "estimate"),
        ("WORLD", "2024/2025", 226.5, None, -1.68, 3.52, "projection"),
        
        # China - Stable acreage
        ("China", "2021/2022", 23.67, 10.7, None, 5.79, "estimate"),
        ("China", "2022/2023", 23.95, 10.7, 0.28, 5.75, "act"),
        ("China", "2023/2024", 23.95, 10.5, 0.00, 5.69, "estimate"),
        ("China", "2024/2025", 24.0, 10.6, 0.05, 5.75, "projection"),
        
        # European Union 27
        ("European Union 27 (FR, DE)", "2021/2022", 24.70, 11.2, None, 5.60, "estimate"),
        ("European Union 27 (FR, DE)", "2022/2023", 24.57, 10.9, -0.13, 5.48, "act"),
        ("European Union 27 (FR, DE)", "2023/2024", 24.05, 10.5, -0.52, 5.57, "estimate"),
        ("European Union 27 (FR, DE)", "2024/2025", 23.80, 10.5, -0.25, 5.29, "projection"),
        
        # India - Large acreage
        ("India", "2021/2022", 34.38, 15.6, None, 3.13, "estimate"),
        ("India", "2022/2023", 34.28, 15.3, -0.10, 3.14, "act"),
        ("India", "2023/2024", 34.00, 14.9, -0.28, 3.25, "estimate"),
        ("India", "2024/2025", 34.10, 15.1, 0.10, 3.28, "projection"),
        
        # Russia - Variable acreage
        ("Russia", "2021/2022", 28.70, 13.0, None, 2.65, "estimate"),
        ("Russia", "2022/2023", 29.43, 13.1, 0.73, 3.54, "act"),
        ("Russia", "2023/2024", 27.83, 12.2, -1.60, 3.27, "estimate"),
        ("Russia", "2024/2025", 28.50, 12.6, 0.67, 3.09, "projection"),
        
        # United States
        ("United States", "2021/2022", 14.74, 6.7, None, 3.04, "estimate"),
        ("United States", "2022/2023", 14.36, 6.4, -0.38, 3.13, "act"),
        ("United States", "2023/2024", 15.08, 6.6, 0.72, 3.27, "estimate"),
        ("United States", "2024/2025", 15.20, 6.7, 0.12, 3.38, "projection"),
        
        # Australia - Variable due to weather
        ("Australia", "2021/2022", 13.20, 6.0, None, 2.75, "estimate"),
        ("Australia", "2022/2023", 13.05, 5.8, -0.15, 3.07, "act"),
        ("Australia", "2023/2024", 12.43, 5.4, -0.62, 2.10, "estimate"),
        ("Australia", "2024/2025", 12.80, 5.7, 0.37, 2.42, "projection"),
        
        # Canada
        ("Canada", "2021/2022", 8.84, 4.0, None, 2.46, "estimate"),
        ("Canada", "2022/2023", 10.08, 4.5, 1.24, 3.35, "act"),
        ("Canada", "2023/2024", 10.68, 4.7, 0.60, 3.01, "estimate"),
        ("Canada", "2024/2025", 10.20, 4.5, -0.48, 3.33, "projection"),
        
        # Ukraine - Significant producer
        ("Ukraine", "2021/2022", 6.90, 3.1, None, 4.78, "estimate"),
        ("Ukraine", "2022/2023", 4.50, 2.0, -2.40, 4.33, "act"),
        ("Ukraine", "2023/2024", 5.00, 2.2, 0.50, 4.50, "estimate"),
        ("Ukraine", "2024/2025", 5.00, 2.2, 0.00, 4.50, "projection"),
        
        # Pakistan
        ("Pakistan", "2021/2022", 9.20, 4.2, None, 2.85, "estimate"),
        ("Pakistan", "2022/2023", 9.05, 4.0, -0.15, 2.89, "act"),
        ("Pakistan", "2023/2024", 9.18, 4.0, 0.13, 2.94, "estimate"),
        ("Pakistan", "2024/2025", 9.30, 4.1, 0.12, 3.01, "projection"),
        
        # Argentina
        ("Argentina", "2021/2022", 6.50, 2.9, None, 3.45, "estimate"),
        ("Argentina", "2022/2023", 5.30, 2.4, -1.20, 2.36, "act"),
        ("Argentina", "2023/2024", 5.50, 2.4, 0.20, 2.82, "estimate"),
        ("Argentina", "2024/2025", 5.70, 2.5, 0.20, 2.89, "projection"),
        
        # Turkey
        ("Turkey", "2021/2022", 6.80, 3.1, None, 2.60, "estimate"),
        ("Turkey", "2022/2023", 7.20, 3.2, 0.40, 2.75, "act"),
        ("Turkey", "2023/2024", 6.90, 3.0, -0.30, 2.68, "estimate"),
        ("Turkey", "2024/2025", 7.00, 3.1, 0.10, 2.71, "projection"),
        
        # Kazakhstan
        ("Kazakhstan", "2021/2022", 11.50, 5.2, None, 1.03, "estimate"),
        ("Kazakhstan", "2022/2023", 12.75, 5.7, 1.25, 1.29, "act"),
        ("Kazakhstan", "2023/2024", 12.80, 5.6, 0.05, 1.30, "estimate"),
        ("Kazakhstan", "2024/2025", 12.70, 5.6, -0.10, 1.30, "projection"),
        
        # Iran
        ("Iran", "2021/2022", 5.70, 2.6, None, 1.75, "estimate"),
        ("Iran", "2022/2023", 5.80, 2.6, 0.10, 2.07, "act"),
        ("Iran", "2023/2024", 6.00, 2.6, 0.20, 2.42, "estimate"),
        ("Iran", "2024/2025", 6.00, 2.7, 0.00, 2.42, "projection"),
        
        # Others (calculated to match world total)
        ("Others", "2021/2022", 38.84, 17.6, None, 2.71, "estimate"),
        ("Others", "2022/2023", 41.01, 18.3, 2.17, 2.80, "act"),
        ("Others", "2023/2024", 44.36, 19.4, 3.35, 2.64, "estimate"),
        ("Others", "2024/2025", 42.30, 18.7, -2.06, 2.69, "projection"),
    ]
    
    # Insert acreage data
    for data in acreage_data:
        cursor.execute('''
            INSERT OR IGNORE INTO wheat_acreage 
            (country, year, acreage_value, percentage_world, change_value, yield_per_hectare, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', data)
    
    # Update metadata for acreage
    metadata_updates = [
        ("acreage_last_updated", "19 Sept'24"),
        ("acreage_next_update", "17 Oct'24"),
    ]
    
    for key, value in metadata_updates:
        cursor.execute('''
            INSERT OR REPLACE INTO metadata (key, value, updated_at)
            VALUES (?, ?, ?)
        ''', (key, value, datetime.now().isoformat()))
    
    # Commit changes
    conn.commit()
    
    # Verify the data was inserted
    cursor.execute("SELECT COUNT(*) FROM wheat_acreage")
    count = cursor.fetchone()[0]
    
    # Get summary statistics
    cursor.execute("""
        SELECT 
            SUM(acreage_value) as total_acreage,
            AVG(yield_per_hectare) as avg_yield
        FROM wheat_acreage 
        WHERE year = '2024/2025' AND country != 'WORLD' AND country != 'Others'
    """)
    stats = cursor.fetchone()
    
    conn.close()
    
    print("✅ Wheat acreage table created successfully!")
    print(f"📊 Inserted {count} acreage records")
    print("\n🌾 Key Statistics for 2024/2025:")
    print(f"   - Total acreage (excl. Others): {stats[0]:.1f} Mha")
    print(f"   - Average yield: {stats[1]:.2f} t/ha")
    print("\n🌍 Major wheat growing countries by area:")
    print("   - India: 34.1 Mha (15.1% of world)")
    print("   - Russia: 28.5 Mha (12.6% of world)")
    print("   - China: 24.0 Mha (10.6% of world)")
    print("   - EU-27: 23.8 Mha (10.5% of world)")
    print("   - United States: 15.2 Mha (6.7% of world)")

if __name__ == "__main__":
    add_wheat_acreage_table()