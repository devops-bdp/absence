"""Calculation utilities"""
import pandas as pd
from calendar import monthrange
import datetime


def calculate_work_days(year, month):
    """Hitung jumlah hari kerja (Senin-Jumat) dalam bulan tertentu"""
    # Dapatkan jumlah hari dalam bulan
    num_days = monthrange(year, month)[1]
    
    # Hitung hari kerja (Senin=0, Jumat=4)
    work_days = 0
    for day in range(1, num_days + 1):
        date = datetime.date(year, month, day)
        # 0 = Senin, 4 = Jumat
        if date.weekday() < 5:  # Senin sampai Jumat
            work_days += 1
    
    return work_days


def calculate_employee_stats(filtered_df, work_days_month):
    """Hitung statistik per karyawan"""
    employee_stats_full = filtered_df.groupby(['Employee ID', 'Full Name', 'Branch', 'Organization', 'Job Position']).agg({
        'Is Present': 'sum',
        'Is Absent': 'sum',
        'Is Dayoff': 'sum',
        'Is Leave': 'sum',
        'Is Late In': 'sum',
        'Is Early Out': 'sum',
        'Real Working Hour Decimal': 'sum',
        'Late In Decimal': 'sum',
        'Early Out Decimal': 'sum'
    }).reset_index()
    
    employee_stats_full.columns = [
        'Employee ID', 'Full Name', 'Branch', 'Organization', 'Job Position',
        'Jumlah Hadir', 'Jumlah Absen', 'Jumlah Hari Libur', 'Jumlah Cuti',
        'Jumlah Late In', 'Jumlah Early Out',
        'Total Jam Kerja (Real)',
        'Total Jam Late In', 'Total Jam Early Out'
    ]
    
    employee_stats_full['Work Days Bulan Ini'] = work_days_month
    employee_stats_full['Total Jam Kerja (Plan)'] = employee_stats_full['Work Days Bulan Ini'] * 8
    
    return employee_stats_full


def calculate_organization_stats(filtered_df, work_days_month):
    """Hitung statistik per organization"""
    org_stats = filtered_df.groupby('Organization').agg({
        'Employee ID': 'nunique',
        'Is Present': 'sum',
        'Is Absent': 'sum',
        'Is Leave': 'sum',
        'Is Late In': 'sum',
        'Is Early Out': 'sum',
        'Real Working Hour Decimal': 'sum'
    }).reset_index()
    
    org_stats.columns = [
        'Organization',
        'Total Karyawan',
        'Total Kehadiran',
        'Total Tidak Hadir',
        'Total Cuti',
        'Total Late In',
        'Total Early Out',
        'Total Jam Kerja (Real)'
    ]
    
    # Hitung metrik tambahan
    org_stats['Work Day'] = work_days_month
    org_stats['Total Work Day'] = org_stats['Total Karyawan'] * org_stats['Work Day']
    org_stats['Total Jam Kerja (Plan)'] = org_stats['Total Work Day'] * 8
    
    # Hitung persentase
    org_stats['Kehadiran (%)'] = (org_stats['Total Kehadiran'] / org_stats['Total Work Day'] * 100).round(2)
    org_stats['Tidak Hadir (%)'] = (org_stats['Total Tidak Hadir'] / org_stats['Total Work Day'] * 100).round(2)
    org_stats['Plan vs Actual (%)'] = (org_stats['Total Jam Kerja (Real)'] / org_stats['Total Jam Kerja (Plan)'] * 100).round(2)
    
    return org_stats

