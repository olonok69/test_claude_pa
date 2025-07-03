# Wheat Market Analysis Dashboard

A comprehensive Streamlit application for managing and analyzing wheat production and export data across major global markets.

## Features

### 🌾 Global Wheat Production Dashboard
- Track production data for major wheat-producing countries
- View historical trends from 2021/2022 to 2024/2025
- Edit and update 2024/2025 projections
- Visualize production trends with interactive charts
- Export/import data in JSON and CSV formats

### 📦 Wheat Exports Dashboard
- Monitor export volumes from major exporting countries
- Analyze market share and export trends
- Update export projections for 2024/2025
- Compare changes across different periods
- Visualize export data with time series and pie charts

## Project Structure

```
wheat/
├── app.py                    # Main application entry point
├── pages/
│   ├── 1_wheat_production.py # Global production dashboard
│   └── 2_wheat_exports.py    # Exports dashboard
├── helpers/
│   ├── database_helper.py    # Database operations
│   └── common_functions.py   # Shared utility functions
├── database_setup.py         # Database initialization script
├── wheat_production.db       # SQLite database (created after setup)
├── requirements.txt          # Python dependencies
└── README.md                # This file
```

## Installation

1. Clone or download this repository

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```bash
python database_setup.py
```

4. Run the application:
```bash
streamlit run app.py
```

## Database Schema

The application uses SQLite with the following tables:

### wheat_production
- Stores global wheat production data by country and year
- Includes production values, percentage of world production, and year-over-year changes

### wheat_exports
- Stores wheat export data for major exporting countries
- Includes export volumes, market share percentages, and changes

### metadata
- Stores application metadata like last update dates

### audit_log
- Tracks all data modifications for transparency

## Usage

### Navigating the Dashboard

1. **Home Page**: Overview of available dashboards and key metrics
2. **Production Dashboard**: Access via sidebar or home page button
3. **Exports Dashboard**: Access via sidebar or home page button

### Editing Data

1. Navigate to the "Edit Projections" tab in either dashboard
2. Update values for 2024/2025 projections
3. Click "Update Projections" to save changes
4. Changes are automatically saved to the database

### Exporting Data

1. Go to the "Data Export" tab
2. Choose between JSON or CSV format
3. Click the download button
4. Data includes all current values and metadata

### Importing Data

1. Go to the "Data Export" tab
2. Upload a previously exported JSON file
3. Click "Import Data" to load the values

## Data Sources

The initial data represents wheat production and export statistics from major global markets, with:
- Historical data (2021/2022 - 2022/2023): Actual values
- Current year (2023/2024): Estimates
- Future year (2024/2025): Projections

## Future Enhancements

Additional dashboards planned for:
- Wheat imports by major importing countries
- Supply & demand balance sheets
- Price monitoring and forecasting
- Regional analysis and market insights
- Inventory levels and stock-to-use ratios

## Technical Details

- **Framework**: Streamlit 1.46.1+
- **Database**: SQLite
- **Visualization**: Plotly
- **Data Processing**: Pandas

## License

This project is provided as-is for educational and analytical purposes.