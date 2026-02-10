"""Data loading and processing utilities"""
import pandas as pd
import streamlit as st


@st.cache_data
def load_data():
    """Load dan clean data dari CSV"""
    try:
        df = pd.read_csv('january.csv')
        
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
        df['Real Working Hour Decimal'] = df['Real Working Hour'].apply(parse_time_to_hours)
        df['Actual Working Hour Decimal'] = df['Actual Working Hour'].apply(parse_time_to_hours)
        df['Late In Decimal'] = df['Late In'].apply(parse_time_to_hours)
        df['Early Out Decimal'] = df['Early Out'].apply(parse_time_to_hours)
        df['Is Late In'] = df['Late In'].apply(parse_late_early)
        df['Is Early Out'] = df['Early Out'].apply(parse_late_early)
        
        # Tentukan apakah hadir (ada Check In atau Attendance Code = 'H')
        df['Is Present'] = (
            (df['Check In'].notna() & (df['Check In'] != '')) |
            (df['Attendance Code'] == 'H')
        )
        
        # Tentukan kategori status
        # Hari libur: Shift = 'dayoff'
        df['Is Dayoff'] = df['Shift'].str.contains('dayoff', case=False, na=False)
        
        # Cuti: Attendance Code = 'CT' atau Time Off Code = 'CT' atau Shift = 'Roster Leave'
        df['Is Leave'] = (
            (df['Attendance Code'] == 'CT') |
            (df['Time Off Code'] == 'CT') |
            (df['Shift'].str.contains('Roster Leave', case=False, na=False))
        )
        
        # Tidak hadir (absen): bukan hadir, bukan cuti, bukan hari libur
        df['Is Absent'] = (
            (~df['Is Present']) &
            (~df['Is Leave']) &
            (~df['Is Dayoff'])
        )
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None


def filter_data(df, branch, org):
    """Filter data berdasarkan branch dan organization"""
    filtered_df = df[df['Branch'] == branch].copy()
    if org != 'All':
        filtered_df = filtered_df[filtered_df['Organization'] == org]
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

