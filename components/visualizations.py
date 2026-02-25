"""Visualizations component"""
import streamlit as st
import plotly.express as px


def render_visualizations(employee_stats_full, selected_branch, work_days_month=None):
    """Render visualisasi data dengan tabs"""
    st.header("📊 Visualisasi Data")
    
    # Tab untuk berbagai visualisasi
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Jumlah Absensi",
        "⏱️ Jam Kerja",
        "⏰ Keterlambatan",
        "🚪 Early Out"
    ])
    
    with tab1:
        st.subheader("Jumlah Hadir Per Karyawan")
        # Top 20 karyawan dengan hadir terbanyak
        top_attendance = employee_stats_full.nlargest(20, 'Jumlah Hadir')
        fig1 = px.bar(
            top_attendance,
            x='Jumlah Hadir',
            y='Full Name',
            orientation='h',
            title="Top 20 Karyawan dengan Kehadiran Terbanyak",
            labels={'Full Name': 'Nama Karyawan', 'Jumlah Hadir': 'Jumlah Hadir'}
        )
        fig1.update_layout(height=600, yaxis={'categoryorder': 'total ascending'})
        # Garis vertikal Plan (target kehadiran)
        if work_days_month is not None:
            fig1.add_vline(
                x=work_days_month,
                line_dash="dash",
                line_color="green",
                annotation_text=f"Plan ({work_days_month} hari)",
                annotation_position="top"
            )
        st.plotly_chart(fig1, use_container_width=True)
        
        # Download data untuk chart ini
        csv_viz_attendance_tab = top_attendance[['Employee ID', 'Full Name', 'Jumlah Hadir']].to_csv(index=False)
        st.download_button(
            label="📥 Download Data Chart Ini (CSV)",
            data=csv_viz_attendance_tab,
            file_name=f"data_chart_jumlah_hadir_tab_{selected_branch}.csv",
            mime="text/csv",
            key='download_viz_attendance_tab1'
        )
    
    with tab2:
        st.subheader("Total Jam Kerja Per Karyawan")
        # Top 20 karyawan dengan jam kerja terbanyak
        top_hours = employee_stats_full.nlargest(20, 'Total Jam Kerja (Real)')
        fig4 = px.bar(
            top_hours,
            x='Total Jam Kerja (Real)',
            y='Full Name',
            orientation='h',
            title="Top 20 Karyawan dengan Jam Kerja Terbanyak",
            labels={'Full Name': 'Nama Karyawan', 'Total Jam Kerja (Real)': 'Total Jam Kerja'},
            color='Total Jam Kerja (Real)',
            color_continuous_scale='Greens'
        )
        fig4.update_layout(
            height=600,
            yaxis={'categoryorder': 'total ascending', 'automargin': True},
            margin=dict(l=180)
        )
        # Garis vertikal Plan (target jam kerja: work_days × 8 jam)
        if work_days_month is not None and work_days_month > 0:
            plan_hours = work_days_month * 8
            fig4.add_vline(
                x=plan_hours,
                line_dash="dash",
                line_color="green",
                annotation_text=f"Plan ({plan_hours} jam)",
                annotation_position="top"
            )
        st.plotly_chart(fig4, use_container_width=True)
        
        # Download data untuk chart jam kerja
        csv_viz_hours = top_hours[['Employee ID', 'Full Name', 'Total Jam Kerja (Real)']].to_csv(index=False)
        st.download_button(
            label="📥 Download Data Chart Jam Kerja (CSV)",
            data=csv_viz_hours,
            file_name=f"data_chart_jam_kerja_{selected_branch}.csv",
            mime="text/csv",
            key='download_viz_hours'
        )
    
    with tab3:
        st.subheader("Keterlambatan Per Karyawan")
        top_late = employee_stats_full[employee_stats_full['Jumlah Late In'] > 0].nlargest(20, 'Jumlah Late In')
        if len(top_late) > 0:
            fig2 = px.bar(
                top_late,
                x='Jumlah Late In',
                y='Full Name',
                orientation='h',
                title="Top 20 Karyawan dengan Keterlambatan Terbanyak",
                labels={'Full Name': 'Nama Karyawan', 'Jumlah Late In': 'Jumlah Keterlambatan'},
                color='Jumlah Late In',
                color_continuous_scale='Reds'
            )
            fig2.update_layout(height=600, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig2, use_container_width=True)
            csv_viz_late_tab = top_late[['Employee ID', 'Full Name', 'Jumlah Late In']].to_csv(index=False)
            st.download_button(
                label="📥 Download Data Chart Ini (CSV)",
                data=csv_viz_late_tab,
                file_name=f"data_chart_late_in_tab_{selected_branch}.csv",
                mime="text/csv",
                key='download_viz_late_tab2'
            )
        else:
            st.info("Tidak ada data keterlambatan")
    
    with tab4:
        st.subheader("Early Out Per Karyawan")
        top_early = employee_stats_full[employee_stats_full['Jumlah Early Out'] > 0].nlargest(20, 'Jumlah Early Out')
        if len(top_early) > 0:
            fig3 = px.bar(
                top_early,
                x='Jumlah Early Out',
                y='Full Name',
                orientation='h',
                title="Top 20 Karyawan dengan Early Out Terbanyak",
                labels={'Full Name': 'Nama Karyawan', 'Jumlah Early Out': 'Jumlah Early Out'},
                color='Jumlah Early Out',
                color_continuous_scale='Oranges'
            )
            fig3.update_layout(height=600, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig3, use_container_width=True)
            csv_viz_early = top_early[['Employee ID', 'Full Name', 'Jumlah Early Out']].to_csv(index=False)
            st.download_button(
                label="📥 Download Data Chart Early Out (CSV)",
                data=csv_viz_early,
                file_name=f"data_chart_early_out_{selected_branch}.csv",
                mime="text/csv",
                key='download_viz_early'
            )
        else:
            st.info("Tidak ada data early out")
    
    st.markdown("---")

