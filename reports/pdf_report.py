"""PDF report generator"""
import pandas as pd
from io import BytesIO
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from utils.formatters import format_hours_pdf


def create_pdf_report(employee_stats_df, checklist_df, filtered_df, branch, org):
    """Membuat report PDF lengkap"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()
    
    # Title Style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Heading Style
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Normal Style
    normal_style = styles['Normal']
    
    # Title
    title = Paragraph("LAPORAN AUDIT & ANALISIS ABSENSI", title_style)
    story.append(title)
    
    # Info
    org_name = org if org != 'All' else 'Semua Organization'
    info_text = f"<b>Branch:</b> {branch} | <b>Organization:</b> {org_name}<br/>"
    info_text += f"<b>Periode:</b> {filtered_df['Date'].min().strftime('%d %B %Y')} - {filtered_df['Date'].max().strftime('%d %B %Y')}<br/>"
    info_text += f"<b>Tanggal Laporan:</b> {datetime.now().strftime('%d %B %Y %H:%M:%S')}"
    story.append(Paragraph(info_text, normal_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Ringkasan Statistik
    story.append(Paragraph("1. RINGKASAN STATISTIK", heading_style))
    
    total_emp = filtered_df['Employee ID'].nunique()
    total_pres = filtered_df['Is Present'].sum()
    total_abs = filtered_df['Is Absent'].sum()
    work_days = employee_stats_df['Work Days Bulan Ini'].iloc[0] if len(employee_stats_df) > 0 else 0
    total_work_day = total_emp * work_days
    attendance_pct = (total_pres / total_work_day * 100) if total_work_day > 0 else 0
    absent_pct = (total_abs / total_work_day * 100) if total_work_day > 0 else 0
    
    total_jam_kerja_real = employee_stats_df['Total Jam Kerja (Real)'].sum() if 'Total Jam Kerja (Real)' in employee_stats_df.columns else filtered_df['Real Working Hour Decimal'].sum()
    total_jam_kerja_plant = total_work_day * 8
    total_jam_kerja_real_formatted = format_hours_pdf(total_jam_kerja_real)
    total_jam_kerja_plant_formatted = format_hours_pdf(total_jam_kerja_plant)
    
    summary_data = [
        ['Metrik', 'Nilai'],
        ['Total Karyawan', str(total_emp)],
        ['Work Day', str(work_days)],
        ['Total Work Day', str(total_work_day)],
        ['Total Kehadiran', f"{total_pres} ({attendance_pct:.2f}%)"],
        ['Total Tidak Hadir', f"{total_abs} ({absent_pct:.2f}%)"],
        ['Total Jam Kerja', total_jam_kerja_real_formatted],
        ['Plan Jam Kerja', total_jam_kerja_plant_formatted]
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Analisis Per Karyawan (Top 20)
    story.append(Paragraph("2. ANALISIS PER KARYAWAN (Top 20)", heading_style))
    
    top_employees = employee_stats_df.head(20).copy()
    top_employees_export = top_employees.drop(columns=['Branch', 'Organization'], errors='ignore')
    emp_data = []
    emp_data.append(['ID', 'Nama', 'Hadir', 'Absen', 'Cuti', 'Late In', 'Early Out', 'Total Jam'])
    
    for _, row in top_employees.iterrows():
        emp_data.append([
            str(int(row['Employee ID'])),
            str(row['Full Name'])[:25] + '...' if len(str(row['Full Name'])) > 25 else str(row['Full Name']),
            str(int(row['Jumlah Hadir'])),
            str(int(row['Jumlah Absen'])),
            str(int(row['Jumlah Cuti'])),
            str(int(row['Jumlah Late In'])),
            str(int(row['Jumlah Early Out'])),
            str(row['Total Jam Kerja (Real) Formatted'])
        ])
    
    emp_table = Table(emp_data, colWidths=[0.6*inch, 2*inch, 0.5*inch, 0.5*inch, 0.5*inch, 0.6*inch, 0.6*inch, 0.8*inch])
    emp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(emp_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Checklist Compliance Summary
    if len(checklist_df) > 0:
        story.append(Paragraph("3. RINGKASAN CHECKLIST COMPLIANCE", heading_style))
        
        compliant_8jam = len(checklist_df[checklist_df['✅ Kerja 8 Jam/Hari'] == '✅'])
        compliant_8_17 = len(checklist_df[checklist_df['✅ Masuk 08:00 & Pulang 17:00'] == '✅'])
        compliant_both = len(checklist_df[
            (checklist_df['✅ Kerja 8 Jam/Hari'] == '✅') &
            (checklist_df['✅ Masuk 08:00 & Pulang 17:00'] == '✅')
        ])
        total_checklist = len(checklist_df)
        
        checklist_data = [
            ['Kriteria', 'Compliant', 'Tidak Compliant', 'Persentase'],
            ['Kerja 8 Jam/Hari', str(compliant_8jam), str(total_checklist - compliant_8jam), 
             f"{(compliant_8jam/total_checklist*100) if total_checklist > 0 else 0:.1f}%"],
            ['Masuk 08:00 & Pulang 17:00', str(compliant_8_17), str(total_checklist - compliant_8_17),
             f"{(compliant_8_17/total_checklist*100) if total_checklist > 0 else 0:.1f}%"],
            ['Keduanya Compliant', str(compliant_both), str(total_checklist - compliant_both),
             f"{(compliant_both/total_checklist*100) if total_checklist > 0 else 0:.1f}%"]
        ]
        
        checklist_table = Table(checklist_data, colWidths=[2.5*inch, 1*inch, 1*inch, 1*inch])
        checklist_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        story.append(checklist_table)
        story.append(Spacer(1, 0.3*inch))
    
    # Footer
    story.append(Spacer(1, 0.2*inch))
    footer_text = f"<i>Laporan ini dibuat secara otomatis oleh sistem Audit & Analisis Absensi</i>"
    story.append(Paragraph(footer_text, normal_style))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


def create_table_pdf(df, title, subtitle=""):
    """Membuat PDF dari DataFrame dalam format Landscape dengan layout yang rapi"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=0.3*inch, bottomMargin=0.3*inch, 
                            leftMargin=0.2*inch, rightMargin=0.2*inch)
    story = []
    styles = getSampleStyleSheet()
    
    # Title Style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=12,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=10,
        alignment=TA_CENTER
    )
    
    # Subtitle Style
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#666666'),
        spaceAfter=8,
        alignment=TA_CENTER
    )
    
    # Normal Style
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=7
    )
    
    # Title
    story.append(Paragraph(title, title_style))
    if subtitle:
        story.append(Paragraph(subtitle, subtitle_style))
    
    # Info
    info_text = f"<b>Tanggal Laporan:</b> {datetime.now().strftime('%d %B %Y %H:%M:%S')}"
    story.append(Paragraph(info_text, normal_style))
    story.append(Spacer(1, 0.1*inch))
    
    # Convert DataFrame to table
    if len(df) > 0:
        table_data = []
        
        # Header - wrap text untuk header yang panjang dan replace emoji
        headers = []
        for col in df.columns:
            col_str = str(col)
            col_str = col_str.replace('✅', '').replace('❌', '').replace('✈️', '').replace('🏖️', '')
            col_str = col_str.strip()
            if len(col_str) > 15:
                words = col_str.split()
                if len(words) > 1:
                    mid = len(words) // 2
                    header_text = ' '.join(words[:mid]) + '<br/>' + ' '.join(words[mid:])
                else:
                    mid = len(col_str) // 2
                    header_text = col_str[:mid] + '<br/>' + col_str[mid:]
                headers.append(Paragraph(header_text, ParagraphStyle('Header', fontSize=7, alignment=TA_CENTER)))
            else:
                headers.append(col_str)
        table_data.append(headers)
        
        # Data rows (limit to 200 rows untuk landscape)
        max_rows = 200
        df_display = df.copy()
        
        # Cek apakah ada kolom tanggal untuk sorting
        date_cols = [col for col in df_display.columns if 'tanggal' in str(col).lower() or 'date' in str(col).lower()]
        if date_cols:
            try:
                date_col = date_cols[0]
                if not pd.api.types.is_datetime64_any_dtype(df_display[date_col]):
                    df_display[date_col] = pd.to_datetime(df_display[date_col], errors='coerce')
                df_display = df_display.sort_values(by=date_col, ascending=True, na_position='last')
            except:
                df_display = df_display.sort_values(by=date_cols[0], ascending=True, na_position='last')
        
        df_display = df_display.head(max_rows) if len(df_display) > max_rows else df_display
        
        # Track column indices yang perlu diwarnai (checklist columns)
        checklist_col_indices = []
        for i, col in enumerate(df.columns):
            col_str = str(col)
            if any(keyword in col_str for keyword in ['Kerja 8 Jam', 'Masuk 08:00', 'Checklist', '✅', '❌']):
                checklist_col_indices.append(i)
        
        for row_idx, row in df_display.iterrows():
            row_data = []
            for col_idx, val in enumerate(row):
                if pd.notna(val):
                    col_name = df.columns[col_idx]
                    col_str = str(col_name).lower()
                    
                    # Format khusus untuk kolom tanggal
                    if 'tanggal' in col_str or 'date' in col_str:
                        val_str = str(val)
                        if ' ' in val_str and ':' in val_str:
                            val_str = val_str.split(' ')[0]
                        try:
                            if pd.api.types.is_datetime64_any_dtype(type(val)) or isinstance(val, pd.Timestamp):
                                val_str = pd.to_datetime(val).strftime('%Y-%m-%d')
                        except:
                            pass
                    else:
                        val_str = str(val)
                    
                    # Replace emoji dengan Y/N untuk PDF
                    val_str = val_str.replace('✅', 'Y').replace('❌', 'N')
                    val_str = val_str.replace('✈️', 'CUTI').replace('🏖️', 'LIBUR')
                    if len(val_str) > 25:
                        row_data.append(val_str[:22] + '...')
                    else:
                        row_data.append(val_str)
                else:
                    row_data.append('')
            table_data.append(row_data)
        
        # Calculate column widths
        num_cols = len(df.columns)
        page_width = landscape(A4)[0] - 0.4*inch
        available_width = page_width
        
        special_widths = {
            'Tanggal': 1.0 * inch,
            'ID': 0.8 * inch,
            'Date': 1.0 * inch,
            'Employee ID': 0.8 * inch
        }
        
        col_widths = []
        for i, col in enumerate(df.columns):
            col_str = str(col)
            if col_str in special_widths:
                col_width = special_widths[col_str]
            else:
                header_len = len(col_str)
                max_data_len = df_display[col].astype(str).str.len().max() if len(df_display) > 0 else header_len
                content_len = max(header_len, max_data_len)
                col_width = min(max(content_len * 0.08, 0.6), 2.0) * inch
            col_widths.append(col_width)
        
        # Normalisasi lebar kolom
        total_width = sum(col_widths)
        if total_width > available_width:
            scale_factor = available_width / total_width
            col_widths = [w * scale_factor for w in col_widths]
        elif total_width < available_width:
            extra = (available_width - total_width) / num_cols
            col_widths = [w + extra for w in col_widths]
        
        # Create table
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        # Style table
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 6.5),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
            ('TOPPADDING', (0, 1), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ])
        
        # Tambahkan warna untuk kolom checklist
        if checklist_col_indices:
            for col_idx in checklist_col_indices:
                for row_idx in range(1, len(table_data)):
                    table_style.add('BACKGROUND', (col_idx, row_idx), (col_idx, row_idx), colors.beige)
        
        for col_idx in checklist_col_indices:
            for row_idx in range(1, len(table_data)):
                cell_value = str(table_data[row_idx][col_idx]).strip().upper()
                if cell_value == 'Y':
                    table_style.add('BACKGROUND', (col_idx, row_idx), (col_idx, row_idx), colors.HexColor('#90EE90'))
                    table_style.add('TEXTCOLOR', (col_idx, row_idx), (col_idx, row_idx), colors.HexColor('#006400'))
                    table_style.add('FONTNAME', (col_idx, row_idx), (col_idx, row_idx), 'Helvetica-Bold')
                elif cell_value == 'N':
                    table_style.add('BACKGROUND', (col_idx, row_idx), (col_idx, row_idx), colors.HexColor('#FFB6C1'))
                    table_style.add('TEXTCOLOR', (col_idx, row_idx), (col_idx, row_idx), colors.HexColor('#8B0000'))
                    table_style.add('FONTNAME', (col_idx, row_idx), (col_idx, row_idx), 'Helvetica-Bold')
        
        table.setStyle(table_style)
        story.append(table)
        
        # Note jika ada lebih dari max_rows
        if len(df) > max_rows:
            story.append(Spacer(1, 0.08*inch))
            note_text = f"<i>Catatan: Menampilkan {max_rows} dari {len(df)} baris. Untuk data lengkap, gunakan format Excel.</i>"
            story.append(Paragraph(note_text, normal_style))
    else:
        story.append(Paragraph("Tidak ada data untuk ditampilkan.", normal_style))
    
    # Footer
    story.append(Spacer(1, 0.1*inch))
    footer_text = f"<i>Laporan ini dibuat secara otomatis oleh sistem Audit & Analisis Absensi</i>"
    story.append(Paragraph(footer_text, normal_style))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

