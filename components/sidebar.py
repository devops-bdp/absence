"""Sidebar component for filters only"""
import streamlit as st


def render_sidebar_filters(df):
    """Render sidebar dengan filter Branch dan Organization - Only filters, no other content"""
    st.sidebar.header("🔍 Filter Data")
    
    # Filter berdasarkan Branch - Default hanya HO Jakarta
    branches = sorted(df['Branch'].unique().tolist())
    default_branch = 'HO Jakarta' if 'HO Jakarta' in branches else branches[0] if branches else None
    selected_branch = st.sidebar.selectbox(
        "Pilih Branch", 
        branches, 
        index=branches.index(default_branch) if default_branch and default_branch in branches else 0
    )
    
    # Filter berdasarkan Organization
    organizations = ['All'] + sorted(df['Organization'].unique().tolist())
    selected_org = st.sidebar.selectbox("Pilih Organization", organizations)
    
    return selected_branch, selected_org

