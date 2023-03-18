from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import Paragraph

basic_table_style = [
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 12),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
    ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
    ('FONTSIZE', (0, 1), (-1, -1), 10),
    ('LEFTPADDING', (0, 1), (-1, -1), 20),  # Adjust this value
    ('RIGHTPADDING', (0, 1), (-1, -1), 4),
    ('TOPPADDING', (0, 1), (-1, -1), 4),
    ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
]

# Create a stylesheet
styles = getSampleStyleSheet()
style_title = styles["Title"]
style_title.alignment = TA_LEFT
style_title.setFont = 'Arial'
style_title.leftIndent = 0
style_body = styles["BodyText"]
style_body.fontSize = 14
style_body.leftPadding = 0
style_not_found_text = ParagraphStyle(
    'style_not_found_text', parent=styles['BodyText'])
style_not_found_text.fontSize = 12
style_not_found_text.textColor = 'green'
style_not_found_text.alignment = TA_CENTER

leave_request_columns = [{"label": 'Employee', 'key': 'employee__user__username',
                          'get_content': lambda obj:
                          [Paragraph(f''' <b>{obj['employee__user__username']}</b>'''),
                           Paragraph(f''' <para>{obj['employee__user__email']}</para>''')]},
                         {"label": 'Request No', 'key': 'request_number'},
                         {"label": 'Range', 'key': 'from_date'},
                         {"label": 'Type', 'key': 'type__code'},
                         {"label": 'Duration', 'key': 'duration__code'},
                         ]
leave_count_columns = [{"label": 'Employee', 'key': 'employee__user__username',
                        'get_content': lambda obj:
                       [Paragraph(f''' <b>{obj['employee__user__username']}</b>'''),
                        Paragraph(f''' <para>{obj['employee__user__email']}</para>''')]},
                       {"label": 'Leave Count', 'key': 'leave_count'}, ]

absentees_columns = [{"label": 'Employee', 'key': 'employee__user__username',
                      'get_content': lambda obj:
                      [Paragraph(f''' <b>{obj['employee__user__username']}</b>'''),
                       Paragraph(f''' <para>{obj['employee__user__email']}</para>''')]},
                     {"label": 'Leave Type', 'key': 'type__code'},
                     {"label": 'Leave Duration', 'key': 'duration__code'},
                     ]

absentees_excel_columns = [{"label": 'Name', 'key': 'employee__user__username'},
                           {"label": 'Email', 'key': 'employee__user__email'},
                           {"label": 'Leave Type', 'key': 'type__code'},
                           {"label": 'Leave Duration', 'key': 'duration__code'},
                           {"label": 'Group', 'key': "employee__teams__team__name"},
                           ]
