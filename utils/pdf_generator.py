from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import io
from datetime import datetime


# ── Color palette ──────────────────────────────────────────────────────────────
BRAND_DARK   = colors.HexColor('#1e293b')
BRAND_MID    = colors.HexColor('#334155')
BRAND_ACCENT = colors.HexColor('#6366f1')
PASS_GREEN   = colors.HexColor('#16a34a')
FAIL_RED     = colors.HexColor('#dc2626')
ROW_ALT      = colors.HexColor('#f8fafc')
HEADER_BG    = colors.HexColor('#e0e7ff')
BORDER_COLOR = colors.HexColor('#cbd5e1')
WHITE        = colors.white


def generate_marksheet(student_data: dict) -> bytes:
    """
    Generate a PDF marksheet for a student.
    student_data: output of Student.to_dict()
    Returns: PDF bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
        title=f"Result - {student_data['name']}"
    )

    styles = getSampleStyleSheet()
    elements = []

    # ── Header ────────────────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        'Title', parent=styles['Normal'],
        fontSize=22, fontName='Helvetica-Bold',
        textColor=BRAND_DARK, alignment=TA_CENTER, spaceAfter=4
    )
    sub_style = ParagraphStyle(
        'Sub', parent=styles['Normal'],
        fontSize=11, textColor=BRAND_MID, alignment=TA_CENTER, spaceAfter=2
    )
    elements.append(Paragraph("Student Result Marksheet", title_style))
    elements.append(Paragraph(student_data.get('exam_name', 'Examination'), sub_style))
    elements.append(HRFlowable(width='100%', thickness=1.5, color=BRAND_ACCENT, spaceAfter=14))

    # ── Student info table ────────────────────────────────────────────────────
    label_style = ParagraphStyle('Label', parent=styles['Normal'],
                                  fontSize=10, fontName='Helvetica-Bold', textColor=BRAND_MID)
    value_style = ParagraphStyle('Value', parent=styles['Normal'],
                                  fontSize=10, textColor=BRAND_DARK)

    info_data = [
        [Paragraph('Student Name', label_style), Paragraph(student_data['name'], value_style),
         Paragraph('Student ID', label_style), Paragraph(student_data['student_id'], value_style)],
        [Paragraph('Class', label_style), Paragraph(student_data['class_name'], value_style),
         Paragraph('Date', label_style), Paragraph(datetime.utcnow().strftime('%d %b %Y'), value_style)],
    ]
    info_table = Table(info_data, colWidths=[3.5*cm, 6*cm, 3.5*cm, 4*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), ROW_ALT),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [ROW_ALT, WHITE]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('ROUNDEDCORNERS', [4]),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 16))

    # ── Subject results table ──────────────────────────────────────────────────
    section_style = ParagraphStyle('Section', parent=styles['Normal'],
                                    fontSize=12, fontName='Helvetica-Bold',
                                    textColor=BRAND_DARK, spaceAfter=6)
    elements.append(Paragraph("Subject-wise Results", section_style))

    header_p = lambda t: Paragraph(t, ParagraphStyle('TH', parent=styles['Normal'],
                                    fontSize=10, fontName='Helvetica-Bold',
                                    textColor=BRAND_DARK, alignment=TA_CENTER))
    cell_p = lambda t, align=TA_LEFT: Paragraph(t, ParagraphStyle('TD', parent=styles['Normal'],
                                    fontSize=10, textColor=BRAND_DARK, alignment=align))

    subject_header = [
        header_p('Subject'),
        header_p('Marks Obtained'),
        header_p('Max Marks'),
        header_p('Percentage'),
        header_p('Grade'),
    ]
    subject_rows = [subject_header]
    for s in student_data['subjects']:
        subject_rows.append([
            cell_p(s['subject']),
            cell_p(str(int(s['marks_obtained'])), TA_CENTER),
            cell_p(str(int(s['max_marks'])), TA_CENTER),
            cell_p(f"{s['percentage']}%", TA_CENTER),
            cell_p(s['grade'], TA_CENTER),
        ])

    subject_table = Table(subject_rows, colWidths=[6*cm, 3.5*cm, 3.5*cm, 3.5*cm, 2.5*cm])
    row_colors = [HEADER_BG] + [WHITE if i % 2 == 0 else ROW_ALT for i in range(len(student_data['subjects']))]
    subject_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, ROW_ALT]),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(subject_table)
    elements.append(Spacer(1, 20))

    # ── Summary card ──────────────────────────────────────────────────────────
    elements.append(Paragraph("Overall Summary", section_style))

    status_color = PASS_GREEN if student_data['status'] == 'Pass' else FAIL_RED
    status_p = Paragraph(
        f"<font color='{'#16a34a' if student_data['status'] == 'Pass' else '#dc2626'}'>"
        f"<b>{student_data['status']}</b></font>",
        ParagraphStyle('Status', parent=styles['Normal'], fontSize=12, alignment=TA_CENTER)
    )

    summary_data = [[
        Paragraph(f"<b>Total Marks</b><br/><font size=14>{student_data['total_marks']} / {student_data['max_marks']}</font>",
                  ParagraphStyle('S', parent=styles['Normal'], alignment=TA_CENTER)),
        Paragraph(f"<b>Percentage</b><br/><font size=14>{student_data['percentage']}%</font>",
                  ParagraphStyle('S', parent=styles['Normal'], alignment=TA_CENTER)),
        Paragraph(f"<b>Grade</b><br/><font size=18><b>{student_data['grade']}</b></font>",
                  ParagraphStyle('S', parent=styles['Normal'], alignment=TA_CENTER)),
        Paragraph(f"<b>Status</b><br/><font size=14><b>{student_data['status']}</b></font>",
                  ParagraphStyle('S', parent=styles['Normal'],
                                  textColor=status_color, alignment=TA_CENTER)),
    ]]
    summary_table = Table(summary_data, colWidths=[4.5*cm, 4.5*cm, 4.5*cm, 4.5*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), ROW_ALT),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(summary_table)

    # ── Footer ────────────────────────────────────────────────────────────────
    elements.append(Spacer(1, 30))
    elements.append(HRFlowable(width='100%', thickness=0.5, color=BORDER_COLOR))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'],
                                   fontSize=8, textColor=BRAND_MID, alignment=TA_CENTER, spaceBefore=6)
    elements.append(Paragraph(
        f"Generated on {datetime.utcnow().strftime('%d %b %Y, %H:%M')} UTC · Student Result Portal",
        footer_style
    ))

    doc.build(elements)
    return buffer.getvalue()
