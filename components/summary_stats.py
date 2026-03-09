"""Summary statistics component"""
import streamlit as st
import pandas as pd
from utils.formatters import format_hours
from utils.calculations import calculate_employee_stats
from reports.pdf_report import create_table_pdf


def render_summary_stats(filtered_df, work_days_month, employee_stats_full, selected_branch, selected_org, total_employees_baseline=None):
    """Render ringkasan statistik. total_employees_baseline: jika diisi (mis. dari Januari), dipakai untuk Total Karyawan dan Total Work Day."""
    st.header("📈 Ringkasan Statistik")

    # Total Karyawan: pakai baseline (Januari) jika ada, agar konsisten antar bulan
    total_employees = total_employees_baseline if total_employees_baseline is not None else filtered_df['Employee ID'].nunique()
    total_present = filtered_df['Is Present'].sum()
    total_leave = filtered_df['Is Leave'].sum()
    total_dayoff = filtered_df['Is Dayoff'].sum()
    total_work_day = total_employees * work_days_month
    # Total Tidak Hadir = sisa hari kerja yang bukan hadir, sehingga Total Kehadiran + Total Tidak Hadir = Total Work Day
    total_tidak_hadir = total_work_day - total_present
    # Hitung persentase relatif terhadap Total Work Day
    attendance_percentage = (total_present / total_work_day * 100) if total_work_day > 0 else 0
    absent_percentage = (total_tidak_hadir / total_work_day * 100) if total_work_day > 0 else 0

    # Hitung total jam kerja
    total_jam_kerja_real = employee_stats_full['Total Jam Kerja (Real)'].sum()
    total_jam_kerja_plant = total_work_day * 8
    total_jam_kerja_real_formatted = format_hours(total_jam_kerja_real)
    total_jam_kerja_plant_formatted = format_hours(total_jam_kerja_plant)
    
    # Tampilkan metrik baris pertama (Total Kehadiran + Total Tidak Hadir = Total Work Day)
    col_stat1, col_stat2, col_stat3, col_stat4, col_stat5 = st.columns(5)
    
    with col_stat1:
        help_total = "Formula: COUNT(DISTINCT Employee ID). Baseline Januari dipakai agar konsisten di semua bulan." if total_employees_baseline is not None else "Formula: COUNT(DISTINCT Employee ID)"
        st.metric("Total Karyawan", total_employees, help=help_total)
    with col_stat2:
        st.metric("Work Day", work_days_month, help="Formula: Jumlah hari kerja (Senin-Jumat) dalam bulan, dikurangi hari libur")
    with col_stat3:
        st.metric("Total Work Day", total_work_day, help=f"Formula: Total Karyawan × Work Day\n= {total_employees} × {work_days_month} = {total_work_day}\n\nTotal Kehadiran + Total Tidak Hadir = Total Work Day")
    with col_stat4:
        st.metric("Total Kehadiran", f"{total_present} ({attendance_percentage:.1f}%)", 
                 help=f"Formula: SUM(Is Present)\nPersentase: (Total Kehadiran / Total Work Day) × 100%\nTotal Kehadiran + Total Tidak Hadir = Total Work Day")
    with col_stat5:
        st.metric("Total Tidak Hadir", f"{int(total_tidak_hadir)} ({absent_percentage:.1f}%)", 
                 help=f"Formula: Total Work Day - Total Kehadiran = {total_work_day} - {total_present} = {int(total_tidak_hadir)}\nPersentase: (Total Tidak Hadir / Total Work Day) × 100%\nTotal Kehadiran + Total Tidak Hadir = Total Work Day")
    
    # Baris kedua untuk Cuti dan Hari Libur
    col_second1, col_second2 = st.columns(2)
    leave_percentage = (total_leave / total_work_day * 100) if total_work_day > 0 else 0
    
    with col_second1:
        st.metric("✈️ Total Cuti", f"{total_leave} ({leave_percentage:.1f}%)", 
                 help=f"Formula: SUM(Is Leave)\nPersentase: (Total Cuti / Total Work Day) × 100%")
    with col_second2:
        st.metric("🏖️ Total Hari Libur", f"{total_dayoff}", 
                 help="Formula: SUM(Is Dayoff). Hari libur tidak masuk dalam Total Work Day.")
    
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
    
    persentase_actual = (total_jam_kerja_real / plant_total_hours * 100) if plant_total_hours > 0 else 0
    
    col_plant1, col_plant2 = st.columns(2)
    
    with col_plant1:
        st.metric(
            "Plan (Ideal)",
            f"{plant_total_formatted} (100%)",
            help=f"Formula: Total Work Day × 8 jam\n= {total_work_day} × 8 = {plant_total_hours:.2f} jam\n100% = baseline referensi"
        )
    
    with col_plant2:
        st.metric(
            "Actual (Real)",
            f"{total_jam_kerja_real_formatted} ({persentase_actual:.1f}%)",
            help=f"Formula: SUM dari Analisis Per Karyawan (Real Working Hour Decimal)\nPersentase: (Actual / Plan) × 100% = {persentase_actual:.1f}%"
        )
    
    # Download Ringkasan Statistik
    summary_data = {
        'Metrik': ['Total Karyawan', 'Work Day', 'Total Work Day', 'Total Kehadiran', 'Total Kehadiran (%)', 
                   'Total Tidak Hadir', 'Total Tidak Hadir (%)', 'Total Jam Kerja', 'Plan Jam Kerja'],
        'Nilai': [total_employees, work_days_month, total_work_day, total_present, f"{attendance_percentage:.2f}%", 
                 int(total_tidak_hadir), f"{absent_percentage:.2f}%", total_jam_kerja_real_formatted, total_jam_kerja_plant_formatted]
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

