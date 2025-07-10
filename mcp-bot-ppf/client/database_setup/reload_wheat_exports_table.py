#!/usr/bin/env python3
"""
One-time script to delete and reload wheat_exports table from Excel file
Place this script in: mcp-bot-ppf/client/database_setup/
"""

import sqlite3
import pandas as pd
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def delete_and_recreate_wheat_exports_table(db_path="wheat_production.db"):
    """Delete the existing wheat_exports table and recreate it"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("🗑️ Dropping existing wheat_exports table...")
        cursor.execute("DROP TABLE IF EXISTS wheat_exports")

        print("🔨 Creating new wheat_exports table...")
        cursor.execute(
            """
            CREATE TABLE wheat_exports (
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

        conn.commit()
        print("✅ Table recreated successfully!")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error recreating table: {e}")
        raise
    finally:
        conn.close()


def load_wheat_exports_from_excel(excel_path, db_path="wheat_production.db"):
    """Load wheat exports data from Excel file"""

    print(f"\n📊 Loading data from: {excel_path}")

    # Read the Excel file
    try:
        # Read the specific sheet
        df = pd.read_excel(excel_path, sheet_name="Supply & Demand", header=None)
        print(f"✅ Successfully read Excel file")
    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        return False

    # Define allowed countries for exports
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

    # Find the row with "Export (WHEAT)" header
    export_start_row = None
    for idx, row in df.iterrows():
        row_str = " ".join([str(cell) for cell in row if pd.notna(cell)])
        if "Export (WHEAT)" in row_str or "Exports (WHEAT)" in row_str:
            export_start_row = idx
            break

    if export_start_row is None:
        print("❌ Could not find 'Export (WHEAT)' section")
        return False

    print(f"✅ Found 'Export (WHEAT)' at row {export_start_row}")

    # Find the header row with years (should be a few rows after Export header)
    header_row = None
    for idx in range(export_start_row + 1, min(export_start_row + 10, len(df))):
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

    # Extract years from header
    years_row = df.iloc[header_row]
    year_columns = {}

    for col_idx, cell in enumerate(years_row):
        if pd.notna(cell) and "/" in str(cell):
            year = str(cell).strip()
            if len(year.split("/")) == 2:
                year_columns[col_idx] = year

    print(f"✅ Found years: {list(year_columns.values())}")

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Process data rows
        data_start_row = header_row + 1
        records_inserted = 0

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

            # Process each year
            for col_idx, year in year_columns.items():
                cell_value = row.iloc[col_idx] if col_idx < len(row) else None

                if pd.isna(cell_value):
                    continue

                # Parse value and change
                export_value, change_value = parse_value_with_change(cell_value)

                if export_value is None:
                    continue

                # Determine status based on year
                if year in ["2021/2022", "2022/2023", "2023/2024"]:
                    status = "actual"
                elif year == "2024/2025":
                    status = "estimate"
                elif year == "2025/2026":
                    status = "projection"
                else:
                    status = "actual"

                # Calculate percentage of world if this is the first year
                percentage_world = None
                if year == "2021/2022" and country != "TOTAL MAJOR EXPORTERS":
                    # Find TOTAL MAJOR EXPORTERS value for this year
                    for total_idx in range(
                        data_start_row, min(data_start_row + 50, len(df))
                    ):
                        total_row = df.iloc[total_idx]
                        total_country = None
                        for col in range(3):
                            if pd.notna(total_row.iloc[col]) and isinstance(
                                total_row.iloc[col], str
                            ):
                                if (
                                    "TOTAL MAJOR EXPORTERS"
                                    in total_row.iloc[col].strip()
                                ):
                                    total_country = "TOTAL MAJOR EXPORTERS"
                                    break

                        if total_country == "TOTAL MAJOR EXPORTERS":
                            total_cell = (
                                total_row.iloc[col_idx]
                                if col_idx < len(total_row)
                                else None
                            )
                            if pd.notna(total_cell):
                                total_value, _ = parse_value_with_change(total_cell)
                                if total_value and total_value > 0:
                                    percentage_world = (
                                        export_value / total_value
                                    ) * 100
                            break

                # Insert into database
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO wheat_exports 
                    (country, year, export_value, percentage_world, change_value, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        country,
                        year,
                        export_value,
                        percentage_world,
                        change_value,
                        status,
                        datetime.now().isoformat(),
                        datetime.now().isoformat(),
                    ),
                )

                print(f"  ✅ {year}: {export_value:.1f} Mt (status: {status})")
                records_inserted += 1

        # Recalculate all percentage_world values to ensure accuracy
        print("\n📊 Recalculating percentage of world for all records...")

        # Get all years
        cursor.execute("SELECT DISTINCT year FROM wheat_exports ORDER BY year")
        all_years = [row[0] for row in cursor.fetchall()]

        for year in all_years:
            # Get TOTAL MAJOR EXPORTERS for this year
            cursor.execute(
                """
                SELECT export_value 
                FROM wheat_exports 
                WHERE country = 'TOTAL MAJOR EXPORTERS' AND year = ?
            """,
                (year,),
            )

            total_result = cursor.fetchone()
            if total_result and total_result[0] > 0:
                total_exports = total_result[0]

                # Update percentages for all countries except TOTAL
                cursor.execute(
                    """
                    UPDATE wheat_exports 
                    SET percentage_world = ROUND((export_value / ?) * 100, 1)
                    WHERE year = ? AND country != 'TOTAL MAJOR EXPORTERS'
                """,
                    (total_exports, year),
                )

                print(
                    f"  ✅ Updated percentages for {year} (Total: {total_exports:.1f} Mt)"
                )

        # Update metadata
        cursor.execute(
            """
            INSERT OR REPLACE INTO metadata (key, value, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """,
            (
                "export_last_updated",
                datetime.now().strftime("%d %b'%y"),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            ),
        )

        # Update display years configuration
        cursor.execute(
            """
            INSERT OR REPLACE INTO metadata (key, value, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """,
            (
                "export_display_years",
                "2022/2023,2023/2024,2024/2025,2025/2026",
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            ),
        )

        conn.commit()
        print(f"\n✅ Successfully inserted {records_inserted} records!")

        # Show summary
        cursor.execute("SELECT COUNT(DISTINCT country) FROM wheat_exports")
        country_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT year) FROM wheat_exports")
        year_count = cursor.fetchone()[0]

        print(f"\n📊 Summary:")
        print(f"  - Countries: {country_count}")
        print(f"  - Years: {year_count}")
        print(f"  - Total records: {records_inserted}")

        return True

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error loading data: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        conn.close()


