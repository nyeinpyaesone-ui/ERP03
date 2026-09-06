"""
PDF Export Service using reportlab
Generates PDF reports from data
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from typing import List, Dict, Any
import io

class PDFExporter:
    """Generate PDF reports from data"""
    
    def __init__(self, pagesize=A4):
        self.pagesize = pagesize
        
    def export(self, data: List[Dict[str, Any]], title: str = "Report", 
               headers: List[str] = None) -> bytes:
        """Export list of dicts to PDF binary"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=self.pagesize,
                               rightMargin=0.5*inch, leftMargin=0.5*inch,
                               topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            alignment=1,  # Center
            spaceAfter=20
        )
        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        if not data:
            doc.build(elements)
            return buffer.getvalue()
        
        # Headers
        if headers is None:
            headers = list(data[0].keys())
        
        # Table data
        table_data = [headers]
        for row in data:
            table_data.append([row.get(h, '') for h in headers])
        
        # Create table
        table = Table(table_data, repeatRows=1)
        
        # Table style
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#D9E2F3')]),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ])
        table.setStyle(style)
        
        # Auto-width columns
        col_widths = []
        for col_idx in range(len(headers)):
            max_width = 0
            for row in table_data:
                cell_value = str(row[col_idx])
                # Approximate width calculation
                width = len(cell_value) * 0.15 * inch
                max_width = max(max_width, min(width, 2.5*inch))
            col_widths.append(max_width)
        
        table._argW = col_widths
        
        elements.append(table)
        doc.build(elements)
        
        return buffer.getvalue()
