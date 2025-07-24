#!/usr/bin/env python3
"""
One-time script to delete and reload wheat_su_ratio table from Excel file
This version properly handles the 2025/2026 data and updates the year configuration
Place this script in: mcp-bot-ppf/client/database_setup/
"""

import sqlite3
import pandas as pd
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def delete_and_recreate_wheat_su_ratio_table(db_path="wheat_production.db"):
    """Delete the existing wheat_su_ratio table and recreate it"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("🗑️ Dropping existing wheat_su_ratio table...")
        cursor.execute("DROP TABLE IF EXISTS wheat_su_ratio")

        print("🔨 Creating new wheat_su_ratio table...")
        cursor.execute(
            """
            CREATE TABLE wheat_su_ratio (
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

        conn.commit()
        print("✅ Table recreated successfully!")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error recreating table: {e}")
        raise
    finally:
        conn.close()


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


def load_su_ratio_from_excel(excel_path, db_path="wheat_production.db"):
    """Load stock-to-use ratio data from Excel file including 2025/2026 data"""

    print(f"\n📊 Loading data from: {excel_path}")

    # Read the Excel file
    try:
        # Read the specific sheet
        df = pd.read_excel(excel_path, sheet_name="Supply & Demand", header=None)
        print(f"✅ Successfully read Excel file")
    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        return False

    # Define allowed countries for S/U ratio
    allowed_countries = [
        "WORLD",
        "China",
        "European Union",
        "India",
        "Russia",
        "United States",
        "Australia",
        "Canada",
    ]

    # Find the row with "Stock-to-Use Ratio" header
    su_ratio_start_row = None
    for idx, row in df.iterrows():
        row_str = " ".join([str(cell) for cell in row if pd.notna(cell)])
        if "Stock-to-Use Ratio" in row_str or "Stock to Use Ratio" in row_str:
            su_ratio_start_row = idx
            break

    if su_ratio_start_row is None:
        print("❌ Could not find 'Stock-to-Use Ratio' section")
        return False

    print(f"✅ Found 'Stock-to-Use Ratio' at row {su_ratio_start_row}")

    # Find the header row with years (should be a few rows after S/U Ratio header)
    header_row = None
    for idx in range(su_ratio_start_row + 1, min(su_ratio_start_row + 10, len(df))):
        row = df.iloc[idx]
        year_pattern_count = sum(
            1
            for cell in row
            if pd.notna(cell) and "/" in str(cell) and len(str(cell).split("/")) == 2
        )
        if year_pattern_count >= 4:
            header_row = idx
            break

    if header_row is None:
        print("❌ Could not find header row with years")
        return False

    # Extract years from header - INCLUDING 2025/2026
    years_row = df.iloc[header_row]
    year_columns = {}

    for col_idx, cell in enumerate(years_row):
        if pd.notna(cell) and "/" in str(cell):
            year = str(cell).strip()
            if len(year.split("/")) == 2:
                year_columns[col_idx] = year

    print(f"✅ Found years: {list(year_columns.values())}")

    # Verify 2025/2026 is included
    if "2025/2026" not in year_columns.values():
        print("⚠️ Warning: 2025/2026 not found in years. Checking for it...")
        # Sometimes the year might be in a different format or adjacent cell
        for col_idx in range(len(years_row)):
            cell_str = str(years_row.iloc[col_idx])
            if "2025" in cell_str and "2026" in cell_str:
                year_columns[col_idx] = "2025/2026"
                print(f"✅ Found 2025/2026 at column {col_idx}")
                break

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Process data rows
        data_start_row = header_row + 1
        records_inserted = 0

        # First pass - collect all data
        all_data = {}

        for idx in range(data_start_row, min(data_start_row + 50, len(df))):
            row = df.iloc[idx]

            # Get country name
            country = None
            for col in range(3):
                if pd.notna(row.iloc[col]) and isinstance(row.iloc[col], str):
                    country_candidate = row.iloc[col].strip()
                    # Handle European Union naming variations
                    if (
                        "European Union" in country_candidate
                        or "EU" in country_candidate
                    ):
                        country = "European Union"
                    else:
                        country = country_candidate
                    break

            if not country or country not in allowed_countries:
                continue

            print(f"\nProcessing {country}:")

            if country not in all_data:
                all_data[country] = {}

            # Process each year
            for col_idx, year in year_columns.items():
                cell_value = row.iloc[col_idx] if col_idx < len(row) else None

                if pd.isna(cell_value):
                    continue

                # Parse value - S/U ratios are percentages
                su_ratio = parse_su_ratio_value(cell_value)

                if su_ratio is None:
                    continue

                all_data[country][year] = su_ratio

                print(f"  - {year}: {su_ratio:.1f}%")

        # Calculate changes and insert data
        for country, data in all_data.items():
            # Sort years to ensure proper order
            sorted_years = sorted(year_columns.values(), key=lambda x: x.split("/")[0])

            for i, year in enumerate(sorted_years):
                if year not in data:
                    continue

                su_ratio = data[year]

                # Calculate change from previous year
                change_value = None
                if i > 0:
                    prev_year = sorted_years[i - 1]
                    if prev_year in data:
                        change_value = su_ratio - data[prev_year]

                # Determine status based on year - UPDATED FOR NEW CONFIGURATION
                if year in ["2021/2022", "2022/2023"]:
                    status = "actual"
                elif year == "2023/2024":
                    status = "actual"  # Changed from estimate to actual
                elif year == "2024/2025":
                    status = "estimate"
                elif year == "2025/2026":
                    status = "projection"
                else:
                    status = "actual"

                # Get category
                category = get_su_ratio_category(su_ratio)

                # Insert into database
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO wheat_su_ratio 
                    (country, year, su_ratio, change_value, category, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        country,
                        year,
                        su_ratio,
                        change_value,
                        category,
                        status,
                        datetime.now().isoformat(),
                        datetime.now().isoformat(),
                    ),
                )

                records_inserted += 1

        # Update metadata with NEW YEAR CONFIGURATION for 2025/2026
        cursor.execute(
            """
            INSERT OR REPLACE INTO metadata (key, value, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """,
            (
                "su_ratio_last_updated",
                datetime.now().strftime("%d %b'%y"),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            ),
        )

        # Update display years configuration to include 2025/2026
        cursor.execute(
            """
            INSERT OR REPLACE INTO metadata (key, value, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """,
            (
                "su_ratio_display_years",
                "2022/2023,2023/2024,2024/2025,2025/2026",
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            ),
        )

        # Update year status configuration
        cursor.execute(
            """
            INSERT OR REPLACE INTO metadata (key, value, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """,
            (
                "su_ratio_year_status",
                '{"2022/2023": "actual", "2023/2024": "actual", "2024/2025": "estimate", "2025/2026": "projection"}',
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            ),
        )

        conn.commit()
        print(f"\n✅ Successfully inserted {records_inserted} records!")

        # Show summary
        cursor.execute("SELECT COUNT(DISTINCT country) FROM wheat_su_ratio")
        country_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT year) FROM wheat_su_ratio")
        year_count = cursor.fetchone()[0]

        # Verify 2025/2026 data
        cursor.execute("SELECT COUNT(*) FROM wheat_su_ratio WHERE year = '2025/2026'")
        count_2025 = cursor.fetchone()[0]

        print(f"\n📊 Summary:")
        print(f"  - Countries: {country_count}")
        print(f"  - Years: {year_count}")
        print(f"  - Total records: {records_inserted}")
        print(f"  - 2025/2026 records: {count_2025}")

        return True

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error loading data: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        conn.close()


