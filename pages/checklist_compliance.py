"""Checklist Compliance page module"""
import streamlit as st
from utils.data_loader import load_data, filter_data
from components.sidebar import render_sidebar_filters
from components.checklist_compliance import render_checklist_compliance

def render_checklist_page():
    """Render the checklist compliance page"""
    st.title("✅ Checklist Compliance")
    st.markdown("---")

    # Load data
    df = load_data()

    if df is not None:
        # Sidebar untuk filter
        selected_branch, selected_org = render_sidebar_filters(df)
        
        # Filter data
        filtered_df = filter_data(df, selected_branch, selected_org)
        
        # Render Checklist Compliance
        render_checklist_compliance(filtered_df, selected_branch)
    else:
        st.error("Gagal memuat data. Pastikan file january.csv ada di direktori yang sama.")

