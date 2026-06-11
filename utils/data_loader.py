"""Data loading and processing utilities"""
import pandas as pd
import streamlit as st

from utils.calculations import (
    get_work_days_holidays,
    get_check_out_minimum_minutes,
    get_check_in_deadline_minutes,
)


# Map bulan ke nama file CSV
# 2025: Maret–Desember, 2026: Januari dst. (tambah key + path CSV jika ada file baru)
MONTH_FILES = {
    # 2025 - nama file bahasa Indonesia
    '2025-03': '2025/maret.csv',
    '2025-04': '2025/april.csv',
    '2025-05': '2025/mei.csv',
    '2025-06': '2025/juni.csv',
    '2025-07': '2025/juli.csv',
    '2025-08': '2025/agustus.csv',
    '2025-09': '2025/september.csv',
    '2025-10': '2025/oktober.csv',
    '2025-11': '2025/november.csv',
    '2025-12': '2025/desember.csv',
    'january': '2026/january.csv',   # Januari 2026
    'february': '2026/february.csv', # Februari 2026
    'march': '2026/maret.csv',       # Maret 2026 (nama file: maret.csv)
    'april': '2026/april.csv',       # April 2026
    'may': '2026/mei.csv',           # Mei 2026 (nama file: mei.csv)
}

# Nama karyawan yang dikecualikan dari analisis (mis. Direktur)
EXCLUDED_EMPLOYEE_NAMES = {'Sumardi', 'Henri Hendriansah', 'Iwan'}
# Posisi jabatan yang dikecualikan dari dropdown Pilih Karyawan & analisis (mis. Direktur)
EXCLUDED_JOB_POSITIONS = {'Direktur'}


def _read_attendance_csv(filename):
    """Baca CSV absensi; deteksi pemisah koma (export lama) atau titik koma (export baru)."""
    with open(filename, encoding='utf-8-sig') as f:
        header = f.readline()
    sep = ';' if header.count(';') > header.count(',') else ','
    return pd.read_csv(filename, sep=sep, encoding='utf-8-sig')


# Naikkan angka ini jika logika transform data berubah (memaksa Streamlit memuat ulang cache).
_PIPELINE_VERSION = 6


