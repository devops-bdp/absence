"""Calculation utilities"""
import pandas as pd
from calendar import monthrange
import datetime

# Hari libur per bulan (tanggal): (year, month) -> [list of day of month]
# Hanya tanggal yang termasuk hari kerja (Senin–Jumat) yang mengurangi Work Day.
HOLIDAYS_BY_MONTH = {
    (2026, 1): [1, 16],   # Januari 2026: 1 = libur nasional tahun baru, 16 = cuti bersama
    (2026, 2): [1, 7, 8, 14, 15, 16, 17, 21, 22, 28],  # Februari 2026
}


def get_work_days_holidays(year, month):
    """Daftar tanggal hari libur di bulan tersebut (untuk referensi)."""
    return HOLIDAYS_BY_MONTH.get((year, month), [])


# Ramadan Feb 2026: tgl 19-28, range jam masuk 07:00–07:45 (batas = 07:45 = 465 menit)
# Di luar periode itu: batas 08:15 = 495 menit
RAMADAN_FEB_2026_START = 19
RAMADAN_FEB_2026_END = 28
CHECK_IN_DEADLINE_RAMADAN_MINUTES = 7 * 60 + 45   # 07:45
CHECK_IN_DEADLINE_NORMAL_MINUTES = 8 * 60 + 15     # 08:15

# Ramadan: istirahat di-adjust 30 menit; total working hours tetap 8 jam/hari (tidak ada 8.5 jam)


def get_check_in_deadline_minutes(date_or_ts):
    """Batas jam masuk (dalam menit dari 00:00). Feb 2026 tgl 19–28 (Ramadan): 07:45 = 465. Lainnya: 08:15 = 495."""
    if date_or_ts is None or (hasattr(date_or_ts, '__iter__') and pd.isna(date_or_ts)):
        return CHECK_IN_DEADLINE_NORMAL_MINUTES
    try:
        d = date_or_ts.date() if hasattr(date_or_ts, 'date') else date_or_ts
        if d.year == 2026 and d.month == 2 and RAMADAN_FEB_2026_START <= d.day <= RAMADAN_FEB_2026_END:
            return CHECK_IN_DEADLINE_RAMADAN_MINUTES
    except Exception:
        pass
    return CHECK_IN_DEADLINE_NORMAL_MINUTES


def calculate_work_days(year, month):
    """Hitung jumlah hari kerja (Senin-Jumat) dalam bulan tertentu, dikurangi hari libur."""
    num_days = monthrange(year, month)[1]
    work_days = 0
    holiday_dates = HOLIDAYS_BY_MONTH.get((year, month), [])

    for day in range(1, num_days + 1):
        date = datetime.date(year, month, day)
        if date.weekday() < 5:  # Senin sampai Jumat
            if day not in holiday_dates:
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

