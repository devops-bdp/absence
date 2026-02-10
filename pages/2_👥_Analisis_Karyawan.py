"""Employee Analysis page"""
import streamlit as st
from utils.data_loader import load_data, filter_data
from utils.calculations import calculate_work_days, calculate_employee_stats
from components.sidebar import render_sidebar_filters
from components.employee_analysis import render_employee_analysis
from utils.formatters import format_hours

st.set_page_config(
    page_title="Analisis Karyawan - Audit Absensi",
    page_icon="👥",
    layout="wide"
)

st.title("👥 Analisis Per Karyawan")
st.markdown("---")

# Load data
df = load_data()

if df is not None:
    # Sidebar untuk filter
    selected_branch, selected_org = render_sidebar_filters(df)
    
    # Filter data
    filtered_df = filter_data(df, selected_branch, selected_org)
    
    # Hitung work days bulan ini
    if not filtered_df['Date'].empty:
        first_date = filtered_df['Date'].min()
        year = first_date.year
        month = first_date.month
        work_days_month = calculate_work_days(year, month)
    else:
        work_days_month = 0
    
    # Hitung employee stats
    employee_stats_full = calculate_employee_stats(filtered_df, work_days_month)
    
    # Format jam kerja untuk employee_stats
    employee_stats_full['Total Jam Kerja (Real) Formatted'] = employee_stats_full['Total Jam Kerja (Real)'].apply(format_hours)
    employee_stats_full['Total Jam Kerja (Plan) Formatted'] = employee_stats_full['Total Jam Kerja (Plan)'].apply(format_hours)
    employee_stats_full['Total Jam Late In Formatted'] = employee_stats_full['Total Jam Late In'].apply(format_hours)
    employee_stats_full['Total Jam Early Out Formatted'] = employee_stats_full['Total Jam Early Out'].apply(format_hours)
    
    # Render Employee Analysis
    render_employee_analysis(employee_stats_full, selected_branch, selected_org)
else:
    st.error("Gagal memuat data. Pastikan file january.csv ada di direktori yang sama.")

