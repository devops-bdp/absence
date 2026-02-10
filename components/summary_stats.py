"""Summary statistics component"""
import streamlit as st
import pandas as pd
from utils.formatters import format_hours
from utils.calculations import calculate_employee_stats
from reports.pdf_report import create_table_pdf


def render_summary_stats(filtered_df, work_days_month, employee_stats_full, selected_branch, selected_org):
    """Render ringkasan statistik"""
    st.header("📈 Ringkasan Statistik")
    
    # Hitung semua metrik
    total_employees = filtered_df['Employee ID'].nunique()
    total_present = filtered_df['Is Present'].sum()
    total_absent = filtered_df['Is Absent'].sum()
    total_leave = filtered_df['Is Leave'].sum()
    total_dayoff = filtered_df['Is Dayoff'].sum()
    total_work_day = total_employees * work_days_month
    # Hitung persentase relatif terhadap Total Work Day
    attendance_percentage = (total_present / total_work_day * 100) if total_work_day > 0 else 0
    absent_percentage = (total_absent / total_work_day * 100) if total_work_day > 0 else 0
    # Verifikasi: Total Work Day = Total Present + Total Absent + Total Leave
    # Catatan: Hari Libur (Is Dayoff) tidak masuk dalam Total Work Day karena Work Day hanya menghitung hari kerja (Senin-Jumat)
    total_work_day_records = total_present + total_absent + total_leave
    
    # Hitung record yang tidak terklasifikasi (bukan Present, Absent, Leave, atau Dayoff)
    # Filter hanya record pada hari kerja (bukan weekend)
    filtered_df['Is Weekday'] = filtered_df['Date'].dt.weekday < 5  # Senin-Jumat
    workday_records = filtered_df[filtered_df['Is Weekday'] == True]
    total_workday_records = len(workday_records)
    classified_records = total_present + total_absent + total_leave
    unclassified_records = total_workday_records - classified_records
    
    # Hitung juga record yang tidak masuk kategori apapun
    no_category = filtered_df[
        (~filtered_df['Is Present']) & 
        (~filtered_df['Is Absent']) & 
        (~filtered_df['Is Leave']) & 
        (~filtered_df['Is Dayoff'])
    ]
    total_no_category = len(no_category)
    
    # Hitung total jam kerja
    total_jam_kerja_real = employee_stats_full['Total Jam Kerja (Real)'].sum()
    total_jam_kerja_plant = total_work_day * 8
    total_jam_kerja_real_formatted = format_hours(total_jam_kerja_real)
    total_jam_kerja_plant_formatted = format_hours(total_jam_kerja_plant)
    
    # Hitung Selisih Absensi (agar total persentase = 100%)
    selisih_absensi = total_work_day - total_present - total_absent
    selisih_absensi_percentage = (selisih_absensi / total_work_day * 100) if total_work_day > 0 else 0
    
    # Tampilkan metrik dalam 2 baris
    col_stat1, col_stat2, col_stat3, col_stat4, col_stat5, col_stat6 = st.columns(6)
    
    with col_stat1:
        st.metric("Total Karyawan", total_employees, help="Formula: COUNT(DISTINCT Employee ID)")
    with col_stat2:
        st.metric("Work Day", work_days_month, help="Formula: Jumlah hari kerja (Senin-Jumat) dalam bulan")
    with col_stat3:
        st.metric("Total Work Day", total_work_day, help=f"Formula: Total Karyawan × Work Day\n= {total_employees} × {work_days_month} = {total_work_day}\n\nBreakdown (hanya hari kerja):\n- Total Kehadiran: {total_present}\n- Total Tidak Hadir: {total_absent}\n- Selisih Absensi: {selisih_absensi}\n- Total: {total_work_day}\n\nCatatan: Hari Libur tidak masuk dalam Total Work Day karena Work Day hanya menghitung hari kerja (Senin-Jumat)")
    with col_stat4:
        st.metric("Total Kehadiran", f"{total_present} ({attendance_percentage:.1f}%)", 
                 help=f"Formula: SUM(Is Present)\nPersentase: (Total Kehadiran / Total Work Day) × 100%\n= ({total_present} / {total_work_day}) × 100% = {attendance_percentage:.1f}%")
    with col_stat5:
        st.metric("Total Tidak Hadir", f"{total_absent} ({absent_percentage:.1f}%)", 
                 help=f"Formula: SUM(Is Absent)\nPersentase: (Total Tidak Hadir / Total Work Day) × 100%\n= ({total_absent} / {total_work_day}) × 100% = {absent_percentage:.1f}%")
    with col_stat6:
        st.metric("Selisih Absensi", f"{selisih_absensi} ({selisih_absensi_percentage:.1f}%)", 
                 help=f"Formula: Total Work Day - Total Kehadiran - Total Tidak Hadir\n= {total_work_day} - {total_present} - {total_absent} = {selisih_absensi}\nPersentase: (Selisih Absensi / Total Work Day) × 100%\n= ({selisih_absensi} / {total_work_day}) × 100% = {selisih_absensi_percentage:.1f}%\n\nSelisih Absensi mencakup Cuti dan Missing Records")
    
    # Baris kedua untuk Cuti dan Hari Libur
    col_stat6, col_stat7 = st.columns(2)
    leave_percentage = (total_leave / total_work_day * 100) if total_work_day > 0 else 0
    dayoff_percentage = (total_dayoff / total_work_day * 100) if total_work_day > 0 else 0
    
    with col_stat6:
        st.metric("✈️ Total Cuti", f"{total_leave} ({leave_percentage:.1f}%)", 
                 help=f"Formula: SUM(Is Leave)\nPersentase: (Total Cuti / Total Work Day) × 100%\n= ({total_leave} / {total_work_day}) × 100% = {leave_percentage:.1f}%")
    with col_stat7:
        st.metric("🏖️ Total Hari Libur", f"{total_dayoff}", 
                 help=f"Formula: SUM(Is Dayoff)\n\nCatatan: Hari Libur tidak masuk dalam perhitungan Total Work Day karena Work Day hanya menghitung hari kerja (Senin-Jumat). Hari Libur ini bisa berupa hari libur nasional yang jatuh pada hari kerja atau data tambahan.")
    
    # Penjelasan Selisih Absensi (Expandable)
    st.markdown("---")
    
    # Hitung komponen selisih absensi
    missing_records = max(0, selisih_absensi - total_leave)
    missing_records_percentage = (missing_records / total_work_day * 100) if total_work_day > 0 else 0
    
    with st.expander("📝 **Penjelasan Selisih Absensi**", expanded=False):
        # Tampilkan tabel penyebab selisih absensi
        st.markdown("**🔍 Penyebab Selisih Absensi:**")
        breakdown_data = {
            'Penyebab': ['✈️ Total Cuti', '📋 Missing Records', '**Total Selisih**'],
            'Jumlah': [total_leave, missing_records, selisih_absensi],
            'Persentase': [f'{leave_percentage:.1f}%', f'{missing_records_percentage:.1f}%', f'{selisih_absensi_percentage:.1f}%']
        }
        breakdown_df = pd.DataFrame(breakdown_data)
        st.dataframe(breakdown_df, use_container_width=True, hide_index=True)
        
        st.markdown(f"""
        **💡 Penjelasan Singkat:**
        
        Selisih Absensi ({selisih_absensi} hari) adalah selisih antara Total Work Day ({total_work_day}) dengan jumlah Total Kehadiran ({total_present}) dan Total Tidak Hadir ({total_absent}).
        
        **Diakibatkan oleh:**
        - **Cuti:** {total_leave} hari - Hari kerja yang digunakan untuk cuti
        - **Missing Records:** {missing_records} hari - Data tidak lengkap atau belum diinput
        
        **Formula:** `{total_work_day} - {total_present} - {total_absent} = {selisih_absensi} hari`
        """)
        
        # Analisis Missing Records per Karyawan
        if missing_records > 0:
            st.markdown("---")
            st.markdown("### 📋 Detail Missing Records")
            
            # Hitung missing records per karyawan
            employee_record_count = filtered_df.groupby('Employee ID').agg({
                'Is Present': 'sum',
                'Is Absent': 'sum',
                'Is Leave': 'sum',
                'Date': 'count'
            }).reset_index()
            employee_record_count.columns = ['Employee ID', 'Present', 'Absent', 'Leave', 'Total Records']
            employee_record_count['Expected Records'] = work_days_month
            employee_record_count['Work Day Records'] = employee_record_count['Present'] + employee_record_count['Absent'] + employee_record_count['Leave']
            employee_record_count['Missing Records'] = employee_record_count['Expected Records'] - employee_record_count['Work Day Records']
            
            # Filter karyawan yang memiliki missing records
            employees_with_missing = employee_record_count[employee_record_count['Missing Records'] > 0].copy()
            
            if len(employees_with_missing) > 0:
                # Get employee names
                employee_names = filtered_df[['Employee ID', 'Full Name']].drop_duplicates().set_index('Employee ID')['Full Name']
                employees_with_missing['Full Name'] = employees_with_missing['Employee ID'].map(employee_names)
                
                # Sort by missing records descending
                employees_with_missing = employees_with_missing.sort_values('Missing Records', ascending=False)
                
                st.markdown(f"**Total Missing Records: {missing_records} hari dari {len(employees_with_missing)} karyawan**")
                
                # Display table
                display_cols = ['Full Name', 'Employee ID', 'Expected Records', 'Present', 'Absent', 'Leave', 'Work Day Records', 'Missing Records']
                display_df = employees_with_missing[display_cols].copy()
                display_df.columns = ['Nama Karyawan', 'Employee ID', 'Seharusnya', 'Hadir', 'Tidak Hadir', 'Cuti', 'Total Terklasifikasi', 'Missing']
                display_df = display_df.reset_index(drop=True)
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                st.markdown(f"""
                **Penjelasan:**
                - Missing Records menunjukkan hari kerja yang seharusnya ada record (untuk {work_days_month} hari kerja), tapi tidak ada dalam data
                - Bisa terjadi karena data belum diinput atau tidak lengkap
                """)
            else:
                st.info(f"Tidak ada karyawan dengan missing records. Missing Records {missing_records} hari mungkin berasal dari record yang tidak terklasifikasi.")
    
    st.markdown("---")
    
    # Baris ketiga untuk Total Jam Kerja
    col_stat8, col_stat9 = st.columns(2)
    
    total_records_with_hours = len(filtered_df[filtered_df['Real Working Hour Decimal'] > 0])
    
    with col_stat8:
        help_text_real = (
            f"Formula: SUM(Real Working Hour Decimal)\n"
            f"Penjelasan: Menjumlahkan semua jam kerja real dari semua record absensi\n"
            f"Total Record: {len(filtered_df):,} record\n"
            f"Record dengan Jam Kerja: {total_records_with_hours:,} record\n"
            f"Hasil {total_jam_kerja_real_formatted} menunjukkan total jam kerja aktual dari semua record"
        )
        st.metric("Total Jam Kerja", total_jam_kerja_real_formatted, help=help_text_real)
    
    with col_stat9:
        help_text_plant = (
            f"Formula: Total Work Day × 8 jam\n"
            f"Penjelasan: Total jam kerja ideal (Plan) = {total_work_day} × 8 = {total_jam_kerja_plant:.2f} jam\n"
            f"Ini adalah total jam kerja ideal jika semua karyawan bekerja 8 jam per hari kerja"
        )
        st.metric("Plan Jam Kerja", total_jam_kerja_plant_formatted, help=help_text_plant)
    
    # Perbandingan Plan vs Actual
    st.markdown("### 📊 Perbandingan Plan vs Actual")
    
    plant_total_hours = total_work_day * 8
    plant_total_formatted = format_hours(plant_total_hours)
    
    # Hitung selisih dan persentase
    selisih_hours = total_jam_kerja_real - plant_total_hours
    persentase = (total_jam_kerja_real / plant_total_hours * 100) if plant_total_hours > 0 else 0
    selisih_formatted = format_hours(abs(selisih_hours))
    delta_color = "normal" if selisih_hours >= 0 else "inverse"
    
    col_plant1, col_plant2, col_plant3 = st.columns(3)
    
    with col_plant1:
        st.metric(
            "Plan (Ideal)",
            plant_total_formatted,
            help=f"Formula: Total Work Day × 8 jam\n= {total_work_day} × 8 = {plant_total_hours:.2f} jam\nTotal Work Day = {total_employees} karyawan × {work_days_month} hari = {total_work_day}\nIni adalah total jam kerja ideal jika semua karyawan bekerja 8 jam per hari kerja"
        )
    
    with col_plant2:
        st.metric(
            "Actual (Real)",
            total_jam_kerja_real_formatted,
            help=f"Formula: SUM dari Analisis Per Karyawan (Real Working Hour Decimal)\n= {total_jam_kerja_real:.2f} jam\nIni adalah total jam kerja aktual dari data absensi yang dihitung per karyawan"
        )
    
    with col_plant3:
        st.metric(
            "Selisih",
            f"{selisih_formatted} ({persentase:.1f}%)",
            delta=f"{selisih_hours:+.2f} jam",
            delta_color=delta_color,
            help=f"Selisih: Actual - Plan\n= {total_jam_kerja_real:.2f} - {plant_total_hours:.2f} = {selisih_hours:+.2f} jam\nPersentase: (Actual / Plan) × 100% = {persentase:.1f}%"
        )
    
    # Download Ringkasan Statistik
    summary_data = {
        'Metrik': ['Total Karyawan', 'Work Day', 'Total Work Day', 'Total Kehadiran', 'Total Kehadiran (%)', 
                   'Total Tidak Hadir', 'Total Tidak Hadir (%)', 'Total Jam Kerja', 'Plan Jam Kerja'],
        'Nilai': [total_employees, work_days_month, total_work_day, total_present, f"{attendance_percentage:.2f}%", 
                 total_absent, f"{absent_percentage:.2f}%", total_jam_kerja_real_formatted, total_jam_kerja_plant_formatted]
    }
    summary_df = pd.DataFrame(summary_data)
    csv_summary = summary_df.to_csv(index=False)
    
    col_summary1, col_summary2 = st.columns(2)
    with col_summary1:
        st.download_button(
            label="📥 Download Ringkasan Statistik (CSV)",
            data=csv_summary,
            file_name=f"ringkasan_statistik_{selected_branch}_{selected_org}.csv",
            mime="text/csv",
            key='download_summary_csv'
        )
    with col_summary2:
        pdf_summary = create_table_pdf(
            summary_df,
            "RINGKASAN STATISTIK",
            f"Branch: {selected_branch} | Organization: {selected_org if selected_org != 'All' else 'Semua'}"
        )
        st.download_button(
            label="📄 Download Ringkasan Statistik (PDF)",
            data=pdf_summary.getvalue(),
            file_name=f"ringkasan_statistik_{selected_branch}_{selected_org}.pdf",
            mime="application/pdf",
            key='download_summary_pdf'
        )
    
    st.markdown("---")

