"""Dashboard Personal page module - Individual/Personal dashboard"""
import streamlit as st
from utils.data_loader import load_data, filter_data
from utils.calculations import calculate_work_days, calculate_employee_stats
from components.sidebar import render_sidebar_filters
from utils.formatters import format_hours
import plotly.express as px
import plotly.graph_objects as go

def render_dashboard_personal():
    """Render the personal dashboard page"""
    st.title("📊 Dashboard Personal")
    st.markdown("---")

    # Load data
    df = load_data()

    if df is not None:
        # Sidebar untuk filter
        selected_branch, selected_org = render_sidebar_filters(df)
        
        # Filter data
        filtered_df = filter_data(df, selected_branch, selected_org)
        
        # Hitung work days bulan ini
        if not filtered_df['Date'].empty:
            first_date = filtered_df['Date'].min()
            year = first_date.year
            month = first_date.month
            work_days_month = calculate_work_days(year, month)
        else:
            work_days_month = 0
        
        # Hitung employee stats
        employee_stats_full = calculate_employee_stats(filtered_df, work_days_month)
        
        # Format jam kerja untuk employee_stats
        employee_stats_full['Total Jam Kerja (Real) Formatted'] = employee_stats_full['Total Jam Kerja (Real)'].apply(format_hours)
        employee_stats_full['Total Jam Kerja (Plan) Formatted'] = employee_stats_full['Total Jam Kerja (Plan)'].apply(format_hours)
        employee_stats_full['Total Jam Late In Formatted'] = employee_stats_full['Total Jam Late In'].apply(format_hours)
        employee_stats_full['Total Jam Early Out Formatted'] = employee_stats_full['Total Jam Early Out'].apply(format_hours)
        
        # Select employee untuk personal dashboard
        st.markdown("### 👤 Pilih Karyawan")
        employee_list = sorted(employee_stats_full['Full Name'].unique())
        selected_employee = st.selectbox(
            "Pilih Karyawan untuk melihat Dashboard Personal",
            options=employee_list,
            key='personal_employee_select'
        )
        
        if selected_employee:
            st.markdown("---")
            
            # Get employee data
            emp_data = employee_stats_full[employee_stats_full['Full Name'] == selected_employee].iloc[0]
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
            
            # Statistik Personal
            st.markdown("### 📊 Statistik Personal Bulan Ini")
            
            stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
            with stat_col1:
                attendance_rate = (emp_data['Jumlah Hadir'] / emp_data['Work Days Bulan Ini'] * 100) if emp_data['Work Days Bulan Ini'] > 0 else 0
                st.metric("📅 Work Days", int(emp_data['Work Days Bulan Ini']), help="Hari kerja yang seharusnya")
            with stat_col2:
                st.metric("✅ Jumlah Hadir", int(emp_data['Jumlah Hadir']), delta=f"{attendance_rate:.1f}%", delta_color="normal", help="Total hari hadir")
            with stat_col3:
                st.metric("❌ Jumlah Absen", int(emp_data['Jumlah Absen']), delta_color="inverse", help="Total hari tidak hadir")
            with stat_col4:
                st.metric("🏖️ Hari Libur", int(emp_data['Jumlah Hari Libur']), help="Total hari libur")
            
            stat_col5, stat_col6, stat_col7, stat_col8 = st.columns(4)
            with stat_col5:
                st.metric("✈️ Cuti", int(emp_data['Jumlah Cuti']), help="Total hari cuti")
            with stat_col6:
                st.metric("⏰ Late In", int(emp_data['Jumlah Late In']), delta_color="inverse", help="Jumlah keterlambatan")
            with stat_col7:
                st.metric("🚪 Early Out", int(emp_data['Jumlah Early Out']), delta_color="inverse", help="Jumlah pulang lebih cepat")
            with stat_col8:
                st.metric("⏱️ Total Jam Kerja", emp_data['Total Jam Kerja (Real) Formatted'], help="Total jam kerja (Real Working Hour)")
            
            st.markdown("---")
            
            # Visualisasi Personal
            viz_col1, viz_col2 = st.columns(2)
            
            with viz_col1:
                # Pie chart untuk distribusi kehadiran
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
                # Bar chart untuk late in dan early out
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
            
            min_date_chart = emp_detail['Date'].min().date() if not emp_detail['Date'].empty else None
            max_date_chart = emp_detail['Date'].max().date() if not emp_detail['Date'].empty else None
            
            if min_date_chart and max_date_chart:
                work_days_data = emp_detail[
                    (emp_detail['Is Present'] == True) & 
                    (emp_detail['Is Dayoff'] == False)
                ].copy()
                
                if len(work_days_data) > 0:
                    from utils.data_loader import parse_check_in_to_minutes
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
            
            # Perbandingan Plan vs Actual untuk Personal
            st.markdown("### 📊 Perbandingan Plan vs Actual (Personal)")
            
            plant_hours_personal = emp_data['Total Jam Kerja (Plan)']
            actual_hours_personal = emp_data['Total Jam Kerja (Real)']
            selisih_personal = actual_hours_personal - plant_hours_personal
            persentase_personal = (actual_hours_personal / plant_hours_personal * 100) if plant_hours_personal > 0 else 0
            
            col_plant1, col_plant2, col_plant3 = st.columns(3)
            
            with col_plant1:
                st.metric(
                    "Plan (Ideal)",
                    emp_data['Total Jam Kerja (Plan) Formatted'],
                    help=f"Total jam kerja ideal: {work_days_month} hari × 8 jam = {plant_hours_personal:.2f} jam"
                )
            
            with col_plant2:
                st.metric(
                    "Actual (Real)",
                    emp_data['Total Jam Kerja (Real) Formatted'],
                    help=f"Total jam kerja aktual dari data absensi"
                )
            
            with col_plant3:
                delta_color = "normal" if selisih_personal >= 0 else "inverse"
                st.metric(
                    "Selisih",
                    f"{format_hours(abs(selisih_personal))} ({persentase_personal:.1f}%)",
                    delta=f"{selisih_personal:+.2f} jam",
                    delta_color=delta_color,
                    help=f"Selisih: Actual - Plan = {selisih_personal:+.2f} jam"
                )
    else:
        st.error("Gagal memuat data. Pastikan file january.csv ada di direktori yang sama.")

