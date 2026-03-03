"""Checklist Compliance page"""
import streamlit as st
from utils.data_loader import load_data, filter_data
from components.sidebar import render_sidebar_month, render_sidebar_filters
from components.checklist_compliance import render_checklist_compliance

st.set_page_config(
    page_title="Checklist Compliance - Audit Absensi",
    page_icon="✅",
    layout="wide"
)

st.title("✅ Checklist Compliance")
st.markdown("---")

selected_month = render_sidebar_month()
df = load_data(selected_month)

if df is not None:
    selected_branch, selected_org = render_sidebar_filters(df)
    
    # Filter data
    filtered_df = filter_data(df, selected_branch, selected_org)
    
    # Render Checklist Compliance
    render_checklist_compliance(filtered_df, selected_branch)
else:
    st.error("Gagal memuat data. Pastikan file CSV bulan yang dipilih ada di folder project.")

