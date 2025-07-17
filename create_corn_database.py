#!/usr/bin/env python3
"""
Comprehensive script to create and populate corn_production.db database
This script creates all tables and loads all corn data from the dashboard
Based on the wheat_production.db implementation
"""

import sqlite3
from datetime import datetime
import os
import sys


def create_database():
    """Create the complete corn production database with all tables"""

    # Remove existing database if it exists
    db_path = "corn_production.db"
    if os.path.exists(db_path):
        response = input(
            f"⚠️  Database {db_path} already exists. Delete and recreate? (yes/no): "
        )
        if response.lower() == "yes":
            os.remove(db_path)
            print(f"✅ Removed existing database")
        else:
            print("❌ Operation cancelled")
            sys.exit(0)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🗄️ Creating corn database...")

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
    insert_world_demand_data(cursor)
    insert_metadata(cursor)

    # Commit changes
    conn.commit()
    conn.close()

    print("\n✅ Database created successfully!")
    print("📊 Tables created:")
    print("   - corn_production")
    print("   - corn_exports")
    print("   - corn_imports")
    print("   - corn_stocks")
    print("   - corn_su_ratio")
    print("   - corn_acreage")
    print("   - corn_yield")
    print("   - corn_world_demand")
    print("   - metadata")
    print("   - audit_log")

    # Verify the data
    verify_database(db_path)


def create_tables(cursor):
    """Create all database tables"""

    # corn_production table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS corn_production (
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
    """
    )

    # corn_exports table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS corn_exports (
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
    """
    )

    # corn_imports table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS corn_imports (
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
    """
    )

    # corn_stocks table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS corn_stocks (
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
    """
    )

    # corn_su_ratio table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS corn_su_ratio (
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
    """
    )

    # corn_acreage table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS corn_acreage (
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
    """
    )

    # corn_yield table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS corn_yield (
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
    """
    )

    # corn_world_demand table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS corn_world_demand (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            year TEXT NOT NULL,
            demand_value REAL NOT NULL,
            percentage_total REAL,
            change_value REAL,
            change_percentage REAL,
            unit TEXT DEFAULT 'mln metrics tn',
            status TEXT DEFAULT 'estimate',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(category, year)
        )
    """
    )

    # metadata table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # audit_log table
    cursor.execute(
        """
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
    """
    )


def get_status(year):
    """Determine status based on year"""
    if year in ["2021/2022", "2022/2023", "2023/2024"]:
        return "actual"
    elif year == "2024/2025":
        return "estimate"
    elif year == "2025/2026":
        return "projection"
    return "actual"


def get_su_ratio_category(ratio):
    """Determine category based on S/U ratio value"""
    if ratio >= 50:
        return "Strategic Reserve"
    elif ratio >= 30:
        return "Comfortable"
    elif ratio >= 20:
        return "Adequate"
    elif ratio >= 10:
        return "Tight"
    else:
        return "Critical"


def get_yield_category(yield_value):
    """Determine yield category"""
    if yield_value >= 10.0:
        return "Very High"
    elif yield_value >= 7.0:
        return "High"
    elif yield_value >= 5.0:
        return "Medium"
    elif yield_value >= 3.0:
        return "Low"
    else:
        return "Very Low"


