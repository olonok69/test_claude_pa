import sqlite3
from datetime import datetime

def add_wheat_yield_table():
    """Add wheat yield table to existing database"""
    
    conn = sqlite3.connect('wheat_production.db')
    cursor = conn.cursor()
    
    # Create wheat_yield table
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
    
    # Insert initial yield data (tonnes per hectare - t/ha)
    yield_data = [
        # WORLD - Global average
        ("WORLD", "2021/2022", 3.53, None, None, "Medium", "Normal", "estimate"),
        ("WORLD", "2022/2023", 3.58, 0.05, 1.3, "Medium", "Favorable", "act"),
        ("WORLD", "2023/2024", 3.48, -0.10, -2.6, "Medium", "Mixed", "estimate"),
        ("WORLD", "2024/2025", 3.52, 0.04, 1.1, "Medium", "Normal", "projection"),
        
        # China - Consistently high yields
        ("China", "2021/2022", 5.78, None, None, "High", "Normal", "estimate"),
        ("China", "2022/2023", 5.75, -0.03, -0.6, "High", "Normal", "act"),
        ("China", "2023/2024", 5.70, -0.05, -0.8, "High", "Normal", "estimate"),
        ("China", "2024/2025", 5.83, 0.13, 2.3, "High", "Favorable", "projection"),
        
        # European Union 27 - High yields with variability
        ("European Union 27 (FR, DE)", "2021/2022", 5.57, None, None, "High", "Normal", "estimate"),
        ("European Union 27 (FR, DE)", "2022/2023", 5.43, -0.14, -2.5, "High", "Dry", "act"),
        ("European Union 27 (FR, DE)", "2023/2024", 5.53, 0.10, 2.0, "High", "Recovery", "estimate"),
        ("European Union 27 (FR, DE)", "2024/2025", 5.14, -0.39, -7.1, "High", "Challenging", "projection"),
        
        # India - Lower yields, gradual improvement
        ("India", "2021/2022", 3.19, None, None, "Medium", "Normal", "estimate"),
        ("India", "2022/2023", 3.14, -0.05, -1.4, "Medium", "Hot", "act"),
        ("India", "2023/2024", 3.25, 0.11, 3.5, "Medium", "Favorable", "estimate"),
        ("India", "2024/2025", 3.31, 0.06, 1.8, "Medium", "Normal", "projection"),
        
        # Russia - Variable yields
        ("Russia", "2021/2022", 2.61, None, None, "Low", "Challenging", "estimate"),
        ("Russia", "2022/2023", 3.24, 0.63, 24.0, "Medium", "Excellent", "act"),
        ("Russia", "2023/2024", 3.27, 0.03, 0.9, "Medium", "Normal", "estimate"),
        ("Russia", "2024/2025", 2.87, -0.40, -12.2, "Low", "Dry", "projection"),
        
        # United States - Improving yields
        ("United States", "2021/2022", 3.04, None, None, "Medium", "Drought", "estimate"),
        ("United States", "2022/2023", 3.13, 0.09, 2.9, "Medium", "Recovery", "act"),
        ("United States", "2023/2024", 3.27, 0.14, 4.6, "Medium", "Good", "estimate"),
        ("United States", "2024/2025", 3.55, 0.28, 8.5, "Medium", "Excellent", "projection"),
        
        # Australia - Highly variable (weather dependent)
        ("Australia", "2021/2022", 2.74, None, None, "Low", "Dry", "estimate"),
        ("Australia", "2022/2023", 3.10, 0.36, 13.2, "Medium", "La Niña", "act"),
        ("Australia", "2023/2024", 2.09, -1.01, -32.6, "Low", "El Niño", "estimate"),
        ("Australia", "2024/2025", 2.48, 0.39, 18.8, "Low", "Recovery", "projection"),
        
        # Canada - Variable yields
        ("Canada", "2021/2022", 2.45, None, None, "Low", "Drought", "estimate"),
        ("Canada", "2022/2023", 3.35, 0.90, 36.6, "Medium", "Recovery", "act"),
        ("Canada", "2023/2024", 3.01, -0.34, -10.1, "Medium", "Mixed", "estimate"),
        ("Canada", "2024/2025", 3.33, 0.32, 10.6, "Medium", "Normal", "projection"),
        
        # Ukraine - Productive despite challenges
        ("Ukraine", "2021/2022", 4.78, None, None, "Medium", "Good", "estimate"),
        ("Ukraine", "2022/2023", 4.33, -0.45, -9.4, "Medium", "Conflict", "act"),
        ("Ukraine", "2023/2024", 4.50, 0.17, 3.9, "Medium", "Recovery", "estimate"),
        ("Ukraine", "2024/2025", 4.50, 0.00, 0.0, "Medium", "Stable", "projection"),
        
        # Pakistan - Lower yields
        ("Pakistan", "2021/2022", 2.85, None, None, "Low", "Normal", "estimate"),
        ("Pakistan", "2022/2023", 2.89, 0.04, 1.4, "Low", "Normal", "act"),
        ("Pakistan", "2023/2024", 2.94, 0.05, 1.7, "Low", "Normal", "estimate"),
        ("Pakistan", "2024/2025", 3.01, 0.07, 2.4, "Medium", "Improving", "projection"),
        
        # Argentina - Variable yields
        ("Argentina", "2021/2022", 3.45, None, None, "Medium", "Normal", "estimate"),
        ("Argentina", "2022/2023", 2.36, -1.09, -31.6, "Low", "Drought", "act"),
        ("Argentina", "2023/2024", 2.82, 0.46, 19.5, "Low", "Recovery", "estimate"),
        ("Argentina", "2024/2025", 2.89, 0.07, 2.5, "Low", "Normal", "projection"),
        
        # Turkey - Moderate yields
        ("Turkey", "2021/2022", 2.60, None, None, "Low", "Dry", "estimate"),
        ("Turkey", "2022/2023", 2.75, 0.15, 5.8, "Low", "Normal", "act"),
        ("Turkey", "2023/2024", 2.68, -0.07, -2.5, "Low", "Mixed", "estimate"),
        ("Turkey", "2024/2025", 2.71, 0.03, 1.1, "Low", "Normal", "projection"),
        
        # Kazakhstan - Low yields, large area
        ("Kazakhstan", "2021/2022", 1.03, None, None, "Very Low", "Drought", "estimate"),
        ("Kazakhstan", "2022/2023", 1.29, 0.26, 25.2, "Very Low", "Better", "act"),
        ("Kazakhstan", "2023/2024", 1.30, 0.01, 0.8, "Very Low", "Normal", "estimate"),
        ("Kazakhstan", "2024/2025", 1.30, 0.00, 0.0, "Very Low", "Normal", "projection"),
        
        # Iran - Low to moderate yields
        ("Iran", "2021/2022", 1.75, None, None, "Very Low", "Drought", "estimate"),
        ("Iran", "2022/2023", 2.07, 0.32, 18.3, "Low", "Better", "act"),
        ("Iran", "2023/2024", 2.42, 0.35, 16.9, "Low", "Good", "estimate"),
        ("Iran", "2024/2025", 2.42, 0.00, 0.0, "Low", "Normal", "projection"),
        
        # United Kingdom - High yields
        ("United Kingdom", "2021/2022", 7.69, None, None, "Very High", "Normal", "estimate"),
        ("United Kingdom", "2022/2023", 7.74, 0.05, 0.6, "Very High", "Good", "act"),
        ("United Kingdom", "2023/2024", 7.86, 0.12, 1.6, "Very High", "Good", "estimate"),
        ("United Kingdom", "2024/2025", 7.50, -0.36, -4.6, "Very High", "Wet", "projection"),
    ]
    
    # Define yield categories
    def get_yield_category(yield_val):
        if yield_val >= 7.0:
            return "Very High"
        elif yield_val >= 5.0:
            return "High"
        elif yield_val >= 3.0:
            return "Medium"
        elif yield_val >= 2.0:
            return "Low"
        else:
            return "Very Low"
    
    # Insert yield data
    for data in yield_data:
        cursor.execute('''
            INSERT OR IGNORE INTO wheat_yield 
            (country, year, yield_value, change_value, change_percentage, yield_category, weather_impact, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)
    
    # Update metadata for yields
    metadata_updates = [
        ("yield_last_updated", "19 Sept'24"),
        ("yield_next_update", "17 Oct'24"),
    ]
    
    for key, value in metadata_updates:
        cursor.execute('''
            INSERT OR REPLACE INTO metadata (key, value, updated_at)
            VALUES (?, ?, ?)
        ''', (key, value, datetime.now().isoformat()))
    
    # Commit changes
    conn.commit()
    
    # Verify the data was inserted
    cursor.execute("SELECT COUNT(*) FROM wheat_yield")
    count = cursor.fetchone()[0]
    
    # Get yield statistics
    cursor.execute("""
        SELECT 
            AVG(yield_value) as avg_yield,
            MAX(yield_value) as max_yield,
            MIN(yield_value) as min_yield,
            COUNT(DISTINCT yield_category) as categories
        FROM wheat_yield 
        WHERE year = '2024/2025'
    """)
    stats = cursor.fetchone()
    
    conn.close()
    
    print("✅ Wheat yield table created successfully!")
    print(f"📊 Inserted {count} yield records")
    print("\n🌾 Yield Statistics for 2024/2025:")
    print(f"   - Average yield: {stats[0]:.2f} t/ha")
    print(f"   - Highest yield: {stats[1]:.2f} t/ha")
    print(f"   - Lowest yield: {stats[2]:.2f} t/ha")
    print(f"   - Categories: {stats[3]}")
    print("\n📈 Yield Categories:")
    print("   - Very High (≥7.0): UK")
    print("   - High (≥5.0): China, EU")
    print("   - Medium (≥3.0): USA, Canada, India")
    print("   - Low (≥2.0): Russia, Australia, Argentina")
    print("   - Very Low (<2.0): Kazakhstan")

if __name__ == "__main__":
    add_wheat_yield_table()