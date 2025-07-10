#!/usr/bin/env python3
"""
One-time script to refresh wheat production data from monitoring dashboard Excel
Place this script in: mcp-bot-ppf/client/database_setup/
"""

import sqlite3
import pandas as pd
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def refresh_production_from_monitoring_excel(excel_path, db_path="wheat_production.db"):
    """Refresh wheat production data from monitoring dashboard Excel file"""

    print(f"\n📊 Refreshing data from: {excel_path}")

    # Read the Excel file - adjust sheet name based on your file
    try:
        # Try different possible sheet names
        possible_sheets = [
            "supply_demand",
            "Supply & Demand",
            "Global Wheat Production",
            "Sheet1",
        ]
        df = None

        for sheet in possible_sheets:
            try:
                df = pd.read_excel(excel_path, sheet_name=sheet, header=None)
                print(f"✅ Successfully read sheet: {sheet}")
                break
            except:
                continue

        if df is None:
            # List available sheets
            xl_file = pd.ExcelFile(excel_path)
            print(f"Available sheets: {xl_file.sheet_names}")
            sheet = input("Enter the sheet name containing wheat production data: ")
            df = pd.read_excel(excel_path, sheet_name=sheet, header=None)

    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        return False

    # Define allowed countries
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

    # Find the row with "Global Wheat Production" or similar header
    production_start_row = None
    for idx, row in df.iterrows():
        row_str = " ".join([str(cell) for cell in row if pd.notna(cell)])
        if (
            "wheat production" in row_str.lower()
            or "global production" in row_str.lower()
        ):
            production_start_row = idx
            break

    if production_start_row is None:
        print("❌ Could not find wheat production section")
        print("Searching for country names instead...")

        # Alternative: Look for WORLD or China
        for idx, row in df.iterrows():
            row_str = " ".join([str(cell) for cell in row if pd.notna(cell)])
            if "WORLD" in row_str or "China" in row_str:
                production_start_row = idx - 2  # Assume header is 2 rows above
                break

    if production_start_row is None:
        print("❌ Could not locate data section")
        return False

    print(f"✅ Found production data starting around row {production_start_row}")

    # Find the header row with years
    header_row = None
    for idx in range(
        max(0, production_start_row - 2), min(production_start_row + 10, len(df))
    ):
        row = df.iloc[idx]
        year_pattern_count = sum(
            1
            for cell in row
            if pd.notna(cell) and "/" in str(cell) and len(str(cell).split("/")) == 2
        )
        if year_pattern_count >= 3:
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
        records_updated = 0

        for idx in range(data_start_row, min(data_start_row + 50, len(df))):
            row = df.iloc[idx]

            # Get country name
            country = None
            for col in range(4):  # Check first 4 columns
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
                production_value, change_value = parse_value_with_change(cell_value)

                if production_value is None:
                    continue

                # Check if record exists
                cursor.execute(
                    """
                    SELECT production_value, change_value 
                    FROM wheat_production 
                    WHERE country = ? AND year = ?
                """,
                    (country, year),
                )

                existing = cursor.fetchone()

                if existing:
                    old_value, old_change = existing
                    # Only update if values are different
                    if abs(old_value - production_value) > 0.01 or (
                        change_value and abs((old_change or 0) - change_value) > 0.01
                    ):
                        cursor.execute(
                            """
                            UPDATE wheat_production 
                            SET production_value = ?, change_value = ?, updated_at = ?
                            WHERE country = ? AND year = ?
                        """,
                            (
                                production_value,
                                change_value,
                                datetime.now().isoformat(),
                                country,
                                year,
                            ),
                        )

                        print(
                            f"  📝 Updated {year}: {old_value:.1f} → {production_value:.1f} Mt"
                        )
                        records_updated += 1
                    else:
                        print(f"  ✓ {year}: {production_value:.1f} Mt (no change)")
                else:
                    # Determine status based on year
                    if year in ["2021/2022", "2022/2023", "2023/2024"]:
                        status = "act"
                    elif year == "2024/2025":
                        status = "estimate"
                    elif year == "2025/2026":
                        status = "projection"
                    else:
                        status = "act"

                    # Insert new record
                    cursor.execute(
                        """
                        INSERT INTO wheat_production 
                        (country, year, production_value, percentage_world, change_value, status, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            country,
                            year,
                            production_value,
                            None,  # percentage_world will be calculated separately
                            change_value,
                            status,
                            datetime.now().isoformat(),
                            datetime.now().isoformat(),
                        ),
                    )

                    print(f"  ➕ Added {year}: {production_value:.1f} Mt")
                    records_updated += 1

        # Recalculate percentage_world for all countries
        print("\n📊 Recalculating percentage of world...")

        # Get all years from the data
        cursor.execute("SELECT DISTINCT year FROM wheat_production ORDER BY year")
        all_years = [row[0] for row in cursor.fetchall()]

        for year in all_years:
            # Get WORLD total for this year
            cursor.execute(
                """
                SELECT production_value 
                FROM wheat_production 
                WHERE country = 'WORLD' AND year = ?
            """,
                (year,),
            )

            world_result = cursor.fetchone()
            if world_result and world_result[0] > 0:
                world_total = world_result[0]

                # Update percentages for all countries except WORLD
                cursor.execute(
                    """
                    UPDATE wheat_production 
                    SET percentage_world = ROUND((production_value / ?) * 100, 1)
                    WHERE year = ? AND country != 'WORLD'
                """,
                    (world_total, year),
                )

                print(
                    f"  ✅ Updated percentages for {year} (World total: {world_total:.1f} Mt)"
                )

        # Update metadata
        cursor.execute(
            """
            INSERT OR REPLACE INTO metadata (key, value, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """,
            (
                "production_last_refreshed",
                datetime.now().strftime("%d %b'%y %H:%M"),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            ),
        )

        conn.commit()
        print(f"\n✅ Successfully updated {records_updated} records!")

        # Show summary
        cursor.execute(
            """
            SELECT year, COUNT(*), AVG(production_value) 
            FROM wheat_production 
            WHERE country != 'WORLD'
            GROUP BY year
            ORDER BY year
        """
        )

        print("\n📊 Data Summary:")
        print("Year       | Countries | Avg Production")
        print("-----------|-----------|---------------")
        for year, count, avg_prod in cursor.fetchall():
            print(f"{year} |     {count}     | {avg_prod:.1f} Mt")

        return True

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error updating data: {e}")
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


def show_current_data(db_path="wheat_production.db"):
    """Show current data state before refresh"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\n📊 Current Database State:")
    print("=" * 60)

    # Show WORLD data
    cursor.execute(
        """
        SELECT year, production_value, change_value, status 
        FROM wheat_production 
        WHERE country = 'WORLD'
        ORDER BY year
    """
    )

    print("\n🌍 WORLD Production:")
    for row in cursor.fetchall():
        year, value, change, status = row
        change_str = f"({change:.1f})" if change else ""
        print(f"  {year}: {value:.1f} Mt {change_str} [{status}]")

    # Show last update time
    cursor.execute("SELECT value FROM metadata WHERE key = 'production_last_refreshed'")
    result = cursor.fetchone()
    if result:
        print(f"\n⏰ Last refreshed: {result[0]}")

    conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Refresh wheat production data from monitoring dashboard Excel"
    )
    parser.add_argument(
        "excel_path", help="Path to the monitoring dashboard Excel file"
    )
    parser.add_argument(
        "--db-path", default="wheat_production.db", help="Path to database file"
    )
    parser.add_argument(
        "--show-current", action="store_true", help="Show current data before refresh"
    )

    args = parser.parse_args()

    # Check if Excel file exists
    if not os.path.exists(args.excel_path):
        print(f"❌ Excel file not found: {args.excel_path}")
        sys.exit(1)

    # Show current state if requested
    if args.show_current:
        show_current_data(args.db_path)

    # Refresh data
    print("\n🔄 Starting data refresh...")
    success = refresh_production_from_monitoring_excel(args.excel_path, args.db_path)

    if success:
        print("\n✅ Refresh completed successfully!")
        # Show updated state
        show_current_data(args.db_path)
    else:
        print("\n❌ Refresh failed!")
        sys.exit(1)
