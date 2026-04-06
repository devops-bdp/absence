"""Employee detail component"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.data_loader import parse_check_in_to_minutes
from utils.formatters import format_hours
from utils.calculations import get_check_in_deadline_minutes
from reports.pdf_report import create_table_pdf


def render_personal_summary_stats_for_employee(selected_employee, employee_stats, filtered_df, work_days_month, selected_branch, selected_org):
    """Render ringkasan statistik untuk 1 karyawan yang dipilih"""
    st.header("📈 Ringkasan Statistik")
    
    # Get employee data
    emp_data = employee_stats[employee_stats['Full Name'] == selected_employee].iloc[0]
    emp_detail = filtered_df[filtered_df['Full Name'] == selected_employee].copy()
    
    # Untuk personal, total karyawan = 1
    total_employees = 1
    
    # Hitung metrik untuk karyawan yang dipilih
    total_present = emp_detail['Is Present'].sum()
    total_absent = emp_detail['Is Absent'].sum()
    total_work_day = total_employees * work_days_month
    # Hitung persentase relatif terhadap Total Work Day
    attendance_percentage = (total_present / total_work_day * 100) if total_work_day > 0 else 0
    absent_percentage = (total_absent / total_work_day * 100) if total_work_day > 0 else 0
    
    # Hitung total jam kerja untuk karyawan yang dipilih
    total_jam_kerja_real = emp_data['Total Jam Kerja (Real)']
    total_jam_kerja_plant = total_work_day * 8
    total_jam_kerja_real_formatted = format_hours(total_jam_kerja_real)
    total_jam_kerja_plant_formatted = format_hours(total_jam_kerja_plant)
    
    # Tampilkan metrik dalam 2 baris
    col_stat1, col_stat2, col_stat3, col_stat4, col_stat5 = st.columns(5)
    
    with col_stat1:
        st.metric("Total Karyawan", total_employees, help="Formula: COUNT(DISTINCT Employee ID) = 1 (untuk detail personal)")
    with col_stat2:
        st.metric("Work Day", work_days_month, help="Formula: Jumlah hari kerja (Senin-Jumat) dalam bulan")
    with col_stat3:
        st.metric("Total Work Day", total_work_day, help="Formula: Total Karyawan × Work Day = 1 × Work Day")
    with col_stat4:
        st.metric("Total Kehadiran", f"{int(total_present)} ({attendance_percentage:.1f}%)", 
                 help=f"Formula: SUM(Is Present) untuk karyawan ini\nPersentase: (Total Kehadiran / Total Work Day) × 100%")
    with col_stat5:
        st.metric("Total Tidak Hadir", f"{int(total_absent)} ({absent_percentage:.1f}%)", 
                 help=f"Formula: SUM(Is Absent) untuk karyawan ini\nPersentase: (Total Tidak Hadir / Total Work Day) × 100%")
    
    # Baris kedua untuk Total Jam Kerja
    col_stat6, col_stat7 = st.columns(2)
    
    total_records_with_hours = len(emp_detail[emp_detail['Real Working Hour Decimal'] > 0])
    
    with col_stat6:
        help_text_real = (
            f"Formula: SUM(Real Working Hour Decimal) untuk karyawan ini\n"
            f"Penjelasan: Menjumlahkan semua jam kerja real dari record absensi karyawan ini\n"
            f"Total Record: {len(emp_detail):,} record\n"
            f"Record dengan Jam Kerja: {total_records_with_hours:,} record\n"
            f"Hasil {total_jam_kerja_real_formatted} menunjukkan total jam kerja aktual untuk karyawan ini"
        )
        st.metric("Total Jam Kerja", total_jam_kerja_real_formatted, help=help_text_real)
    
    with col_stat7:
        help_text_plant = (
            f"Formula: Total Work Day × 8 jam\n"
            f"Penjelasan: Total jam kerja ideal (Plan) = {total_work_day} × 8 = {total_jam_kerja_plant:.2f} jam\n"
            f"Ini adalah total jam kerja ideal untuk 1 karyawan jika bekerja 8 jam per hari kerja"
        )
        st.metric("Plan Jam Kerja", total_jam_kerja_plant_formatted, help=help_text_plant)
    
    # Perbandingan Plan vs Actual
    st.markdown("### 📊 Perbandingan Plan vs Actual")
    
    plant_total_hours = total_work_day * 8
    plant_total_formatted = format_hours(plant_total_hours)
    
    # Hitung selisih dan persentase
    selisih_hours = total_jam_kerja_real - plant_total_hours
    persentase_actual = (total_jam_kerja_real / plant_total_hours * 100) if plant_total_hours > 0 else 0
    persentase_selisih = persentase_actual - 100
    selisih_formatted = format_hours(abs(selisih_hours))
    
    col_plant1, col_plant2, col_plant3 = st.columns(3)
    
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
            help=f"Formula: SUM dari Real Working Hour Decimal untuk karyawan ini\nPersentase: (Actual / Plan) × 100% = {persentase_actual:.1f}%"
        )
    
    with col_plant3:
        st.metric(
            "Selisih",
            f"{selisih_formatted} ({persentase_selisih:+.1f}%)",
            help=f"Selisih: Actual - Plan = {selisih_hours:+.2f} jam\nPersentase selisih: {persentase_selisih:+.1f}% (positif = di atas plan, negatif = di bawah plan)"
        )
        # Highlight selisih jam dengan warna kuning (bukan hijau/merah)
        st.markdown(
            f"<p style='margin-top: -0.5rem; color: #B8860B; font-weight: 600; font-size: 0.95rem;'>{selisih_hours:+.2f} jam</p>",
            unsafe_allow_html=True
        )
    
    # Download Ringkasan Statistik Personal
    summary_data = {
        'Metrik': ['Total Karyawan', 'Work Day', 'Total Work Day', 'Total Kehadiran', 'Total Kehadiran (%)', 
                   'Total Tidak Hadir', 'Total Tidak Hadir (%)', 'Total Jam Kerja', 'Plan Jam Kerja'],
        'Nilai': [total_employees, work_days_month, total_work_day, int(total_present), f"{attendance_percentage:.2f}%", 
                 int(total_absent), f"{absent_percentage:.2f}%", total_jam_kerja_real_formatted, total_jam_kerja_plant_formatted]
    }
    summary_df = pd.DataFrame(summary_data)
    csv_summary = summary_df.to_csv(index=False)
    
    col_summary1, col_summary2 = st.columns(2)
    with col_summary1:
        st.download_button(
            label="📥 Download Ringkasan Statistik (CSV)",
            data=csv_summary,
            file_name=f"ringkasan_statistik_personal_{selected_employee.replace(' ', '_')}_{selected_branch}_{selected_org}.csv",
            mime="text/csv",
            key='download_summary_personal_csv'
        )
    with col_summary2:
        pdf_summary = create_table_pdf(
            summary_df,
            f"RINGKASAN STATISTIK PERSONAL - {selected_employee}",
            f"Branch: {selected_branch} | Organization: {selected_org if selected_org != 'All' else 'Semua'}"
        )
        st.download_button(
            label="📄 Download Ringkasan Statistik (PDF)",
            data=pdf_summary.getvalue(),
            file_name=f"ringkasan_statistik_personal_{selected_employee.replace(' ', '_')}_{selected_branch}_{selected_org}.pdf",
            mime="application/pdf",
            key='download_summary_personal_pdf'
        )


def get_status(row):
    """Get status untuk setiap hari"""
    if row['Is Present']:
        return '✅ Hadir'
    elif row['Is Leave']:
        return '✈️ Cuti'
    elif row['Is Dayoff']:
        return '🏖️ Hari Libur'
    elif row['Is Absent']:
        return '❌ Absen'
    else:
        return '❓ Tidak Diketahui'


def render_employee_detail(employee_stats, filtered_df, work_days_month=None, selected_branch=None, selected_org=None):
    """Render detail per karyawan"""
    st.header("🔍 Detail Per Karyawan")
    
    # Search box untuk memilih karyawan
    employee_list = sorted(employee_stats['Full Name'].unique())
    search_employee = st.text_input("🔍 Cari Karyawan", "", placeholder="Ketik nama atau ID karyawan...")
    
    if search_employee:
        filtered_employees = [
            emp for emp in employee_list 
            if search_employee.lower() in emp.lower() or 
            search_employee in str(employee_stats[employee_stats['Full Name'] == emp]['Employee ID'].iloc[0])
        ]
        if filtered_employees:
            selected_employee = st.selectbox("Pilih Karyawan", options=filtered_employees, key='employee_select')
        else:
            st.warning("Karyawan tidak ditemukan")
            selected_employee = None
    else:
        selected_employee = st.selectbox("Pilih Karyawan", options=employee_list, key='employee_select')
    
    if selected_employee:
        # Render Summary Statistik Personal untuk karyawan yang dipilih
        if work_days_month is not None:
            render_personal_summary_stats_for_employee(
                selected_employee, employee_stats, filtered_df, work_days_month, selected_branch, selected_org
            )
            st.markdown("---")
        emp_data = employee_stats[employee_stats['Full Name'] == selected_employee].iloc[0]
        emp_detail = filtered_df[filtered_df['Full Name'] == selected_employee].copy()
        
        # Header dengan informasi karyawan
        st.markdown("### 👤 Informasi Karyawan")
        info_col1, info_col2, info_col3, info_col4 = st.columns(4)
        
        with info_col1:
            st.markdown(f"**🆔 Employee ID**  \n{emp_data['Employee ID']}")
        with info_col2:
            st.markdown(f"**🏢 Branch**  \n{emp_data['Branch']}")
        with info_col3:
            st.markdown(f"**🏛️ Organization**  \n{emp_data['Organization']}")
        with info_col4:
            st.markdown(f"**💼 Posisi**  \n{emp_data['Job Position']}")
        
        st.markdown("---")
        
        # Statistik utama — dihitung dulu yang dipakai di beberapa metrik
        total_work_8_hours = len(emp_detail[emp_detail['Real Working Hour Decimal'] >= 8])
        emp_detail_with_checkin = emp_detail[emp_detail['Check In'].notna() & (emp_detail['Check In'] != '')].copy()
        if len(emp_detail_with_checkin) > 0:
            emp_detail_with_checkin['Check In Minutes'] = emp_detail_with_checkin['Check In'].apply(parse_check_in_to_minutes)
            emp_detail_with_checkin['Deadline Minutes'] = emp_detail_with_checkin['Date'].apply(get_check_in_deadline_minutes)
            total_clock_on_time = len(emp_detail_with_checkin[
                emp_detail_with_checkin['Check In Minutes'].notna() &
                (emp_detail_with_checkin['Check In Minutes'] <= emp_detail_with_checkin['Deadline Minutes'])
            ])
        else:
            total_clock_on_time = 0
        total_sick = int(emp_detail['Is Sick'].sum()) if 'Is Sick' in emp_detail.columns else 0
        n_days = len(emp_detail)
        attendance_rate = (emp_data['Jumlah Hadir'] / emp_data['Work Days Bulan Ini'] * 100) if emp_data['Work Days Bulan Ini'] > 0 else 0
        work_8_pct = (total_work_8_hours / n_days * 100) if n_days > 0 else 0
        clock_on_time_pct = (total_clock_on_time / n_days * 100) if n_days > 0 else 0

        st.markdown("### 📊 Statistik Absensi Bulan Ini")
        st.caption("Ringkasan kehadiran, pelanggaran waktu, dan jam kerja untuk bulan ini.")

        # Baris 1: Kehadiran dasar (4 kolom)
        r1_1, r1_2, r1_3, r1_4 = st.columns(4)
        with r1_1:
            st.metric("📅 Work Days Bulan Ini", int(emp_data['Work Days Bulan Ini']), help="Hari kerja yang seharusnya")
        with r1_2:
            st.metric("✅ Jumlah Hadir", int(emp_data['Jumlah Hadir']), delta=f"{attendance_rate:.1f}%", delta_color="normal", help="Total hari hadir")
        with r1_3:
            st.metric("❌ Jumlah Absen", int(emp_data['Jumlah Absen']), delta_color="inverse", help="Total hari tidak hadir")
        with r1_4:
            st.metric("🏖️ Hari Libur", int(emp_data['Jumlah Hari Libur']), help="Total hari libur")

        # Baris 2: Cuti, Sakit, pelanggaran (4 kolom)
        r2_1, r2_2, r2_3, r2_4 = st.columns(4)
        with r2_1:
            st.metric("✈️ Cuti", int(emp_data['Jumlah Cuti']), help="Total hari cuti")
        with r2_2:
            st.metric("🤒 Sakit", total_sick, help="Total hari sakit (Attendance Code = S)")
        with r2_3:
            st.metric("⏰ Late In", int(emp_data['Jumlah Late In']), delta_color="inverse", help="Jumlah keterlambatan")
        with r2_4:
            st.metric("🚪 Early Out", int(emp_data['Jumlah Early Out']), delta_color="inverse", help="Jumlah pulang lebih cepat")

        # Baris 3: Jam kerja & compliance (3 kolom)
        r3_1, r3_2, r3_3 = st.columns(3)
        with r3_1:
            st.metric("⏱️ Total Jam Kerja", emp_data['Total Jam Kerja (Real) Formatted'], help="Total jam kerja (Real Working Hour)")
        with r3_2:
            st.metric("⏰ Total Work 8 Hours", total_work_8_hours, delta=f"{work_8_pct:.1f}%", delta_color="normal",
                     help="Hari bekerja ≥ 8 jam (Ramadan: istirahat 30 menit, total tetap 8 jam)")
        with r3_3:
            st.metric("🕐 Jam Masuk On Time", total_clock_on_time, delta=f"{clock_on_time_pct:.1f}%", delta_color="normal",
                     help="Tepat waktu jika Check In ≤ batas tanggal: Mar 1–17/2026 → 07:30; Feb 19–28/2026 → 07:45; lainnya → 08:15")

        st.markdown("---")
        
        # Visualisasi ringkasan
        viz_col1, viz_col2 = st.columns(2)
        
        with viz_col1:
            attendance_data = {
                'Hadir': int(emp_data['Jumlah Hadir']),
                'Absen': int(emp_data['Jumlah Absen']),
                'Cuti': int(emp_data['Jumlah Cuti']),
                'Hari Libur': int(emp_data['Jumlah Hari Libur'])
            }
            fig_pie = px.pie(
                values=list(attendance_data.values()),
                names=list(attendance_data.keys()),
                title="Distribusi Kehadiran Bulan Ini",
                color_discrete_map={
                    'Hadir': '#2ecc71',
                    'Absen': '#e74c3c',
                    'Cuti': '#3498db',
                    'Hari Libur': '#f39c12'
                }
            )
            fig_pie.update_layout(height=350)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with viz_col2:
            violation_data = {
                'Late In': int(emp_data['Jumlah Late In']),
                'Early Out': int(emp_data['Jumlah Early Out'])
            }
            fig_bar = px.bar(
                x=list(violation_data.keys()),
                y=list(violation_data.values()),
                title="Pelanggaran Waktu Kerja",
                labels={'x': 'Jenis Pelanggaran', 'y': 'Jumlah'},
                color=list(violation_data.keys()),
                color_discrete_map={
                    'Late In': '#e74c3c',
                    'Early Out': '#f39c12'
                }
            )
            fig_bar.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)
        
        st.markdown("---")
        
        # Line chart jam masuk per hari kerja
        st.markdown("### 📈 Jam Masuk per Hari Kerja")
        
        min_date_chart = emp_detail['Date'].min().date() if not emp_detail['Date'].empty else pd.Timestamp.now().date()
        max_date_chart = emp_detail['Date'].max().date() if not emp_detail['Date'].empty else pd.Timestamp.now().date()
        
        work_days_data = emp_detail[
            (emp_detail['Is Present'] == True) & 
            (emp_detail['Is Dayoff'] == False) &
            (emp_detail['Date'].dt.date >= min_date_chart) &
            (emp_detail['Date'].dt.date <= max_date_chart)
        ].copy()
        
        if len(work_days_data) > 0:
            work_days_data['Check In Minutes'] = work_days_data['Check In'].apply(parse_check_in_to_minutes)
            work_days_data = work_days_data[work_days_data['Check In Minutes'].notna()].copy()
            
            if len(work_days_data) > 0:
                work_days_data = work_days_data.sort_values('Date')
                
                fig_check_in = go.Figure()
                fig_check_in.add_trace(go.Scatter(
                    x=work_days_data['Date'],
                    y=work_days_data['Check In Minutes'],
                    mode='lines+markers',
                    name='Jam Masuk Aktual',
                    line=dict(color='#3498db', width=2),
                    marker=dict(size=6, color='#3498db'),
                    hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Jam Masuk: %{customdata}<extra></extra>',
                    customdata=work_days_data['Check In']
                ))
                
                plant_time_minutes = 8 * 60
                fig_check_in.add_hline(
                    y=plant_time_minutes,
                    line_dash="dash",
                    line_color="red",
                    annotation_text="Plan 08:00",
                    annotation_position="right",
                    annotation=dict(font_size=12, font_color="red")
                )
                
                min_minutes = max(0, int(work_days_data['Check In Minutes'].min()) - 60)
                max_minutes = min(24*60, int(work_days_data['Check In Minutes'].max()) + 60)
                
                tick_vals = []
                tick_texts = []
                start_tick = (min_minutes // 30) * 30
                end_tick = ((max_minutes // 30) + 1) * 30
                
                for minutes in range(start_tick, end_tick + 1, 30):
                    if minutes <= 24*60:
                        tick_vals.append(minutes)
                        hours = minutes // 60
                        mins = minutes % 60
                        tick_texts.append(f"{hours:02d}:{mins:02d}")
                
                fig_check_in.update_layout(
                    title="Jam Masuk per Hari Kerja",
                    xaxis_title="Tanggal",
                    yaxis_title="Jam Masuk",
                    height=400,
                    hovermode='x unified',
                    yaxis=dict(tickmode='array', tickvals=tick_vals, ticktext=tick_texts, range=[min_minutes, max_minutes]),
                    xaxis=dict(tickformat='%Y-%m-%d', tickangle=-45)
                )
                
                st.plotly_chart(fig_check_in, use_container_width=True)
            else:
                st.info("Tidak ada data jam masuk yang valid untuk ditampilkan")
        else:
            st.info("Tidak ada data hari kerja untuk ditampilkan")
        
        st.markdown("---")
        
        # Tabel detail harian
        st.markdown("### 📋 Detail Harian")
        
        detail_date_col1, detail_date_col2 = st.columns(2)
        with detail_date_col1:
            min_date_detail = emp_detail['Date'].min().date() if not emp_detail['Date'].empty else pd.Timestamp.now().date()
            max_date_detail = emp_detail['Date'].max().date() if not emp_detail['Date'].empty else pd.Timestamp.now().date()
            detail_date_start = st.date_input("Tanggal Mulai", value=min_date_detail, min_value=min_date_detail, max_value=max_date_detail, key='detail_start')
        with detail_date_col2:
            detail_date_end = st.date_input("Tanggal Akhir", value=max_date_detail, min_value=min_date_detail, max_value=max_date_detail, key='detail_end')
        
        emp_detail_filtered = emp_detail[
            (emp_detail['Date'].dt.date >= detail_date_start) &
            (emp_detail['Date'].dt.date <= detail_date_end)
        ].copy()
        
        emp_detail_filtered['Status'] = emp_detail_filtered.apply(get_status, axis=1)
        
        # Compliance: minimum 8 jam kerja per hari (Ramadan istirahat 30 menit, total tetap 8 jam)
        emp_detail_filtered['Compliance'] = emp_detail_filtered.apply(
            lambda row: '✅' if (row['Real Working Hour Decimal'] >= 8) else '❌',
            axis=1
        )
        
        # Kolom Check In Range: batas per tanggal (Mar 1–17 → 07:30, Feb 19–28 → 07:45, normal 08:15)
        def check_in_time_range(row):
            check_in_minutes = parse_check_in_to_minutes(row['Check In'])
            if check_in_minutes is None:
                return '❌'
            deadline = get_check_in_deadline_minutes(row['Date'])
            return '✅' if check_in_minutes <= deadline else '❌'
        
        emp_detail_filtered['Check In Range'] = emp_detail_filtered.apply(check_in_time_range, axis=1)
        
        detail_cols = ['Date', 'Status', 'Compliance', 'Check In Range', 'Shift', 'Check In', 'Check Out', 'Late In', 'Early Out', 
                      'Real Working Hour', 'Actual Working Hour', 'Attendance Code']
        detail_display = emp_detail_filtered[detail_cols].copy()
        detail_display = detail_display.sort_values('Date', ascending=False)
        detail_display['Date'] = detail_display['Date'].dt.strftime('%Y-%m-%d (%A)')
        
        detail_display.columns = [
            'Tanggal', 'Status', '8 Hour Working Time', 'Jam Masuk (≤07.30 / ≤07.45 / ≤08.15)', 'Shift', 'Check In', 'Check Out', 'Late In', 'Early Out',
            'Jam Kerja (Real)', 'Jam Kerja (Actual)', 'Kode Absensi'
        ]
        
        status_filter = st.multiselect(
            "Filter Status",
            options=['✅ Hadir', '✈️ Cuti', '🏖️ Hari Libur', '❌ Absen'],
            default=['✅ Hadir', '✈️ Cuti', '🏖️ Hari Libur', '❌ Absen'],
            key='status_filter'
        )
        
        if status_filter:
            detail_display = detail_display[detail_display['Status'].isin(status_filter)]
        
        st.dataframe(detail_display, use_container_width=True, height=400, hide_index=True)
        
        # Download button untuk detail harian
        csv_detail = detail_display.to_csv(index=False)
        
        col_detail1, col_detail2 = st.columns(2)
        with col_detail1:
            st.download_button(
                label="📥 Download Detail Harian (CSV)",
                data=csv_detail,
                file_name=f"detail_harian_{selected_employee.replace(' ', '_')}_{detail_date_start}_{detail_date_end}.csv",
                mime="text/csv",
                key='download_detail_csv'
            )
        with col_detail2:
            pdf_detail = create_table_pdf(
                detail_display,
                f"DETAIL HARIAN - {selected_employee}",
                f"Periode: {detail_date_start} - {detail_date_end}"
            )
            st.download_button(
                label="📄 Download Detail Harian (PDF)",
                data=pdf_detail.getvalue(),
                file_name=f"detail_harian_{selected_employee.replace(' ', '_')}_{detail_date_start}_{detail_date_end}.pdf",
                mime="application/pdf",
                key='download_detail_pdf'
            )
        
        st.markdown("---")