def parse_value_with_change(cell_value):
    """Parse a cell that might contain value and change in parentheses"""
    if pd.isna(cell_value):
        return None, None

    # Convert to string and clean
    cell_str = str(cell_value).strip()

    # Remove any commas
    cell_str = cell_str.replace(",", "")

    # Check if there's a parenthesis (indicating change value)
    if "(" in cell_str and ")" in cell_str:
        # Split by first parenthesis
        parts = cell_str.split("(")
        try:
            value = float(parts[0].strip())
            change_str = parts[1].replace(")", "").strip()
            # Handle negative values in parentheses
            if change_str.startswith("-"):
                change = float(change_str)
            else:
                change = -float(
                    change_str
                )  # Values in parentheses are typically negative
            return value, change
        except:
            return None, None
    else:
        # Just a simple value
        try:
            return float(cell_str), None
        except:
            return None, None


def verify_data(db_path="wheat_production.db"):
    """Verify the loaded data"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\n🔍 Verifying loaded data...")

    # Show sample data
    cursor.execute(
        """
        SELECT country, year, export_value, change_value, status 
        FROM wheat_exports 
        WHERE country IN ('Russia', 'United States', 'TOTAL MAJOR EXPORTERS')
        ORDER BY country, year
    """
    )

    print("\n📦 Sample Export Data:")
    for row in cursor.fetchall():
        country, year, value, change, status = row
        change_str = f"({change:.1f})" if change else ""
        print(f"  {country} - {year}: {value:.1f} Mt {change_str} [{status}]")

    # Show all countries
    cursor.execute("SELECT DISTINCT country FROM wheat_exports ORDER BY country")
    countries = [row[0] for row in cursor.fetchall()]
    print(f"\n📍 Countries in database: {', '.join(countries)}")

    conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Reload wheat exports table from Excel"
    )
    parser.add_argument(
        "excel_path",
        help="Path to the Excel file (Global Wheat Production exports.xlsx)",
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
        "⚠️  This will DELETE all existing wheat_exports data. Continue? (yes/no): "
    )
    if response.lower() != "yes":
        print("❌ Operation cancelled")
        sys.exit(0)

    delete_and_recreate_wheat_exports_table(args.db_path)

    # Step 2: Load data from Excel
    success = load_wheat_exports_from_excel(args.excel_path, args.db_path)

    if success:
        # Step 3: Verify
        verify_data(args.db_path)
        print("\n✅ All done!")
    else:
        print("\n❌ Failed to load data")
        sys.exit(1)
