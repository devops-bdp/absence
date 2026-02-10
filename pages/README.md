# Pages Directory

This directory contains all the page files for the Streamlit multi-page application, similar to Next.js's `pages` directory structure.

## How It Works

Streamlit automatically detects files in the `pages/` directory and creates navigation for them. The file naming convention determines the page order and display name:

- **File naming**: `{number}_{icon}_{name}.py`
  - The number determines the order in the sidebar
  - The icon and name appear in the navigation menu
  - Example: `1_📊_Dashboard.py` becomes "📊 Dashboard" in the sidebar

## Current Pages

1. **📊 Dashboard** (`1_📊_Dashboard.py`) - Overview and summary statistics with visualizations
2. **👥 Analisis Karyawan** (`2_👥_Analisis_Karyawan.py`) - Employee analysis table
3. **✅ Checklist Compliance** (`3_✅_Checklist_Compliance.py`) - Compliance checklist
4. **📋 Raport Organization** (`4_📋_Raport_Organization.py`) - Organization reports
5. **🔍 Detail Karyawan** (`5_🔍_Detail_Karyawan.py`) - Individual employee details

## Adding New Pages

To add a new page:

1. Create a new file in this directory with the naming pattern: `{next_number}_{icon}_{name}.py`
2. Import necessary utilities and components
3. Use `st.set_page_config()` to configure the page
4. Implement your page logic

Example:
```python
# pages/6_📈_Reports.py
import streamlit as st

st.set_page_config(
    page_title="Reports - Audit Absensi",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Reports")
# Your page content here
```

## Notes

- The main `app.py` file serves as the home page
- Each page is independent and can have its own sidebar filters
- Shared components are imported from the `components/` directory
- Data loading and utilities are in the `utils/` directory

