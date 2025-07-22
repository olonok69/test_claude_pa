#!/usr/bin/env python3
"""
One-time script to create and populate wheat_world_demand table
This script creates the table structure and loads initial data for world wheat demand
Place this script in: mcp-bot-ppf/client/database_setup/
"""

import sqlite3
import pandas as pd
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def create_world_demand_table(db_path="wheat_production.db"):
    """Create the wheat_world_demand table"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("🗑️ Dropping existing wheat_world_demand table if exists...")
        cursor.execute("DROP TABLE IF EXISTS wheat_world_demand")

        print("🔨 Creating new wheat_world_demand table...")
        cursor.execute(
            """
            CREATE TABLE wheat_world_demand (
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

        conn.commit()
        print("✅ Table created successfully!")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error creating table: {e}")
        raise
    finally:
        conn.close()


def populate_world_demand_data(db_path="wheat_production.db"):
    """Populate the wheat_world_demand table with initial data"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Define the data based on the provided table
        demand_data = [
            # Food category
            ("Food", "2021/2022", 545.3, 70, None, None, "actual"),
            ("Food", "2022/2023", 549.7, None, 4.4, 0.81, "actual"),
            ("Food", "2023/2024", 557.5, None, 7.8, 1.42, "actual"),
            ("Food", "2024/2025", 563.2, None, 5.7, 1.02, "estimate"),
            ("Food", "2025/2026", 568.0, None, 4.8, 0.85, "projection"),
            # Feed category
            ("Feed", "2021/2022", 149.5, 19, None, None, "actual"),
            ("Feed", "2022/2023", 148.8, None, -0.7, -0.47, "actual"),
            ("Feed", "2023/2024", 154.7, None, 5.9, 3.97, "actual"),
            ("Feed", "2024/2025", 147.0, None, -7.7, -4.98, "estimate"),
            ("Feed", "2025/2026", 149.0, None, 2.0, 1.36, "projection"),
            # Industrial category
            ("Industrial", "2021/2022", 24.6, 3, None, None, "actual"),
            ("Industrial", "2022/2023", 25.5, None, 0.9, 3.66, "actual"),
            ("Industrial", "2023/2024", 27.1, None, 1.6, 6.27, "actual"),
            ("Industrial", "2024/2025", 27.5, None, 0.4, 1.48, "estimate"),
            ("Industrial", "2025/2026", 28.0, None, 0.5, 1.82, "projection"),
            # Seed category
            ("Seed", "2021/2022", 38.4, 5, None, None, "actual"),
            ("Seed", "2022/2023", 38.6, None, 0.2, 0.52, "actual"),
            ("Seed", "2023/2024", 38.5, None, -0.1, -0.26, "actual"),
            ("Seed", "2024/2025", 38.0, None, -0.5, -1.30, "estimate"),
            ("Seed", "2025/2026", 38.0, None, 0.0, 0.00, "projection"),
            # Other category
            ("Other", "2021/2022", 26.1, 3, None, None, "actual"),
            ("Other", "2022/2023", 31.7, None, 5.6, 21.46, "actual"),
            ("Other", "2023/2024", 29.0, None, -2.7, -8.52, "actual"),
            ("Other", "2024/2025", 27.6, None, -1.4, -4.83, "estimate"),
            ("Other", "2025/2026", 27.3, None, -0.3, -1.09, "projection"),
            # Total Consumption
            ("Total Consumption", "2021/2022", 783.9, None, None, None, "actual"),
            ("Total Consumption", "2022/2023", 794.3, None, 10.4, 1.33, "actual"),
            ("Total Consumption", "2023/2024", 806.8, None, 12.5, 1.57, "actual"),
            ("Total Consumption", "2024/2025", 803.3, None, -3.5, -0.43, "estimate"),
            ("Total Consumption", "2025/2026", 810.3, None, 7.0, 0.87, "projection"),
        ]

        # Insert data
        for data in demand_data:
            category, year, value, pct_total, change, change_pct, status = data

            cursor.execute(
                """
                INSERT INTO wheat_world_demand 
                (category, year, demand_value, percentage_total, change_value, 
                 change_percentage, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    category,
                    year,
                    value,
                    pct_total,
                    change,
                    change_pct,
                    status,
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                ),
            )

        # Update metadata
        cursor.execute(
            """
            INSERT OR REPLACE INTO metadata (key, value, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """,
            (
                "world_demand_last_updated",
                datetime.now().strftime("%d %b'%y"),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            ),
        )

        cursor.execute(
            """
            INSERT OR REPLACE INTO metadata (key, value, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """,
            (
                "world_demand_next_update",
                "17 Oct'24",
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            ),
        )

        # Add display years configuration
        cursor.execute(
            """
            INSERT OR REPLACE INTO metadata (key, value, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """,
            (
                "world_demand_display_years",
                "2022/2023,2023/2024,2024/2025,2025/2026",
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            ),
        )

        # Add year status configuration
        cursor.execute(
            """
            INSERT OR REPLACE INTO metadata (key, value, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """,
            (
                "world_demand_year_status",
                '{"2022/2023": "actual", "2023/2024": "actual", "2024/2025": "estimate", "2025/2026": "projection"}',
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            ),
        )

        conn.commit()
        print(f"✅ Successfully inserted {len(demand_data)} records!")

        # Verify data
        cursor.execute("SELECT COUNT(*) FROM wheat_world_demand")
        total_records = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT category) FROM wheat_world_demand")
        category_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT year) FROM wheat_world_demand")
        year_count = cursor.fetchone()[0]

        print(f"\n📊 Summary:")
        print(f"  - Total records: {total_records}")
        print(f"  - Categories: {category_count}")
        print(f"  - Years: {year_count}")

        return True

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error loading data: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        conn.close()


def verify_data(db_path="wheat_production.db"):
    """Verify the loaded data"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\n🔍 Verifying loaded data...")

    # Show sample data
    cursor.execute(
        """
        SELECT category, year, demand_value, change_value, status 
        FROM wheat_world_demand 
        WHERE year IN ('2024/2025', '2025/2026')
        ORDER BY category, year
    """
    )

    print("\n🌾 Sample World Demand Data:")
    for row in cursor.fetchall():
        category, year, value, change, status = row
        change_str = f"({change:+.1f})" if change else ""
        print(f"  {category} - {year}: {value:.1f} {change_str} [{status}]")

    # Show categories
    cursor.execute("SELECT DISTINCT category FROM wheat_world_demand ORDER BY category")
    categories = [row[0] for row in cursor.fetchall()]
    print(f"\n📍 Categories: {', '.join(categories)}")

    # Show years
    cursor.execute("SELECT DISTINCT year FROM wheat_world_demand ORDER BY year")
    years = [row[0] for row in cursor.fetchall()]
    print(f"\n📅 Years: {', '.join(years)}")

    conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Setup wheat world demand table")
    parser.add_argument(
        "--db-path", default="wheat_production.db", help="Path to database file"
    )

    args = parser.parse_args()

    # Check if database exists
    if not os.path.exists(args.db_path):
        print(f"❌ Database not found: {args.db_path}")
        print("Please ensure the database exists or run database_setup.py first")
        sys.exit(1)

    # Step 1: Create table
    print("Step 1: Creating wheat_world_demand table...")
    create_world_demand_table(args.db_path)

    # Step 2: Populate data
    print("\nStep 2: Populating data...")
    success = populate_world_demand_data(args.db_path)

    if success:
        # Step 3: Verify
        verify_data(args.db_path)
        print("\n✅ All done! World demand table is ready.")
    else:
        print("\n❌ Failed to setup world demand table")
        sys.exit(1)
