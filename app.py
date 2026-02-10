"""Main Streamlit application - Landing Page with Card Navigation"""
import streamlit as st
import pandas as pd
from datetime import datetime

# Import utilities
from utils.data_loader import load_data, filter_data
from utils.calculations import calculate_work_days, calculate_employee_stats

# Import components
from components.sidebar import render_sidebar_filters

# Import reports
from reports.excel_report import create_excel_report
from reports.pdf_report import create_pdf_report
from components.checklist_compliance import check_in_out_time
from utils.formatters import format_hours

# Import pages
from pages.dashboard import render_dashboard
from pages.dashboard_personal import render_dashboard_personal
from pages.employee_analysis import render_employee_analysis_page
from pages.checklist_compliance import render_checklist_page
from pages.organization_report import render_organization_page
from pages.employee_detail import render_employee_detail_page

# Konfigurasi halaman
st.set_page_config(
    page_title="Audit & Analisis Absensi - Januari 2026",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide the default Streamlit menu and footer
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Initialize session state for navigation
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'landing'

# Navigation function
def navigate_to(page):
    st.session_state.current_page = page
    st.rerun()

# Custom CSS for landing page cards
st.markdown("""
<style>
    .landing-card-container {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s, box-shadow 0.3s;
        height: 100%;
        border: 2px solid transparent;
        cursor: pointer;
    }
    .landing-card-container:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
    }
    .card-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    .card-title {
        font-size: 1.5rem;
        font-weight: bold;
        margin: 0.5rem 0;
        color: #1f4788;
    }
    .card-description {
        color: #666;
        font-size: 0.95rem;
        margin-top: 0.5rem;
    }
    .card-dashboard {
        border-top: 4px solid #667eea;
    }
    .card-dashboard:hover {
        border-color: #667eea;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
    }
    .card-analysis {
        border-top: 4px solid #f5576c;
    }
    .card-analysis:hover {
        border-color: #f5576c;
        background: linear-gradient(135deg, rgba(245, 87, 108, 0.05) 0%, rgba(240, 147, 251, 0.05) 100%);
    }
    .card-checklist {
        border-top: 4px solid #4facfe;
    }
    .card-checklist:hover {
        border-color: #4facfe;
        background: linear-gradient(135deg, rgba(79, 172, 254, 0.05) 0%, rgba(0, 242, 254, 0.05) 100%);
    }
    .card-organization {
        border-top: 4px solid #43e97b;
    }
    .card-organization:hover {
        border-color: #43e97b;
        background: linear-gradient(135deg, rgba(67, 233, 123, 0.05) 0%, rgba(56, 249, 215, 0.05) 100%);
    }
    .card-detail {
        border-top: 4px solid #fa709a;
    }
    .card-detail:hover {
        border-color: #fa709a;
        background: linear-gradient(135deg, rgba(250, 112, 154, 0.05) 0%, rgba(254, 225, 64, 0.05) 100%);
    }
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# Main app logic
if st.session_state.current_page == 'landing':
    # Landing Page
    st.title("📊 Audit & Analisis Data Absensi - Januari 2026")
    st.markdown("---")
    
    st.markdown("""
    <div style='text-align: center; margin-bottom: 3rem;'>
        <h2>Selamat Datang di Sistem Audit & Analisis Absensi</h2>
        <p style='font-size: 1.1rem; color: #666;'>Pilih menu di bawah untuk mulai menganalisis data absensi</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Card Grid
    col1, col2 = st.columns(2)
    
    with col1:
        # Dashboard Card
        with st.container():
            st.markdown("""
            <div class="landing-card-container card-dashboard">
                <div class="card-icon">📊</div>
                <div class="card-title">Dashboard</div>
                <div class="card-description">Ringkasan statistik dan visualisasi data absensi</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("📊 Buka Dashboard", key="btn_dashboard", use_container_width=True):
                navigate_to('dashboard')
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Checklist Compliance Card
        with st.container():
            st.markdown("""
            <div class="landing-card-container card-checklist">
                <div class="card-icon">✅</div>
                <div class="card-title">Checklist Compliance</div>
                <div class="card-description">Verifikasi compliance terhadap standar kerja</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("✅ Buka Checklist", key="btn_checklist", use_container_width=True):
                navigate_to('checklist')
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Employee Analysis Card
        with st.container():
            st.markdown("""
            <div class="landing-card-container card-analysis">
                <div class="card-icon">👥</div>
                <div class="card-title">Analisis Karyawan</div>
                <div class="card-description">Analisis detail per karyawan dengan metrik lengkap</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("👥 Buka Analisis", key="btn_analysis", use_container_width=True):
                navigate_to('analysis')
    
    with col2:
        # Employee Detail Card
        with st.container():
            st.markdown("""
            <div class="landing-card-container card-detail">
                <div class="card-icon">🔍</div>
                <div class="card-title">Detail Karyawan</div>
                <div class="card-description">Detail lengkap per karyawan dengan visualisasi</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🔍 Buka Detail", key="btn_detail", use_container_width=True):
                navigate_to('detail')
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Organization Report Card
        with st.container():
            st.markdown("""
            <div class="landing-card-container card-organization">
                <div class="card-icon">📋</div>
                <div class="card-title">Raport Organization</div>
                <div class="card-description">Ringkasan statistik absensi per organization</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("📋 Buka Raport", key="btn_organization", use_container_width=True):
                navigate_to('organization')

elif st.session_state.current_page == 'dashboard':
    # Back button
    if st.button("← Kembali ke Landing Page", key="back_dashboard"):
        navigate_to('landing')
    render_dashboard()

elif st.session_state.current_page == 'dashboard_personal':
    # Back button
    if st.button("← Kembali ke Landing Page", key="back_dashboard_personal"):
        navigate_to('landing')
    render_dashboard_personal()

elif st.session_state.current_page == 'analysis':
    # Back button
    if st.button("← Kembali ke Landing Page", key="back_analysis"):
        navigate_to('landing')
    render_employee_analysis_page()

elif st.session_state.current_page == 'checklist':
    # Back button
    if st.button("← Kembali ke Landing Page", key="back_checklist"):
        navigate_to('landing')
    render_checklist_page()

elif st.session_state.current_page == 'organization':
    # Back button
    if st.button("← Kembali ke Landing Page", key="back_organization"):
        navigate_to('landing')
    render_organization_page()

elif st.session_state.current_page == 'detail':
    # Back button
    if st.button("← Kembali ke Landing Page", key="back_detail"):
        navigate_to('landing')
    render_employee_detail_page()