@st.cache_data
def load_data(month='january', _pipeline_version=_PIPELINE_VERSION):
    """Load dan clean data dari CSV. Parameter month mengacu ke key di MONTH_FILES."""
    try:
        # Default fallback ke Januari 2026 jika key tidak dikenal
        filename = MONTH_FILES.get(month, MONTH_FILES['january'])
        df = _read_attendance_csv(filename)

        # Normalisasi nama kolom (hilangkan spasi dan tanda * di akhir seperti 'Employee ID*', 'Date*', dst.)
        df.columns = (
            df.columns
            .str.strip()
            .str.replace('*', '', regex=False)
        )

        # Simpan daftar kolom asli (setelah normalisasi) sebelum menambah kolom default
        original_time_cols = set(df.columns)

        # Pastikan kolom waktu yang dipakai di pipeline selalu ada
        for col in ['Real Working Hour', 'Actual Working Hour', 'Late In', 'Early Out']:
            if col not in df.columns:
                df[col] = '00:00'
        
        # Filter baris yang bukan TOTAL (baris yang berisi "TOTAL FOR EMPLOYEE")
        df = df[~df['Employee ID'].astype(str).str.contains('TOTAL', na=False)]
        
        # Filter baris yang memiliki Employee ID valid (numeric)
        df = df[pd.to_numeric(df['Employee ID'], errors='coerce').notna()]
        
        # Convert Employee ID ke integer
        df['Employee ID'] = df['Employee ID'].astype(int)
        
        # Convert Date ke datetime
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        # Parse waktu kerja (format HH:MM ke jam desimal)
        def parse_time_to_hours(time_str):
            """Convert waktu format HH:MM ke jam desimal"""
            if pd.isna(time_str) or time_str == '' or time_str == '00:00':
                return 0.0
            try:
                parts = str(time_str).split(':')
                if len(parts) == 2:
                    hours = int(parts[0])
                    minutes = int(parts[1])
                    return hours + (minutes / 60.0)
                return 0.0
            except:
                return 0.0
        
        # Parse Late In dan Early Out
        def parse_late_early(time_str):
            """Check apakah ada late in atau early out (bukan 00:00)"""
            if pd.isna(time_str) or time_str == '' or time_str == '00:00':
                return False
            try:
                parts = str(time_str).split(':')
                if len(parts) == 2:
                    hours = int(parts[0])
                    minutes = int(parts[1])
                    return hours > 0 or minutes > 0
                return False
            except:
                return False
        
        def _decimal_to_hhmm(h):
            """Jam desimal ke string HH:MM."""
            if pd.isna(h):
                return '00:00'
            h_int = int(h)
            m = round((h - h_int) * 60)
            if m >= 60:
                h_int += 1
                m = 0
            return f"{h_int:02d}:{m:02d}"

        # Apply parsing
        # Jika data punya kolom 'Real Working Hour', gunakan itu.
        # Jika tidak (seperti data 2025), hitung jam kerja dari selisih Check In dan Check Out.
        if 'Real Working Hour' in original_time_cols:
            df['Real Working Hour Decimal'] = df['Real Working Hour'].apply(parse_time_to_hours)
        else:
            df['Real Working Hour Decimal'] = df.apply(
                lambda row: max(
                    0.0,
                    parse_time_to_hours(row.get('Check Out')) - parse_time_to_hours(row.get('Check In'))
                ),
                axis=1
            )

        if 'Actual Working Hour' in original_time_cols:
            df['Actual Working Hour Decimal'] = df['Actual Working Hour'].apply(parse_time_to_hours)
        else:
            df['Actual Working Hour Decimal'] = df['Real Working Hour Decimal']

        # Export kadang isi Real Working Hour = 00:00 padahal ada Check In/Out — hitung ulang dari absensi
        if 'Real Working Hour' in original_time_cols:
            _ci_min = df['Check In'].apply(time_to_minutes)
            _co_min = df['Check Out'].apply(time_to_minutes)
            _fix_real = _ci_min.notna() & _co_min.notna() & (df['Real Working Hour Decimal'] <= 0)
            if _fix_real.any():
                df.loc[_fix_real, 'Real Working Hour Decimal'] = (
                    (_co_min[_fix_real] - _ci_min[_fix_real]).astype(float) / 60.0
                )
                df.loc[_fix_real, 'Real Working Hour'] = (
                    df.loc[_fix_real, 'Real Working Hour Decimal'].apply(_decimal_to_hhmm)
                )

        # Export tanpa kolom Real/Actual (mis. maret.csv): isi string HH:MM dari desimal untuk semua baris.
        if 'Real Working Hour' not in original_time_cols:
            df['Real Working Hour'] = df['Real Working Hour Decimal'].apply(_decimal_to_hhmm)
            df['Actual Working Hour'] = df['Actual Working Hour Decimal'].apply(_decimal_to_hhmm)

        df['Early Out Decimal'] = df['Early Out'].apply(parse_time_to_hours)
        df['Is Early Out'] = df['Early Out'].apply(parse_late_early)

        # Early Out by rule: puasa (Feb 19–28, Mar 1–17 2026) pulang < 16:00; setelah lebaran / normal < 17:00
        df['_co_min'] = df['Check Out'].apply(time_to_minutes)
        df['_co_threshold'] = df['Date'].apply(get_check_out_minimum_minutes)
        has_co = df['_co_min'].notna()
        is_early_by_rule = has_co & (df['_co_min'] < df['_co_threshold'])
        df.loc[has_co, 'Is Early Out'] = is_early_by_rule[has_co]
        def _early_out_decimal(r):
            if r['_co_min'] is not None and r['_co_min'] < r['_co_threshold']:
                return (r['_co_threshold'] - r['_co_min']) / 60.0
            if r['_co_min'] is not None:
                return 0.0
            return r['Early Out Decimal']
        df['Early Out Decimal'] = df.apply(_early_out_decimal, axis=1)
        df = df.drop(columns=['_co_min', '_co_threshold'], errors='ignore')

        # Tentukan apakah hadir (ada Check In atau Attendance Code = 'H')
        df['Is Present'] = (
            (df['Check In'].notna() & (df['Check In'] != '')) |
            (df['Attendance Code'] == 'H')
        )
        
        # Tentukan kategori status
        # Hari libur: Shift = 'dayoff' + hari libur yang dikonfigurasi (mis. list hari libur per bulan)
        if df['Date'].notna().any():
            year_mode = int(df['Date'].dt.year.mode()[0])
            month_mode = int(df['Date'].dt.month.mode()[0])
            holiday_days = set(get_work_days_holidays(year_mode, month_mode))
            is_holiday_config = df['Date'].dt.day.isin(holiday_days)
        else:
            is_holiday_config = False

        df['Is Dayoff'] = df['Shift'].str.contains('dayoff', case=False, na=False) | is_holiday_config
        
        # Sakit: Attendance Code = 'S' atau Time Off Code = 'S'
        df['Is Sick'] = (
            (df['Attendance Code'] == 'S') |
            (df['Time Off Code'] == 'S')
        )
        
        # Cuti / izin (tidak termasuk sakit):
        # - Attendance Code = 'CT' (Cuti)
        # - Time Off Code = 'CT'
        # - Attendance Code = 'CPD' (Cuti Perjalanan Dinas)
        # - Time Off Code = 'CPD'
        # - Shift mengandung 'Roster Leave'
        df['Is Leave'] = (
            (df['Attendance Code'] == 'CT') |
            (df['Time Off Code'] == 'CT') |
            (df['Attendance Code'] == 'CPD') |
            (df['Time Off Code'] == 'CPD') |
            (df['Shift'].str.contains('Roster Leave', case=False, na=False))
        )

        # Hari cuti: 8 jam kerja (plan) di kolom Jam Kerja; tetap status cuti, bukan dihitung hadir
        if df['Is Leave'].any():
            df.loc[df['Is Leave'], 'Real Working Hour Decimal'] = 8.0
            df.loc[df['Is Leave'], 'Actual Working Hour Decimal'] = 8.0
            df.loc[df['Is Leave'], 'Real Working Hour'] = '08:00'
            df.loc[df['Is Leave'], 'Actual Working Hour'] = '08:00'
            df.loc[df['Is Leave'], 'Is Present'] = False

        if df['Is Sick'].any():
            df.loc[df['Is Sick'], 'Is Present'] = False
        
        # Tidak hadir (absen): bukan hadir, bukan cuti, bukan sakit, bukan hari libur
        df['Is Absent'] = (
            (~df['Is Present']) &
            (~df['Is Leave']) &
            (~df['Is Sick']) &
            (~df['Is Dayoff'])
        )

        # Late In: Check In lewat batas tepat waktu (normal 08:15; puasa 07:30 / 07:45 per tanggal), bukan kolom CSV
        df['_ci_min'] = df['Check In'].apply(time_to_minutes)
        df['_ci_deadline'] = df['Date'].apply(get_check_in_deadline_minutes)
        late_eligible = (
            df['_ci_min'].notna()
            & (~df['Is Leave'])
            & (~df['Is Dayoff'])
            & (~df['Is Sick'])
        )
        df['Is Late In'] = late_eligible & (df['_ci_min'] > df['_ci_deadline'])

        def _late_in_decimal(r):
            if r['_ci_min'] is None or r['Is Leave'] or r['Is Dayoff'] or r['Is Sick']:
                return 0.0
            if r['_ci_min'] > r['_ci_deadline']:
                return (r['_ci_min'] - r['_ci_deadline']) / 60.0
            return 0.0

        df['Late In Decimal'] = df.apply(_late_in_decimal, axis=1)
        df['Late In'] = df['Late In Decimal'].apply(_decimal_to_hhmm)

        # 8 jam kerja (plan): cuti = 8 jam; hadir = masuk ≤ batas & pulang ≥ batas (bukan Real Working Hour CSV)
        co_min = df['Check Out'].apply(time_to_minutes)
        co_minimum = df['Date'].apply(get_check_out_minimum_minutes)
        attended_full_day = (
            df['Is Present']
            & ~df['Is Dayoff']
            & ~df['Is Sick']
            & df['_ci_min'].notna()
            & co_min.notna()
            & (df['_ci_min'] <= df['_ci_deadline'])
            & (co_min >= co_minimum)
        )
        df['Meets 8 Hour Work Day'] = df['Is Leave'] | attended_full_day

        df = df.drop(columns=['_ci_min', '_ci_deadline'], errors='ignore')
        
        return df
    except FileNotFoundError:
        st.error(f"File data tidak ditemukan: {filename}. Pastikan file ada di folder project.")
        return None
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None


