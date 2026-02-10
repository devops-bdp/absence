"""Organization report component"""
import streamlit as st
import pandas as pd
from utils.calculations import calculate_organization_stats
from utils.formatters import format_hours
from reports.pdf_report import create_table_pdf


def render_organization_report(filtered_df, work_days_month, employee_stats_full, selected_branch, selected_org):
    """Render raport per organization"""
    st.header("📋 Raport per Organization")
    st.markdown("Ringkasan statistik absensi per Organization")
    
    # Hitung statistik per organization
    org_stats = calculate_organization_stats(filtered_df, work_days_month)
    
    # Format jam kerja
    org_stats['Total Jam Kerja (Real) Formatted'] = org_stats['Total Jam Kerja (Real)'].apply(format_hours)
    org_stats['Total Jam Kerja (Plan) Formatted'] = org_stats['Total Jam Kerja (Plan)'].apply(format_hours)
    
    # Hitung selisih Plan vs Actual
    org_stats['Selisih Jam Kerja'] = org_stats['Total Jam Kerja (Real)'] - org_stats['Total Jam Kerja (Plan)']
    org_stats['Selisih Jam Kerja Formatted'] = org_stats['Selisih Jam Kerja'].apply(
        lambda x: format_hours(abs(x)) if x != 0 else '0 jam'
    )
    
    # Checklist Plan
    org_stats['Checklist Plan'] = org_stats.apply(
        lambda row: '✅' if row['Total Jam Kerja (Real)'] >= row['Total Jam Kerja (Plan)'] else '❌',
        axis=1
    )
    
    # Pilih kolom untuk display
    org_display_cols = [
        'Organization', 'Total Karyawan', 'Work Day', 'Total Work Day',
        'Total Kehadiran', 'Kehadiran (%)', 'Total Tidak Hadir', 'Tidak Hadir (%)',
        'Total Cuti', 'Total Late In', 'Total Early Out',
        'Total Jam Kerja (Real) Formatted', 'Total Jam Kerja (Plan) Formatted',
        'Checklist Plan', 'Plan vs Actual (%)', 'Selisih Jam Kerja Formatted'
    ]
    
    org_display_df = org_stats[org_display_cols].copy()
    org_display_df.columns = [
        'Organization', 'Total Karyawan', 'Work Day', 'Total Work Day',
        'Total Kehadiran', 'Kehadiran (%)', 'Total Tidak Hadir', 'Tidak Hadir (%)',
        'Total Cuti', 'Total Late In', 'Total Early Out',
        'Total Jam Kerja (Real)', 'Total Jam Kerja (Plan)',
        'Checklist Plan', 'Plan vs Actual (%)', 'Selisih Jam Kerja'
    ]
    
    # Tampilkan cards per Organization
    st.subheader("📊 Ringkasan per Organization")
    
    num_orgs = len(org_stats)
    cols = st.columns(num_orgs)
    
    for idx in range(num_orgs):
        org_row = org_stats.iloc[idx]
        with cols[idx]:
            with st.container():
                st.markdown(f"### {org_row['Organization']}")
                st.markdown(f"**{org_row['Checklist Plan']}** Plan Status")
                
                st.metric("Total Karyawan", int(org_row['Total Karyawan']))
                st.metric("Total Kehadiran", f"{int(org_row['Total Kehadiran'])} ({org_row['Kehadiran (%)']:.1f}%)")
                st.metric("Total Tidak Hadir", f"{int(org_row['Total Tidak Hadir'])} ({org_row['Tidak Hadir (%)']:.1f}%)")
                st.metric("Total Cuti", int(org_row['Total Cuti']))
                st.metric("Late In", int(org_row['Total Late In']))
                st.metric("Early Out", int(org_row['Total Early Out']))
                
                st.markdown("---")
                st.markdown(f"**Total Jam Kerja (Real):** {org_row['Total Jam Kerja (Real) Formatted']}")
                st.markdown(f"**Total Jam Kerja (Plan):** {org_row['Total Jam Kerja (Plan) Formatted']}")
                st.markdown(f"**Plan vs Actual:** {org_row['Plan vs Actual (%)']:.1f}%")
                st.markdown(f"**Selisih:** {org_row['Selisih Jam Kerja Formatted']}")
    
    st.markdown("---")
    
    # Breakdown per Organization dengan peringkat karyawan
    st.subheader("🔍 Breakdown per Organization")
    
    org_list = ['All'] + sorted(org_stats['Organization'].unique().tolist())
    selected_org_breakdown = st.selectbox(
        "Pilih Organization untuk melihat breakdown",
        options=org_list,
        key='org_breakdown_select'
    )
    
    if selected_org_breakdown != 'All':
        org_employees = employee_stats_full[employee_stats_full['Organization'] == selected_org_breakdown].copy()
        
        if len(org_employees) > 0:
            # Format jam kerja untuk breakdown
            org_employees['Total Jam Kerja (Real) Formatted'] = org_employees['Total Jam Kerja (Real)'].apply(format_hours)
            org_employees['Total Jam Kerja (Plan) Formatted'] = org_employees['Total Jam Kerja (Plan)'].apply(format_hours)
            
            # Hitung checklist dan kekurangan
            org_employees['Checklist Plan'] = org_employees.apply(
                lambda row: '✅' if row['Total Jam Kerja (Real)'] >= row['Total Jam Kerja (Plan)'] else '❌',
                axis=1
            )
            org_employees['Kekurangan Jam Kerja'] = org_employees.apply(
                lambda row: max(0, row['Total Jam Kerja (Plan)'] - row['Total Jam Kerja (Real)']),
                axis=1
            )
            org_employees['Kekurangan Jam Kerja Formatted'] = org_employees['Kekurangan Jam Kerja'].apply(
                lambda x: format_hours(x) if x > 0 else '0 jam'
            )
            
            # Selectbox untuk memilih metrik perangkingan
            ranking_metric = st.selectbox(
                "Peringkat berdasarkan",
                options=[
                    'Total Jam Kerja (Real)',
                    'Jumlah Hadir',
                    'Jumlah Absen',
                    'Jumlah Late In',
                    'Jumlah Early Out'
                ],
                key='ranking_metric_select'
            )
            
            # Sort berdasarkan metrik yang dipilih
            sort_col = ranking_metric
            org_employees_sorted = org_employees.sort_values(sort_col, ascending=False)
            
            # Tambahkan kolom peringkat
            org_employees_sorted['Peringkat'] = range(1, len(org_employees_sorted) + 1)
            
            # Pilih kolom untuk display
            breakdown_cols = [
                'Peringkat', 'Employee ID', 'Full Name', 'Job Position',
                'Work Days Bulan Ini', 'Jumlah Hadir', 'Jumlah Absen', 'Jumlah Cuti',
                'Jumlah Late In', 'Jumlah Early Out',
                'Total Jam Kerja (Real) Formatted', 'Total Jam Kerja (Plan) Formatted',
                'Checklist Plan', 'Kekurangan Jam Kerja Formatted'
            ]
            
            breakdown_df = org_employees_sorted[breakdown_cols].copy()
            breakdown_df.columns = [
                'Peringkat', 'ID', 'Nama', 'Posisi',
                'Work Days Bulan Ini', 'Jumlah Hadir', 'Jumlah Absen', 'Cuti',
                'Late In', 'Early Out',
                'Total Jam Kerja (Real)', 'Total Jam Kerja (Plan)',
                'Checklist Plan', 'Kekurangan Jam Kerja'
            ]
            
            st.markdown(f"### 📊 Breakdown Organization: **{selected_org_breakdown}**")
            st.markdown(f"**Total Karyawan:** {len(org_employees_sorted)} | **Peringkat berdasarkan:** {ranking_metric}")
            
            st.dataframe(breakdown_df, use_container_width=True, height=500)
            
            # Download button untuk breakdown
            csv_breakdown = org_employees_sorted.drop(columns=['Branch', 'Organization', 'Total Jam Kerja (Real) Formatted', 'Total Jam Kerja (Plan) Formatted', 'Kekurangan Jam Kerja Formatted'], errors='ignore').to_csv(index=False)
            
            col_breakdown1, col_breakdown2 = st.columns(2)
            with col_breakdown1:
                st.download_button(
                    label="📥 Download Breakdown Organization (CSV)",
                    data=csv_breakdown,
                    file_name=f"breakdown_{selected_org_breakdown}_{selected_branch}.csv",
                    mime="text/csv",
                    key='download_breakdown_csv'
                )
            with col_breakdown2:
                pdf_breakdown = create_table_pdf(
                    breakdown_df,
                    f"BREAKDOWN ORGANIZATION - {selected_org_breakdown}",
                    f"Branch: {selected_branch} | Peringkat berdasarkan: {ranking_metric}"
                )
                st.download_button(
                    label="📄 Download Breakdown Organization (PDF)",
                    data=pdf_breakdown.getvalue(),
                    file_name=f"breakdown_{selected_org_breakdown}_{selected_branch}.pdf",
                    mime="application/pdf",
                    key='download_breakdown_pdf'
                )
        else:
            st.info(f"Tidak ada data untuk Organization: {selected_org_breakdown}")
    else:
        st.info("Pilih Organization untuk melihat breakdown dan peringkat karyawan")
    
    st.markdown("---")
    
    # Download button untuk Raport per Organization
    csv_org = org_stats.drop(columns=['Total Jam Kerja (Real) Formatted', 'Total Jam Kerja (Plan) Formatted', 'Selisih Jam Kerja Formatted'], errors='ignore').to_csv(index=False)
    
    col_org1, col_org2 = st.columns(2)
    with col_org1:
        st.download_button(
            label="📥 Download Raport per Organization (CSV)",
            data=csv_org,
            file_name=f"raport_per_organization_{selected_branch}_{selected_org}.csv",
            mime="text/csv",
            key='download_org_csv'
        )
    with col_org2:
        pdf_org = create_table_pdf(
            org_display_df,
            "RAPORT PER ORGANIZATION",
            f"Branch: {selected_branch} | Organization: {selected_org if selected_org != 'All' else 'Semua'}"
        )
        st.download_button(
            label="📄 Download Raport per Organization (PDF)",
            data=pdf_org.getvalue(),
            file_name=f"raport_per_organization_{selected_branch}_{selected_org}.pdf",
            mime="application/pdf",
            key='download_org_pdf'
        )
    
    st.markdown("---")

