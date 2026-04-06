"""Calculation utilities"""
import pandas as pd
from calendar import monthrange
import datetime

# Hari libur per bulan (tanggal): (year, month) -> [list of day of month]
# Hanya tanggal yang termasuk hari kerja (Senin–Jumat) yang mengurangi Work Day.
HOLIDAYS_BY_MONTH = {
    (2026, 1): [1, 16],   # Januari 2026: 1 = libur nasional tahun baru, 16 = cuti bersama
    (2026, 2): [1, 7, 8, 14, 15, 16, 17, 21, 22, 28],  # Februari 2026
    # Maret 2026: SKB 3 Menteri — CB 18; LN Nyepi 19; CB 20; LN Idulfitri 21–22; CB 23–24
    (2026, 3): [18, 19, 20, 21, 22, 23, 24],
}


def get_work_days_holidays(year, month):
    """Daftar tanggal hari libur di bulan tersebut (untuk referensi)."""
    return HOLIDAYS_BY_MONTH.get((year, month), [])


# Ramadan Feb 2026: tgl 19–28, batas tepat waktu masuk 07:45 (465 menit)
RAMADAN_FEB_2026_START = 19
RAMADAN_FEB_2026_END = 28
# Ramadan Maret 2026: tgl 1–17 (masih puasa sebelum libur Lebaran 18–24), batas masuk 07:30
RAMADAN_MAR_2026_START = 1
RAMADAN_MAR_2026_END = 17

CHECK_IN_DEADLINE_RAMADAN_FEB_MINUTES = 7 * 60 + 45   # 07:45
CHECK_IN_DEADLINE_RAMADAN_MAR_MINUTES = 7 * 60 + 30   # 07:30
CHECK_IN_DEADLINE_NORMAL_MINUTES = 8 * 60 + 15         # 08:15 (normal, termasuk 25–31 Mar 2026)

# Ramadan: istirahat di-adjust +30 menit pada jam kerja terekam; total efektif 8 jam/hari
# Puasa: batas jam pulang = 16:00 (early out jika < 16:00). Normal: 17:00
CHECK_OUT_MINIMUM_RAMADAN_MINUTES = 16 * 60 + 0   # 16:00 = 960
CHECK_OUT_MINIMUM_NORMAL_MINUTES = 17 * 60 + 0     # 17:00 = 1020


def _to_date(date_or_ts):
    """Normalisasi ke datetime.date atau None."""
    if date_or_ts is None:
        return None
    try:
        if pd.isna(date_or_ts):
            return None
    except TypeError:
        pass
    try:
        return date_or_ts.date() if hasattr(date_or_ts, 'date') else date_or_ts
    except Exception:
        return None


def is_ramadan_feb_2026(date_or_ts):
    """True jika tanggal dalam periode puasa 19–28 Feb 2026 (batas masuk 07:45, pulang 16:00)."""
    d = _to_date(date_or_ts)
    if d is None:
        return False
    return d.year == 2026 and d.month == 2 and RAMADAN_FEB_2026_START <= d.day <= RAMADAN_FEB_2026_END


def is_ramadan_mar_2026_partial(date_or_ts):
    """True jika 1–17 Maret 2026 (masih puasa; 18–24 libur Lebaran, 25+ kembali normal)."""
    d = _to_date(date_or_ts)
    if d is None:
        return False
    return d.year == 2026 and d.month == 3 and RAMADAN_MAR_2026_START <= d.day <= RAMADAN_MAR_2026_END


def is_ramadan_adjusted_hours_2026(date_or_ts):
    """Hari yang dapat penyesuaian +30 menit jam kerja (istirahat puasa): Feb 19–28 atau Mar 1–17 2026."""
    return is_ramadan_feb_2026(date_or_ts) or is_ramadan_mar_2026_partial(date_or_ts)


def get_check_out_minimum_minutes(date_or_ts):
    """Batas jam pulang minimum. Puasa (Feb 19–28, Mar 1–17 2026): 16:00. Lainnya: 17:00."""
    d = _to_date(date_or_ts)
    if d is None:
        return CHECK_OUT_MINIMUM_NORMAL_MINUTES
    if d.year == 2026 and d.month == 2 and RAMADAN_FEB_2026_START <= d.day <= RAMADAN_FEB_2026_END:
        return CHECK_OUT_MINIMUM_RAMADAN_MINUTES
    if d.year == 2026 and d.month == 3 and RAMADAN_MAR_2026_START <= d.day <= RAMADAN_MAR_2026_END:
        return CHECK_OUT_MINIMUM_RAMADAN_MINUTES
    return CHECK_OUT_MINIMUM_NORMAL_MINUTES


def get_check_in_deadline_minutes(date_or_ts):
    """Batas jam masuk tepat waktu: Mar 1–17 2026 → 07:30; Feb 19–28 → 07:45; lainnya → 08:15."""
    d = _to_date(date_or_ts)
    if d is None:
        return CHECK_IN_DEADLINE_NORMAL_MINUTES
    if d.year == 2026 and d.month == 3 and RAMADAN_MAR_2026_START <= d.day <= RAMADAN_MAR_2026_END:
        return CHECK_IN_DEADLINE_RAMADAN_MAR_MINUTES
    if d.year == 2026 and d.month == 2 and RAMADAN_FEB_2026_START <= d.day <= RAMADAN_FEB_2026_END:
        return CHECK_IN_DEADLINE_RAMADAN_FEB_MINUTES
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

