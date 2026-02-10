"""Employee analysis component"""
import streamlit as st
import pandas as pd
from utils.formatters import format_hours
from reports.pdf_report import create_table_pdf


def render_employee_analysis(employee_stats_full, selected_branch, selected_org):
    """Render analisis per karyawan"""
    st.header("👥 Analisis Per Karyawan")
    
    # Gunakan employee_stats_full yang sudah dihitung di atas
    employee_stats = employee_stats_full.copy()
    
    # Format jam kerja
    employee_stats['Total Jam Kerja (Real) Formatted'] = employee_stats['Total Jam Kerja (Real)'].apply(format_hours)
    employee_stats['Total Jam Kerja (Plan) Formatted'] = employee_stats['Total Jam Kerja (Plan)'].apply(format_hours)
    employee_stats['Total Jam Late In Formatted'] = employee_stats['Total Jam Late In'].apply(format_hours)
    employee_stats['Total Jam Early Out Formatted'] = employee_stats['Total Jam Early Out'].apply(format_hours)
    
    # Hitung checklist dan kekurangan jam kerja
    # Checklist: ✅ (hijau) jika Real >= Plan, ❌ (merah) jika Real < Plan
    employee_stats['Checklist Plan'] = employee_stats.apply(
        lambda row: '✅' if row['Total Jam Kerja (Real)'] >= row['Total Jam Kerja (Plan)'] else '❌',
        axis=1
    )
    
    # Kekurangan jam kerja: Plan - Real (jika Real < Plan), 0 jika sudah memenuhi
    employee_stats['Kekurangan Jam Kerja'] = employee_stats.apply(
        lambda row: max(0, row['Total Jam Kerja (Plan)'] - row['Total Jam Kerja (Real)']),
        axis=1
    )
    
    # Format kekurangan jam kerja
    employee_stats['Kekurangan Jam Kerja Formatted'] = employee_stats['Kekurangan Jam Kerja'].apply(
        lambda x: format_hours(x) if x > 0 else '0 jam'
    )
    
    # Tampilkan tabel (tanpa Branch dan Hari Libur)
    display_cols = [
        'Employee ID', 'Full Name', 'Organization', 'Job Position',
        'Work Days Bulan Ini', 'Jumlah Hadir', 'Jumlah Absen', 'Jumlah Cuti',
        'Jumlah Late In', 'Jumlah Early Out',
        'Total Jam Kerja (Real) Formatted', 'Total Jam Kerja (Plan) Formatted',
        'Checklist Plan', 'Kekurangan Jam Kerja Formatted',
        'Total Jam Late In Formatted', 'Total Jam Early Out Formatted'
    ]
    
    # Rename untuk display
    display_df = employee_stats[display_cols].copy()
    display_df.columns = [
        'ID', 'Nama', 'Organization', 'Posisi',
        'Work Days Bulan Ini', 'Jumlah Hadir', 'Jumlah Absen', 'Cuti',
        'Late In', 'Early Out',
        'Total Jam Kerja (Real)', 'Total Jam Kerja (Plan)',
        'Checklist Plan', 'Kekurangan Jam Kerja',
        'Total Jam Late In', 'Total Jam Early Out'
    ]
    
    # Search box
    search_term = st.text_input("🔍 Cari Karyawan (Nama atau ID)", "")
    if search_term:
        mask = (
            display_df['Nama'].str.contains(search_term, case=False, na=False) |
            display_df['ID'].astype(str).str.contains(search_term, case=False, na=False)
        )
        display_df = display_df[mask]
    
    st.dataframe(
        display_df,
        use_container_width=True,
        height=400
    )
    
    # Download button (hapus kolom Branch dan Organization dari CSV)
    csv_df = employee_stats.drop(columns=['Branch', 'Organization'], errors='ignore')
    csv = csv_df.to_csv(index=False)
    
    col_analysis1, col_analysis2 = st.columns(2)
    with col_analysis1:
        st.download_button(
            label="📥 Download Data Analisis (CSV)",
            data=csv,
            file_name=f"analisis_absensi_januari_{selected_branch}_{selected_org}.csv",
            mime="text/csv",
            key='download_analysis_csv'
        )
    with col_analysis2:
        # Siapkan data untuk PDF (hapus kolom Branch dan Organization)
        pdf_analysis_df = display_df.drop(columns=['Branch', 'Organization'], errors='ignore').copy()
        pdf_analysis = create_table_pdf(
            pdf_analysis_df,
            "ANALISIS PER KARYAWAN",
            f"Branch: {selected_branch} | Organization: {selected_org if selected_org != 'All' else 'Semua'}"
        )
        st.download_button(
            label="📄 Download Data Analisis (PDF)",
            data=pdf_analysis.getvalue(),
            file_name=f"analisis_absensi_januari_{selected_branch}_{selected_org}.pdf",
            mime="application/pdf",
            key='download_analysis_pdf'
        )
    
    st.markdown("---")
    
    return employee_stats

