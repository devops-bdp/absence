"""Checklist compliance component"""
import streamlit as st
import pandas as pd
from utils.data_loader import time_to_minutes
from reports.pdf_report import create_table_pdf


def check_in_out_time(row):
    """Check apakah masuk <= 08:00 dan pulang >= 17:00"""
    check_in_minutes = time_to_minutes(row['Check In'])
    check_out_minutes = time_to_minutes(row['Check Out'])
    
    if check_in_minutes is None or check_out_minutes is None:
        return '❌'
    
    # Target: Check In <= 08:00 (480 menit) dan Check Out >= 17:00 (1020 menit)
    target_check_in = 8 * 60 + 0  # 08:00 = 480 menit
    target_check_out = 17 * 60 + 0  # 17:00 = 1020 menit
    
    if check_in_minutes <= target_check_in and check_out_minutes >= target_check_out:
        return '✅'
    else:
        return '❌'


def render_checklist_compliance(filtered_df, selected_branch):
    """Render tabel checklist compliance"""
    st.header("✅ Tabel Checklist Compliance")
    st.markdown("Checklist untuk memverifikasi compliance karyawan terhadap standar kerja")
    
    # Buat tabel checklist
    checklist_data = filtered_df.copy()
    
    # Filter hanya yang hadir
    checklist_data = checklist_data[checklist_data['Is Present'] == True].copy()
    
    # Checklist 1: Kerja selama 8 jam per hari
    checklist_data['Checklist_8_Jam'] = checklist_data['Real Working Hour Decimal'].apply(
        lambda x: '✅' if x >= 8.0 else '❌'
    )
    
    # Checklist 2: Masuk <= 08:00 dan pulang >= 17:00
    checklist_data['Checklist_Jam_8_17'] = checklist_data.apply(check_in_out_time, axis=1)
    
    # Pilih kolom untuk checklist (dengan Branch dan Organization untuk display di UI)
    checklist_display = checklist_data[[
        'Date', 'Employee ID', 'Full Name', 'Branch', 'Organization', 'Job Position',
        'Shift', 'Check In', 'Check Out', 'Real Working Hour', 'Real Working Hour Decimal',
        'Checklist_8_Jam', 'Checklist_Jam_8_17'
    ]].copy()
    
    # Filter tanggal untuk checklist
    col_check1, col_check2 = st.columns(2)
    with col_check1:
        min_date_check = checklist_display['Date'].min().date() if not checklist_display['Date'].empty else pd.Timestamp.now().date()
        max_date_check = checklist_display['Date'].max().date() if not checklist_display['Date'].empty else pd.Timestamp.now().date()
        date_start_check = st.date_input("Tanggal Mulai - Checklist", value=min_date_check, min_value=min_date_check, max_value=max_date_check, key='check_start')
    with col_check2:
        date_end_check = st.date_input("Tanggal Akhir - Checklist", value=max_date_check, min_value=min_date_check, max_value=max_date_check, key='check_end')
    
    # Filter berdasarkan tanggal
    checklist_display_filtered = checklist_display[
        (checklist_display['Date'].dt.date >= date_start_check) &
        (checklist_display['Date'].dt.date <= date_end_check)
    ].copy()
    
    # Search box untuk checklist (sebelum rename)
    search_checklist = st.text_input("🔍 Cari Karyawan (Nama atau ID) - Checklist", "", key='search_checklist')
    if search_checklist:
        mask_check = (
            checklist_display_filtered['Full Name'].str.contains(search_checklist, case=False, na=False) |
            checklist_display_filtered['Employee ID'].astype(str).str.contains(search_checklist, case=False, na=False)
        )
        checklist_display_filtered = checklist_display_filtered[mask_check]
    
    # Sort berdasarkan nama dulu, baru tanggal (untuk grouping per orang)
    checklist_display_filtered = checklist_display_filtered.sort_values(['Full Name', 'Date'], ascending=[True, True])
    
    # Format tanggal untuk display (hanya tanggal, tanpa jam)
    checklist_display_filtered['Date'] = checklist_display_filtered['Date'].dt.strftime('%Y-%m-%d')
    checklist_display_filtered['Date'] = checklist_display_filtered['Date'].astype(str)
    
    # Rename kolom untuk display
    checklist_display_filtered.columns = [
        'Tanggal', 'ID', 'Nama', 'Branch', 'Organization', 'Posisi',
        'Shift', 'Check In', 'Check Out', 'Jam Kerja (Format)', 'Jam Kerja (Desimal)',
        '✅ Kerja 8 Jam/Hari', '✅ Masuk 08:00 & Pulang 17:00'
    ]
    
    # Buat copy untuk download (tanpa Branch dan Organization)
    checklist_display_for_download = checklist_display_filtered.drop(columns=['Branch', 'Organization'], errors='ignore').copy()
    checklist_display_for_download = checklist_display_for_download.sort_values(['Nama', 'Tanggal'], ascending=[True, True])
    
    # Statistik checklist
    total_checklist = len(checklist_display_filtered)
    compliant_8jam = len(checklist_display_filtered[checklist_display_filtered['✅ Kerja 8 Jam/Hari'] == '✅'])
    compliant_8_17 = len(checklist_display_filtered[checklist_display_filtered['✅ Masuk 08:00 & Pulang 17:00'] == '✅'])
    compliant_both = len(checklist_display_filtered[
        (checklist_display_filtered['✅ Kerja 8 Jam/Hari'] == '✅') &
        (checklist_display_filtered['✅ Masuk 08:00 & Pulang 17:00'] == '✅')
    ])
    
    col_check_stat1, col_check_stat2, col_check_stat3, col_check_stat4 = st.columns(4)
    with col_check_stat1:
        st.metric("Total Record", total_checklist)
    with col_check_stat2:
        st.metric("✅ Kerja 8 Jam/Hari", f"{compliant_8jam} ({(compliant_8jam/total_checklist*100) if total_checklist > 0 else 0:.1f}%)")
    with col_check_stat3:
        st.metric("✅ Masuk 08:00 & Pulang 17:00", f"{compliant_8_17} ({(compliant_8_17/total_checklist*100) if total_checklist > 0 else 0:.1f}%)")
    with col_check_stat4:
        st.metric("✅ Keduanya Compliant", f"{compliant_both} ({(compliant_both/total_checklist*100) if total_checklist > 0 else 0:.1f}%)")
    
    # Tampilkan tabel checklist
    st.dataframe(
        checklist_display_filtered,
        use_container_width=True,
        height=500
    )
    
    # Download button untuk checklist (tanpa Branch dan Organization)
    csv_checklist = checklist_display_for_download.to_csv(index=False)
    
    col_checklist1, col_checklist2 = st.columns(2)
    with col_checklist1:
        st.download_button(
            label="📥 Download Tabel Checklist (CSV)",
            data=csv_checklist,
            file_name=f"checklist_compliance_ho_jakarta_{date_start_check}_{date_end_check}.csv",
            mime="text/csv",
            key='download_checklist_csv'
        )
    with col_checklist2:
        pdf_checklist = create_table_pdf(
            checklist_display_for_download,
            "CHECKLIST COMPLIANCE",
            f"Branch: {selected_branch} | Periode: {date_start_check} - {date_end_check}"
        )
        st.download_button(
            label="📄 Download Tabel Checklist (PDF)",
            data=pdf_checklist.getvalue(),
            file_name=f"checklist_compliance_ho_jakarta_{date_start_check}_{date_end_check}.pdf",
            mime="application/pdf",
            key='download_checklist_pdf'
        )
    
    st.markdown("---")
    
    return checklist_display_for_download

