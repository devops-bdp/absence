"""Sidebar component for filters only"""
import streamlit as st

# Opsi bulan (value -> label)
MONTH_OPTIONS = [
    # 2025
    ('2025-03', 'Maret 2025'),
    ('2025-04', 'April 2025'),
    ('2025-05', 'Mei 2025'),
    ('2025-06', 'Juni 2025'),
    ('2025-07', 'Juli 2025'),
    ('2025-08', 'Agustus 2025'),
    ('2025-09', 'September 2025'),
    ('2025-10', 'Oktober 2025'),
    ('2025-11', 'November 2025'),
    ('2025-12', 'Desember 2025'),
    # 2026
    ('january', 'Januari 2026'),
    ('february', 'Februari 2026'),
    ('march', 'Maret 2026'),
]


def render_sidebar_month():
    """Render hanya selector bulan di sidebar. Panggil sekali per halaman, lalu load_data(month)."""
    st.sidebar.header("🔍 Filter Data")
    month_values = [m[0] for m in MONTH_OPTIONS]
    default_month = st.session_state.get('selected_month', 'january')
    default_index = month_values.index(default_month) if default_month in month_values else 0
    selected_month = st.sidebar.selectbox(
        "Pilih Bulan",
        options=month_values,
        format_func=lambda x: dict(MONTH_OPTIONS).get(x, x),
        index=default_index,
        key="sidebar_month"
    )
    st.session_state.selected_month = selected_month
    return selected_month


def render_sidebar_filters(df):
    """Render filter Branch dan Organization. Panggil setelah load_data(selected_month)."""
    branches = sorted(df['Branch'].unique().tolist())
    default_branch = 'HO Jakarta' if 'HO Jakarta' in branches else branches[0] if branches else None
    selected_branch = st.sidebar.selectbox(
        "Pilih Branch",
        branches,
        index=branches.index(default_branch) if default_branch and default_branch in branches else 0
    )
    organizations = ['All'] + sorted(df['Organization'].unique().tolist())
    selected_org = st.sidebar.selectbox("Pilih Organization", organizations)
    return selected_branch, selected_org