def insert_production_data(cursor):
    """Insert corn production data"""
    production_data = [
        # WORLD data
        ("WORLD", "2021/2022", 1214.2, None, None),
        ("WORLD", "2022/2023", 1164.2, None, -50.0),
        ("WORLD", "2023/2024", 1229.3, None, 65.1),
        ("WORLD", "2024/2025", 1214.2, None, -15.1),
        ("WORLD", "2025/2026", 1266.0, None, 51.8),
        # China
        ("China", "2021/2022", 272.6, 22, None),
        ("China", "2022/2023", 277.2, None, 4.6),
        ("China", "2023/2024", 288.8, None, 11.6),
        ("China", "2024/2025", 294.9, None, 6.1),
        ("China", "2025/2026", 295.0, None, 0.1),
        # European Union
        ("European Union", "2021/2022", 66.9, 6, None),
        ("European Union", "2022/2023", 52.4, None, -14.5),
        ("European Union", "2023/2024", 62.0, None, 9.6),
        ("European Union", "2024/2025", 59.3, None, -2.7),
        ("European Union", "2025/2026", 60.0, None, 0.7),
        # India
        ("India", "2021/2022", 33.6, 3, None),
        ("India", "2022/2023", 38.1, None, 4.5),
        ("India", "2023/2024", 37.7, None, -0.4),
        ("India", "2024/2025", 40.0, None, 2.3),
        ("India", "2025/2026", 40.5, None, 0.5),
        # Russia
        ("Russia", "2021/2022", 15.0, 1, None),
        ("Russia", "2022/2023", 15.8, None, 0.8),
        ("Russia", "2023/2024", 16.6, None, 0.8),
        ("Russia", "2024/2025", 14.0, None, -2.6),
        ("Russia", "2025/2026", 14.5, None, 0.5),
        # United States
        ("United States", "2021/2022", 383.9, 32, None),
        ("United States", "2022/2023", 346.7, None, -37.2),
        ("United States", "2023/2024", 389.7, None, 43.0),
        ("United States", "2024/2025", 377.6, None, -12.1),
        ("United States", "2025/2026", 395.7, None, 18.1),
        # Australia
        ("Australia", "2021/2022", 1.9, 0, None),
        ("Australia", "2022/2023", 1.8, None, -0.1),
        ("Australia", "2023/2024", 1.4, None, -0.4),
        ("Australia", "2024/2025", 1.7, None, 0.3),
        ("Australia", "2025/2026", 1.8, None, 0.1),
        # Canada
        ("Canada", "2021/2022", 14.6, 1, None),
        ("Canada", "2022/2023", 14.5, None, -0.1),
        ("Canada", "2023/2024", 15.4, None, 0.9),
        ("Canada", "2024/2025", 15.4, None, 0.0),
        ("Canada", "2025/2026", 15.5, None, 0.1),
    ]

    for country, year, value, pct, change in production_data:
        status = get_status(year)
        cursor.execute(
            """
            INSERT OR IGNORE INTO corn_production 
            (country, year, production_value, percentage_world, change_value, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (country, year, value, pct, change, status),
        )

    print(f"✅ Inserted {len(production_data)} production records")


def insert_export_data(cursor):
    """Insert corn export data"""
    export_data = [
        # WORLD data
        ("WORLD", "2021/2022", 193.5, None, None),
        ("WORLD", "2022/2023", 181.0, None, -12.5),
        ("WORLD", "2023/2024", 198.2, None, 17.2),
        ("WORLD", "2024/2025", 187.8, None, -10.4),
        ("WORLD", "2025/2026", 195.1, None, 7.3),
        # China
        ("China", "2021/2022", 2.2, 1, None),
        ("China", "2022/2023", 1.6, None, -0.6),
        ("China", "2023/2024", 1.1, None, -0.5),
        ("China", "2024/2025", 0.9, None, -0.2),
        ("China", "2025/2026", 0.9, None, 0.0),
        # European Union
        ("European Union", "2021/2022", 6.0, 3, None),
        ("European Union", "2022/2023", 4.2, None, -1.8),
        ("European Union", "2023/2024", 4.4, None, 0.2),
        ("European Union", "2024/2025", 2.4, None, -2.0),
        ("European Union", "2025/2026", 3.0, None, 0.6),
        # India
        ("India", "2021/2022", 0.04, 0, None),
        ("India", "2022/2023", 0.04, None, 0.0),
        ("India", "2023/2024", 0.03, None, -0.01),
        ("India", "2024/2025", 0.05, None, 0.02),
        ("India", "2025/2026", 0.05, None, 0.0),
        # Russia
        ("Russia", "2021/2022", 4.0, 2, None),
        ("Russia", "2022/2023", 5.9, None, 1.9),
        ("Russia", "2023/2024", 6.6, None, 0.7),
        ("Russia", "2024/2025", 3.3, None, -3.3),
        ("Russia", "2025/2026", 3.6, None, 0.3),
        # United States
        ("United States", "2021/2022", 62.9, 33, None),
        ("United States", "2022/2023", 42.8, None, -20.1),
        ("United States", "2023/2024", 59.3, None, 16.5),
        ("United States", "2024/2025", 66.0, None, 6.7),
        ("United States", "2025/2026", 68.0, None, 2.0),
        # Australia
        ("Australia", "2021/2022", 0.5, 0, None),
        ("Australia", "2022/2023", 0.8, None, 0.3),
        ("Australia", "2023/2024", 0.5, None, -0.3),
        ("Australia", "2024/2025", 0.4, None, -0.1),
        ("Australia", "2025/2026", 0.4, None, 0.0),
        # Canada
        ("Canada", "2021/2022", 2.2, 1, None),
        ("Canada", "2022/2023", 2.9, None, 0.7),
        ("Canada", "2023/2024", 2.2, None, -0.7),
        ("Canada", "2024/2025", 2.2, None, 0.0),
        ("Canada", "2025/2026", 2.1, None, -0.1),
    ]

    for country, year, value, pct, change in export_data:
        status = get_status(year)
        cursor.execute(
            """
            INSERT OR IGNORE INTO corn_exports 
            (country, year, export_value, percentage_world, change_value, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (country, year, value, pct, change, status),
        )

    print(f"✅ Inserted {len(export_data)} export records")


def insert_import_data(cursor):
    """Insert corn import data"""
    import_data = [
        # World total
        ("World", "2021/2022", 193.5, None, None),
        ("World", "2022/2023", 181.0, None, -12.5),
        ("World", "2023/2024", 198.2, None, 17.2),
        ("World", "2024/2025", 187.8, None, -10.4),
        ("World", "2025/2026", 195.1, None, 7.3),
        # Mexico
        ("Mexico", "2021/2022", 17.6, 9, None),
        ("Mexico", "2022/2023", 19.4, None, 1.8),
        ("Mexico", "2023/2024", 24.8, None, 5.4),
        ("Mexico", "2024/2025", 25.0, None, 0.2),
        ("Mexico", "2025/2026", 25.0, None, 0.0),
        # Japan
        ("Japan", "2021/2022", 15.0, 8, None),
        ("Japan", "2022/2023", 14.9, None, -0.1),
        ("Japan", "2023/2024", 15.3, None, 0.4),
        ("Japan", "2024/2025", 15.3, None, 0.0),
        ("Japan", "2025/2026", 15.5, None, 0.2),
        # China
        ("China", "2021/2022", 21.9, 11, None),
        ("China", "2022/2023", 18.7, None, -3.2),
        ("China", "2023/2024", 23.4, None, 4.7),
        ("China", "2024/2025", 8.0, None, -15.4),
        ("China", "2025/2026", 10.0, None, 2.0),
        # South Korea
        ("South Korea", "2021/2022", 11.5, 6, None),
        ("South Korea", "2022/2023", 11.1, None, -0.4),
        ("South Korea", "2023/2024", 11.6, None, 0.5),
        ("South Korea", "2024/2025", 11.5, None, -0.1),
        ("South Korea", "2025/2026", 11.5, None, 0.0),
        # European Union
        ("European Union", "2021/2022", 19.5, 10, None),
        ("European Union", "2022/2023", 23.2, None, 3.7),
        ("European Union", "2023/2024", 19.8, None, -3.4),
        ("European Union", "2024/2025", 20.0, None, 0.2),
        ("European Union", "2025/2026", 20.5, None, 0.5),
        # Vietnam
        ("Vietnam", "2021/2022", 9.1, 5, None),
        ("Vietnam", "2022/2023", 9.5, None, 0.4),
        ("Vietnam", "2023/2024", 11.3, None, 1.8),
        ("Vietnam", "2024/2025", 12.5, None, 1.2),
        ("Vietnam", "2025/2026", 13.0, None, 0.5),
        # Egypt
        ("Egypt", "2021/2022", 9.8, 5, None),
        ("Egypt", "2022/2023", 6.2, None, -3.6),
        ("Egypt", "2023/2024", 8.0, None, 1.8),
        ("Egypt", "2024/2025", 8.4, None, 0.4),
        ("Egypt", "2025/2026", 8.8, None, 0.4),
        # Colombia
        ("Colombia", "2021/2022", 6.5, 3, None),
        ("Colombia", "2022/2023", 6.3, None, -0.2),
        ("Colombia", "2023/2024", 6.6, None, 0.3),
        ("Colombia", "2024/2025", 7.0, None, 0.4),
        ("Colombia", "2025/2026", 7.2, None, 0.2),
    ]

    for country, year, value, pct, change in import_data:
        status = get_status(year)
        cursor.execute(
            """
            INSERT OR IGNORE INTO corn_imports 
            (country, year, import_value, percentage_world, change_value, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (country, year, value, pct, change, status),
        )

    print(f"✅ Inserted {len(import_data)} import records")


def insert_stocks_data(cursor):
    """Insert corn ending stocks data"""
    stocks_data = [
        # WORLD data
        ("WORLD", "2021/2022", 304.2, None, None),
        ("WORLD", "2022/2023", 302.4, None, -1.8),
        ("WORLD", "2023/2024", 316.3, None, 13.9),
        ("WORLD", "2024/2025", 288.3, None, -28.0),
        ("WORLD", "2025/2026", 277.7, None, -10.6),
        # China
        ("China", "2021/2022", 209.1, 69, None),
        ("China", "2022/2023", 206.0, None, -3.1),
        ("China", "2023/2024", 211.3, None, 5.3),
        ("China", "2024/2025", 198.2, None, -13.1),
        ("China", "2025/2026", 182.2, None, -16.0),
        # European Union
        ("European Union", "2021/2022", 11.4, 4, None),
        ("European Union", "2022/2023", 8.0, None, -3.4),
        ("European Union", "2023/2024", 7.3, None, -0.7),
        ("European Union", "2024/2025", 6.3, None, -1.0),
        ("European Union", "2025/2026", 6.0, None, -0.3),
        # India
        ("India", "2021/2022", 2.5, 1, None),
        ("India", "2022/2023", 3.2, None, 0.7),
        ("India", "2023/2024", 2.8, None, -0.4),
        ("India", "2024/2025", 3.0, None, 0.2),
        ("India", "2025/2026", 3.2, None, 0.2),
        # Russia
        ("Russia", "2021/2022", 1.5, 0, None),
        ("Russia", "2022/2023", 1.2, None, -0.3),
        ("Russia", "2023/2024", 1.0, None, -0.2),
        ("Russia", "2024/2025", 0.8, None, -0.2),
        ("Russia", "2025/2026", 0.9, None, 0.1),
        # United States
        ("United States", "2021/2022", 34.9, 11, None),
        ("United States", "2022/2023", 34.6, None, -0.3),
        ("United States", "2023/2024", 44.8, None, 10.2),
        ("United States", "2024/2025", 35.9, None, -8.9),
        ("United States", "2025/2026", 45.7, None, 9.8),
        # Australia
        ("Australia", "2021/2022", 0.3, 0, None),
        ("Australia", "2022/2023", 0.3, None, 0.0),
        ("Australia", "2023/2024", 0.2, None, -0.1),
        ("Australia", "2024/2025", 0.3, None, 0.1),
        ("Australia", "2025/2026", 0.3, None, 0.0),
        # Canada
        ("Canada", "2021/2022", 2.1, 1, None),
        ("Canada", "2022/2023", 1.8, None, -0.3),
        ("Canada", "2023/2024", 2.0, None, 0.2),
        ("Canada", "2024/2025", 1.8, None, -0.2),
        ("Canada", "2025/2026", 1.9, None, 0.1),
    ]

    for country, year, value, pct, change in stocks_data:
        status = get_status(year)
        cursor.execute(
            """
            INSERT OR IGNORE INTO corn_stocks 
            (country, year, stock_value, percentage_world, change_value, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (country, year, value, pct, change, status),
        )

    print(f"✅ Inserted {len(stocks_data)} stocks records")


def insert_su_ratio_data(cursor):
    """Insert corn stock-to-use ratio data"""
    su_ratio_data = [
        # WORLD data
        ("WORLD", "2021/2022", 25.1, None),
        ("WORLD", "2022/2023", 25.2, 0.1),
        ("WORLD", "2023/2024", 25.7, 0.5),
        ("WORLD", "2024/2025", 23.0, -2.7),
        ("WORLD", "2025/2026", 21.9, -1.1),
        # China
        ("China", "2021/2022", 77.5, None),
        ("China", "2022/2023", 74.3, -3.2),
        ("China", "2023/2024", 73.8, -0.5),
        ("China", "2024/2025", 67.0, -6.8),
        ("China", "2025/2026", 61.9, -5.1),
        # European Union
        ("European Union", "2021/2022", 13.8, None),
        ("European Union", "2022/2023", 10.3, -3.5),
        ("European Union", "2023/2024", 9.8, -0.5),
        ("European Union", "2024/2025", 8.6, -1.2),
        ("European Union", "2025/2026", 8.2, -0.4),
        # India
        ("India", "2021/2022", 7.6, None),
        ("India", "2022/2023", 9.2, 1.6),
        ("India", "2023/2024", 7.9, -1.3),
        ("India", "2024/2025", 8.1, 0.2),
        ("India", "2025/2026", 8.6, 0.5),
        # Russia
        ("Russia", "2021/2022", 11.5, None),
        ("Russia", "2022/2023", 9.1, -2.4),
        ("Russia", "2023/2024", 7.3, -1.8),
        ("Russia", "2024/2025", 6.5, -0.8),
        ("Russia", "2025/2026", 7.2, 0.7),
        # United States
        ("United States", "2021/2022", 9.4, None),
        ("United States", "2022/2023", 10.4, 1.0),
        ("United States", "2023/2024", 12.1, 1.7),
        ("United States", "2024/2025", 9.8, -2.3),
        ("United States", "2025/2026", 11.9, 2.1),
        # Australia
        ("Australia", "2021/2022", 33.3, None),
        ("Australia", "2022/2023", 37.5, 4.2),
        ("Australia", "2023/2024", 28.6, -8.9),
        ("Australia", "2024/2025", 37.5, 8.9),
        ("Australia", "2025/2026", 37.5, 0.0),
        # Canada
        ("Canada", "2021/2022", 18.8, None),
        ("Canada", "2022/2023", 16.7, -2.1),
        ("Canada", "2023/2024", 17.2, 0.5),
        ("Canada", "2024/2025", 15.5, -1.7),
        ("Canada", "2025/2026", 16.4, 0.9),
    ]

    for country, year, ratio, change in su_ratio_data:
        status = get_status(year)
        category = get_su_ratio_category(ratio)
        cursor.execute(
            """
            INSERT OR IGNORE INTO corn_su_ratio 
            (country, year, su_ratio, change_value, category, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (country, year, ratio, change, category, status),
        )

    print(f"✅ Inserted {len(su_ratio_data)} S/U ratio records")


def insert_acreage_data(cursor):
    """Insert corn acreage data"""
    acreage_data = [
        # WORLD data
        ("WORLD", "2021/2022", 205.1, None, None),
        ("WORLD", "2022/2023", 202.2, None, -2.9),
        ("WORLD", "2023/2024", 206.5, None, 4.3),
        ("WORLD", "2024/2025", 203.5, None, -3.0),
        ("WORLD", "2025/2026", 204.0, None, 0.5),
        # China
        ("China", "2021/2022", 41.3, 20, None),
        ("China", "2022/2023", 43.1, None, 1.8),
        ("China", "2023/2024", 44.2, None, 1.1),
        ("China", "2024/2025", 44.7, None, 0.5),
        ("China", "2025/2026", 44.8, None, 0.1),
        # European Union
        ("European Union", "2021/2022", 8.5, 4, None),
        ("European Union", "2022/2023", 8.9, None, 0.4),
        ("European Union", "2023/2024", 8.3, None, -0.6),
        ("European Union", "2024/2025", 8.7, None, 0.4),
        ("European Union", "2025/2026", 8.8, None, 0.1),
        # India
        ("India", "2021/2022", 10.2, 5, None),
        ("India", "2022/2023", 10.7, None, 0.5),
        ("India", "2023/2024", 11.2, None, 0.5),
        ("India", "2024/2025", 11.2, None, 0.0),
        ("India", "2025/2026", 11.3, None, 0.1),
        # Russia
        ("Russia", "2021/2022", 2.6, 1, None),
        ("Russia", "2022/2023", 2.6, None, 0.0),
        ("Russia", "2023/2024", 2.4, None, -0.2),
        ("Russia", "2024/2025", 2.7, None, 0.3),
        ("Russia", "2025/2026", 2.7, None, 0.0),
        # United States
        ("United States", "2021/2022", 35.4, 17, None),
        ("United States", "2022/2023", 31.9, None, -3.5),
        ("United States", "2023/2024", 35.0, None, 3.1),
        ("United States", "2024/2025", 33.6, None, -1.4),
        ("United States", "2025/2026", 38.1, None, 4.5),
        # Australia
        ("Australia", "2021/2022", 0.08, 0, None),
        ("Australia", "2022/2023", 0.10, None, 0.02),
        ("Australia", "2023/2024", 0.09, None, -0.01),
        ("Australia", "2024/2025", 0.10, None, 0.01),
        ("Australia", "2025/2026", 0.10, None, 0.0),
        # Canada
        ("Canada", "2021/2022", 1.5, 1, None),
        ("Canada", "2022/2023", 1.4, None, -0.1),
        ("Canada", "2023/2024", 1.5, None, 0.1),
        ("Canada", "2024/2025", 1.5, None, 0.0),
        ("Canada", "2025/2026", 1.5, None, 0.0),
    ]

    for country, year, value, pct, change in acreage_data:
        status = get_status(year)
        cursor.execute(
            """
            INSERT OR IGNORE INTO corn_acreage 
            (country, year, acreage_value, percentage_world, change_value, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (country, year, value, pct, change, status),
        )

    print(f"✅ Inserted {len(acreage_data)} acreage records")


def insert_yield_data(cursor):
    """Insert corn yield data"""
    yield_data = [
        # WORLD data
        ("WORLD", "2021/2022", 5.92, None),
        ("WORLD", "2022/2023", 5.76, -0.16),
        ("WORLD", "2023/2024", 5.95, 0.19),
        ("WORLD", "2024/2025", 5.97, 0.02),
        ("WORLD", "2025/2026", 6.20, 0.23),
        # China
        ("China", "2021/2022", 6.60, None),
        ("China", "2022/2023", 6.44, -0.16),
        ("China", "2023/2024", 6.53, 0.09),
        ("China", "2024/2025", 6.59, 0.06),
        ("China", "2025/2026", 6.58, -0.01),
        # European Union
        ("European Union", "2021/2022", 7.87, None),
        ("European Union", "2022/2023", 5.92, -1.95),
        ("European Union", "2023/2024", 7.48, 1.56),
        ("European Union", "2024/2025", 6.81, -0.67),
        ("European Union", "2025/2026", 6.82, 0.01),
        # India
        ("India", "2021/2022", 3.29, None),
        ("India", "2022/2023", 3.54, 0.25),
        ("India", "2023/2024", 3.35, -0.19),
        ("India", "2024/2025", 3.57, 0.22),
        ("India", "2025/2026", 3.58, 0.01),
        # Russia
        ("Russia", "2021/2022", 5.77, None),
        ("Russia", "2022/2023", 6.00, 0.23),
        ("Russia", "2023/2024", 6.92, 0.92),
        ("Russia", "2024/2025", 5.19, -1.73),
        ("Russia", "2025/2026", 5.37, 0.18),
        # United States
        ("United States", "2021/2022", 10.84, None),
        ("United States", "2022/2023", 10.89, 0.05),
        ("United States", "2023/2024", 11.13, 0.24),
        ("United States", "2024/2025", 11.26, 0.13),
        ("United States", "2025/2026", 11.38, 0.12),
        # Australia
        ("Australia", "2021/2022", 23.75, None),
        ("Australia", "2022/2023", 18.00, -5.75),
        ("Australia", "2023/2024", 15.56, -2.44),
        ("Australia", "2024/2025", 17.00, 1.44),
        ("Australia", "2025/2026", 18.00, 1.00),
        # Canada
        ("Canada", "2021/2022", 9.73, None),
        ("Canada", "2022/2023", 10.07, 0.34),
        ("Canada", "2023/2024", 10.15, 0.08),
        ("Canada", "2024/2025", 10.59, 0.44),
        ("Canada", "2025/2026", 10.33, -0.26),
    ]

    for country, year, value, change in yield_data:
        status = get_status(year)
        category = get_yield_category(value)
        change_pct = (
            (change / (value - change) * 100)
            if change and (value - change) > 0
            else None
        )

        cursor.execute(
            """
            INSERT OR IGNORE INTO corn_yield 
            (country, year, yield_value, change_value, change_percentage, yield_category, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (country, year, value, change, change_pct, category, status),
        )

    print(f"✅ Inserted {len(yield_data)} yield records")


def insert_world_demand_data(cursor):
    """Insert corn world demand data"""
    demand_data = [
        # Food category
        ("Food", "2021/2022", 142.0, 12, None, None, "actual"),
        ("Food", "2022/2023", 145.0, None, 3.0, 2.11, "actual"),
        ("Food", "2023/2024", 147.0, None, 2.0, 1.38, "actual"),
        ("Food", "2024/2025", 150.0, None, 3.0, 2.04, "estimate"),
        ("Food", "2025/2026", 152.0, None, 2.0, 1.33, "projection"),
        # Feed category
        ("Feed", "2021/2022", 725.0, 62, None, None, "actual"),
        ("Feed", "2022/2023", 710.0, None, -15.0, -2.07, "actual"),
        ("Feed", "2023/2024", 742.0, None, 32.0, 4.51, "actual"),
        ("Feed", "2024/2025", 747.0, None, 5.0, 0.67, "estimate"),
        ("Feed", "2025/2026", 767.0, None, 20.0, 2.68, "projection"),
        # Industrial category
        ("Industrial", "2021/2022", 285.0, 24, None, None, "actual"),
        ("Industrial", "2022/2023", 290.0, None, 5.0, 1.75, "actual"),
        ("Industrial", "2023/2024", 298.0, None, 8.0, 2.76, "actual"),
        ("Industrial", "2024/2025", 305.0, None, 7.0, 2.35, "estimate"),
        ("Industrial", "2025/2026", 315.0, None, 10.0, 3.28, "projection"),
        # Seed category
        ("Seed", "2021/2022", 20.0, 2, None, None, "actual"),
        ("Seed", "2022/2023", 20.0, None, 0.0, 0.00, "actual"),
        ("Seed", "2023/2024", 20.5, None, 0.5, 2.50, "actual"),
        ("Seed", "2024/2025", 20.5, None, 0.0, 0.00, "estimate"),
        ("Seed", "2025/2026", 21.0, None, 0.5, 2.44, "projection"),
        # Other category
        ("Other", "2021/2022", 7.0, 1, None, None, "actual"),
        ("Other", "2022/2023", 7.5, None, 0.5, 7.14, "actual"),
        ("Other", "2023/2024", 8.0, None, 0.5, 6.67, "actual"),
        ("Other", "2024/2025", 8.0, None, 0.0, 0.00, "estimate"),
        ("Other", "2025/2026", 8.5, None, 0.5, 6.25, "projection"),
        # Total Consumption
        ("Total Consumption", "2021/2022", 1179.0, None, None, None, "actual"),
        ("Total Consumption", "2022/2023", 1172.5, None, -6.5, -0.55, "actual"),
        ("Total Consumption", "2023/2024", 1215.5, None, 43.0, 3.67, "actual"),
        ("Total Consumption", "2024/2025", 1230.5, None, 15.0, 1.23, "estimate"),
        ("Total Consumption", "2025/2026", 1263.5, None, 33.0, 2.68, "projection"),
    ]

    for category, year, value, pct_total, change, change_pct, status in demand_data:
        cursor.execute(
            """
            INSERT OR IGNORE INTO corn_world_demand 
            (category, year, demand_value, percentage_total, change_value, 
             change_percentage, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (category, year, value, pct_total, change, change_pct, status),
        )

    print(f"✅ Inserted {len(demand_data)} world demand records")


def insert_metadata(cursor):
    """Insert metadata"""
    metadata = [
        ("production_last_updated", datetime.now().strftime("%d %b'%y")),
        ("production_next_update", "17 Aug'25"),
        ("export_last_updated", datetime.now().strftime("%d %b'%y")),
        ("export_next_update", "17 Aug'25"),
        ("import_last_updated", datetime.now().strftime("%d %b'%y")),
        ("import_next_update", "17 Aug'25"),
        ("stocks_last_updated", datetime.now().strftime("%d %b'%y")),
        ("stocks_next_update", "17 Aug'25"),
        ("su_ratio_last_updated", datetime.now().strftime("%d %b'%y")),
        ("su_ratio_next_update", "17 Aug'25"),
        ("acreage_last_updated", datetime.now().strftime("%d %b'%y")),
        ("acreage_next_update", "17 Aug'25"),
        ("yield_last_updated", datetime.now().strftime("%d %b'%y")),
        ("yield_next_update", "17 Aug'25"),
        ("world_demand_last_updated", datetime.now().strftime("%d %b'%y")),
        ("world_demand_next_update", "17 Aug'25"),
        ("database_version", "1.0"),
        ("created_date", datetime.now().isoformat()),
        (
            "data_source",
            "IGC, USDA, and various national agricultural statistics agencies (July 2025)",
        ),
        # Display years configuration
        ("display_years", "2022/2023,2023/2024,2024/2025,2025/2026"),
        ("production_display_years", "2022/2023,2023/2024,2024/2025,2025/2026"),
        ("export_display_years", "2022/2023,2023/2024,2024/2025,2025/2026"),
        ("import_display_years", "2022/2023,2023/2024,2024/2025,2025/2026"),
        ("stocks_display_years", "2022/2023,2023/2024,2024/2025,2025/2026"),
        ("su_ratio_display_years", "2022/2023,2023/2024,2024/2025,2025/2026"),
        ("acreage_display_years", "2022/2023,2023/2024,2024/2025,2025/2026"),
        ("yield_display_years", "2022/2023,2023/2024,2024/2025,2025/2026"),
        ("world_demand_display_years", "2022/2023,2023/2024,2024/2025,2025/2026"),
        # Year status configuration
        (
            "year_status",
            '{"2022/2023": "actual", "2023/2024": "actual", "2024/2025": "estimate", "2025/2026": "projection"}',
        ),
        (
            "production_year_status",
            '{"2022/2023": "actual", "2023/2024": "actual", "2024/2025": "estimate", "2025/2026": "projection"}',
        ),
        (
            "export_year_status",
            '{"2022/2023": "actual", "2023/2024": "actual", "2024/2025": "estimate", "2025/2026": "projection"}',
        ),
        (
            "import_year_status",
            '{"2022/2023": "actual", "2023/2024": "actual", "2024/2025": "estimate", "2025/2026": "projection"}',
        ),
        (
            "stocks_year_status",
            '{"2022/2023": "actual", "2023/2024": "actual", "2024/2025": "estimate", "2025/2026": "projection"}',
        ),
        (
            "su_ratio_year_status",
            '{"2022/2023": "actual", "2023/2024": "actual", "2024/2025": "estimate", "2025/2026": "projection"}',
        ),
        (
            "acreage_year_status",
            '{"2022/2023": "actual", "2023/2024": "actual", "2024/2025": "estimate", "2025/2026": "projection"}',
        ),
        (
            "yield_year_status",
            '{"2022/2023": "actual", "2023/2024": "actual", "2024/2025": "estimate", "2025/2026": "projection"}',
        ),
        (
            "world_demand_year_status",
            '{"2022/2023": "actual", "2023/2024": "actual", "2024/2025": "estimate", "2025/2026": "projection"}',
        ),
    ]

    for key, value in metadata:
        cursor.execute(
            """
            INSERT OR IGNORE INTO metadata (key, value)
            VALUES (?, ?)
        """,
            (key, value),
        )

    print(f"✅ Inserted {len(metadata)} metadata entries")


def verify_database(db_path):
    """Verify the database was created correctly"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\n🔍 Verifying database...")

    # Check all tables
    tables = [
        "corn_production",
        "corn_exports",
        "corn_imports",
        "corn_stocks",
        "corn_su_ratio",
        "corn_acreage",
        "corn_yield",
        "corn_world_demand",
    ]

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]

        # Handle corn_world_demand differently as it uses 'category' instead of 'country'
        if table == "corn_world_demand":
            cursor.execute(f"SELECT COUNT(DISTINCT category) FROM {table}")
            categories = cursor.fetchone()[0]

            cursor.execute(f"SELECT COUNT(DISTINCT year) FROM {table}")
            years = cursor.fetchone()[0]

            print(f"\n📊 {table}:")
            print(f"   - Total records: {count}")
            print(f"   - Categories: {categories}")
            print(f"   - Years: {years}")
        else:
            cursor.execute(
                f"SELECT COUNT(DISTINCT country) FROM {table} WHERE country != 'WORLD' AND country != 'World'"
            )
            countries = cursor.fetchone()[0]

            cursor.execute(f"SELECT COUNT(DISTINCT year) FROM {table}")
            years = cursor.fetchone()[0]

            print(f"\n📊 {table}:")
            print(f"   - Total records: {count}")
            print(f"   - Countries: {countries}")
            print(f"   - Years: {years}")

    # Show sample data from production table
    print("\n📈 Sample Production Data (2025/2026):")
    cursor.execute(
        """
        SELECT country, production_value, change_value, status 
        FROM corn_production 
        WHERE year = '2025/2026' 
        ORDER BY production_value DESC 
        LIMIT 5
    """
    )

    for row in cursor.fetchall():
        country, value, change, status = row
        change_str = f"({change:+.1f})" if change else ""
        print(f"   {country}: {value:.1f} Mt {change_str} [{status}]")

    conn.close()


if __name__ == "__main__":
    create_database()