def filter_data(df, branch, org):
    """Filter data berdasarkan branch dan organization. Mengecualikan nama di EXCLUDED_EMPLOYEE_NAMES dan posisi di EXCLUDED_JOB_POSITIONS (mis. Direktur)."""
    filtered_df = df[df['Branch'] == branch].copy()
    if org != 'All':
        filtered_df = filtered_df[filtered_df['Organization'] == org]
    # Exclude karyawan tertentu berdasarkan nama (mis. Direktur)
    if EXCLUDED_EMPLOYEE_NAMES and 'Full Name' in filtered_df.columns:
        filtered_df = filtered_df[~filtered_df['Full Name'].astype(str).str.strip().isin(EXCLUDED_EMPLOYEE_NAMES)]
    # Exclude berdasarkan posisi jabatan (mis. Direktur) agar tidak muncul di Pilih Karyawan
    if EXCLUDED_JOB_POSITIONS and 'Job Position' in filtered_df.columns:
        pos = filtered_df['Job Position'].astype(str).str.strip()
        mask_excluded_pos = pos.str.lower().isin({p.lower() for p in EXCLUDED_JOB_POSITIONS})
        filtered_df = filtered_df[~mask_excluded_pos]
    return filtered_df


def time_to_minutes(time_str):
    """Convert waktu HH:MM ke total menit"""
    if pd.isna(time_str) or time_str == '' or str(time_str).strip() == '':
        return None
    try:
        time_clean = str(time_str).strip()
        parts = time_clean.split(':')
        if len(parts) == 2:
            hour = int(parts[0])
            minute = int(parts[1])
            return hour * 60 + minute
        return None
    except:
        return None


def parse_check_in_to_minutes(check_in_str):
    """Convert waktu format HH:MM ke menit dari 00:00"""
    if pd.isna(check_in_str) or check_in_str == '' or check_in_str == '00:00':
        return None
    try:
        parts = str(check_in_str).split(':')
        if len(parts) == 2:
            hours = int(parts[0])
            minutes = int(parts[1])
            return hours * 60 + minutes
        return None
    except:
        return None

