"""Dashboard page module"""
import streamlit as st
from utils.data_loader import load_data, filter_data
from utils.calculations import calculate_work_days, calculate_employee_stats
from components.sidebar import render_sidebar_month, render_sidebar_filters
from components.summary_stats import render_summary_stats
from components.visualizations import render_visualizations
from utils.formatters import format_hours

def render_dashboard():
    """Render the dashboard page"""
    st.title("📊 Dashboard")
    st.markdown("---")

    selected_month = render_sidebar_month()
    df = load_data(selected_month)

    if df is not None:
        selected_branch, selected_org = render_sidebar_filters(df)

        # Filter data
        filtered_df = filter_data(df, selected_branch, selected_org)

        # Total Karyawan baseline dari Januari (agar sama di semua bulan)
        total_employees_baseline = None
        if selected_month != 'january':
            df_january = load_data('january')
            if df_january is not None:
                january_filtered = filter_data(df_january, selected_branch, selected_org)
                total_employees_baseline = january_filtered['Employee ID'].nunique()

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

        # Render Summary Statistics (Total Karyawan = baseline Januari jika bukan bulan Januari)
        render_summary_stats(filtered_df, work_days_month, employee_stats_full, selected_branch, selected_org, total_employees_baseline)
        
        # Render Visualizations
        render_visualizations(employee_stats_full, selected_branch, work_days_month)
    else:
        st.error("Gagal memuat data. Pastikan file CSV bulan yang dipilih ada di folder project.")

