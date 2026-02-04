# Aplikasi Audit & Analisis Absensi - Januari 2026

Aplikasi Streamlit untuk melakukan audit dan analisis data absensi dari Talenta.

## Fitur

- ✅ **Jumlah Absensi Per Orang**: Menghitung total kehadiran setiap karyawan
- ⏰ **Jumlah Late In**: Menghitung berapa kali setiap karyawan terlambat
- 🚪 **Jumlah Fast Clock Out (Early Out)**: Menghitung berapa kali setiap karyawan clock out lebih cepat
- ⏱️ **Total Jam Kerja**: Menghitung total jam kerja setiap karyawan (Real Working Hour dan Actual Working Hour)

## Instalasi

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Menjalankan Aplikasi

```bash
streamlit run app.py
```

Aplikasi akan terbuka di browser pada `http://localhost:8501`

## Struktur Data

Aplikasi membaca file `january.csv` dengan kolom-kolom berikut:
- Employee ID
- Full Name
- Branch
- Organization
- Job Position
- Date
- Check In / Check Out
- Late In / Early Out
- Real Working Hour / Actual Working Hour
- Attendance Code

## Fitur Aplikasi

1. **Filter Data**: Filter berdasarkan Branch dan Organization
2. **Ringkasan Statistik**: Overview statistik keseluruhan
3. **Analisis Per Karyawan**: Tabel lengkap dengan semua metrik
4. **Visualisasi**: Charts untuk berbagai metrik
5. **Detail Per Karyawan**: Detail harian untuk setiap karyawan
6. **Export Data**: Download hasil analisis dalam format CSV