def parse_su_ratio_value(cell_value):
    """Parse a cell that contains S/U ratio value"""
    if pd.isna(cell_value):
        return None

    # Convert to string and clean
    cell_str = str(cell_value).strip()

    # Remove any % signs and commas
    cell_str = cell_str.replace("%", "").replace(",", "")

    # S/U ratios are typically percentages
    try:
        # If the value is already a percentage (e.g., 35.7)
        value = float(cell_str)

        # If the value seems too small (like 0.357), multiply by 100
        if value < 1:
            value = value * 100

        return value
    except:
        return None


def verify_data(db_path="wheat_production.db"):
    """Verify the loaded data including 2025/2026"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\n🔍 Verifying loaded data...")

    # Show sample data including 2025/2026
    cursor.execute(
        """
        SELECT country, year, su_ratio, change_value, category, status 
        FROM wheat_su_ratio 
        WHERE country IN ('WORLD', 'China', 'United States')
        AND year IN ('2023/2024', '2024/2025', '2025/2026')
        ORDER BY country, year
    """
    )

    print("\n📊 Sample S/U Ratio Data (including 2025/2026):")
    for row in cursor.fetchall():
        country, year, ratio, change, category, status = row
        change_str = f"({change:+.1f})" if change else ""
        print(
            f"  {country} - {year}: {ratio:.1f}% {change_str} [{category}] [{status}]"
        )

    # Show all countries
    cursor.execute("SELECT DISTINCT country FROM wheat_su_ratio ORDER BY country")
    countries = [row[0] for row in cursor.fetchall()]
    print(f"\n📍 Countries in database: {', '.join(countries)}")

    # Show all years
    cursor.execute("SELECT DISTINCT year FROM wheat_su_ratio ORDER BY year")
    years = [row[0] for row in cursor.fetchall()]
    print(f"\n📅 Years in database: {', '.join(years)}")

    # Show category distribution
    cursor.execute(
        """
        SELECT category, COUNT(*) as count 
        FROM wheat_su_ratio 
        WHERE year = '2025/2026'
        GROUP BY category
    """
    )
    print("\n📊 Category distribution for 2025/2026:")
    for row in cursor.fetchall():
        category, count = row
        print(f"  {category}: {count} countries")

    conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Reload wheat S/U ratio table from Excel"
    )
    parser.add_argument(
        "excel_path",
        help="Path to the Excel file (Global Wheat Ending Stocks_to_use_Ratio.xlsx)",
    )
    parser.add_argument(
        "--db-path", default="wheat_production.db", help="Path to database file"
    )

    args = parser.parse_args()

    # Check if Excel file exists
    if not os.path.exists(args.excel_path):
        print(f"❌ Excel file not found: {args.excel_path}")
        sys.exit(1)

    # Step 1: Delete and recreate table
    response = input(
        "⚠️  This will DELETE all existing wheat_su_ratio data. Continue? (yes/no): "
    )
    if response.lower() != "yes":
        print("❌ Operation cancelled")
        sys.exit(0)

    delete_and_recreate_wheat_su_ratio_table(args.db_path)

    # Step 2: Load data from Excel
    success = load_su_ratio_from_excel(args.excel_path, args.db_path)

    if success:
        # Step 3: Verify
        verify_data(args.db_path)
        print("\n✅ All done!")
    else:
        print("\n❌ Failed to load data")
        sys.exit(1)
