"""Data loading and processing utilities"""
import pandas as pd
import streamlit as st

from utils.calculations import get_work_days_holidays, get_check_out_minimum_minutes, is_ramadan_adjusted_hours_2026


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
}

# Nama karyawan yang dikecualikan dari analisis (mis. Direktur)
EXCLUDED_EMPLOYEE_NAMES = {'Sumardi', 'Henri Hendriansah', 'Iwan'}
# Posisi jabatan yang dikecualikan dari dropdown Pilih Karyawan & analisis (mis. Direktur)
EXCLUDED_JOB_POSITIONS = {'Direktur'}


@st.cache_data
def load_data(month='january'):
    """Load dan clean data dari CSV. Parameter month mengacu ke key di MONTH_FILES."""
    try:
        # Default fallback ke Januari 2026 jika key tidak dikenal
        filename = MONTH_FILES.get(month, MONTH_FILES['january'])
        df = pd.read_csv(filename)

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
            # Jika tidak ada kolom Actual, gunakan nilai Real sebagai proxy
            df['Actual Working Hour Decimal'] = df['Real Working Hour Decimal']

        # Puasa 2026: Feb 19–28 & Mar 1–17 — tambah 30 menit ke Jam Kerja (Real/Actual) (penyesuaian istirahat)
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

        ramadan_mask = df['Date'].apply(is_ramadan_adjusted_hours_2026)
        if ramadan_mask.any():
            df.loc[ramadan_mask, 'Real Working Hour Decimal'] = df.loc[ramadan_mask, 'Real Working Hour Decimal'] + 0.5
            df.loc[ramadan_mask, 'Actual Working Hour Decimal'] = df.loc[ramadan_mask, 'Actual Working Hour Decimal'] + 0.5

        # Export tanpa kolom Real/Actual (mis. maret.csv): jam dihitung dari Check In/Out → isi string HH:MM untuk SEMUA baris.
        # Sebelumnya hanya baris puasa yang disinkronkan, sehingga tgl 25–31 Maret (dst.) tetap 00:00 / tampak kosong.
        if 'Real Working Hour' not in original_time_cols:
            df['Real Working Hour'] = df['Real Working Hour Decimal'].apply(_decimal_to_hhmm)
            df['Actual Working Hour'] = df['Actual Working Hour Decimal'].apply(_decimal_to_hhmm)
        elif ramadan_mask.any():
            df.loc[ramadan_mask, 'Real Working Hour'] = df.loc[ramadan_mask, 'Real Working Hour Decimal'].apply(_decimal_to_hhmm)
            if 'Actual Working Hour' in df.columns:
                df.loc[ramadan_mask, 'Actual Working Hour'] = df.loc[ramadan_mask, 'Actual Working Hour Decimal'].apply(_decimal_to_hhmm)

        df['Late In Decimal'] = df['Late In'].apply(parse_time_to_hours)
        df['Early Out Decimal'] = df['Early Out'].apply(parse_time_to_hours)
        df['Is Late In'] = df['Late In'].apply(parse_late_early)
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
        
        # Tidak hadir (absen): bukan hadir, bukan cuti, bukan sakit, bukan hari libur
        df['Is Absent'] = (
            (~df['Is Present']) &
            (~df['Is Leave']) &
            (~df['Is Sick']) &
            (~df['Is Dayoff'])
        )
        
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

