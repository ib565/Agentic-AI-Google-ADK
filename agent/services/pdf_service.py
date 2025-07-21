import io
from time import perf_counter
from datetime import datetime, timezone
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration

from ..models import WorksheetOutput


def create_html_from_worksheet(worksheet: WorksheetOutput) -> str:
    """Convert structured worksheet data to HTML."""
    html_content = f"""<!doctype html>
<html>
    <head>
        <meta charset="utf-8">
        <title>{worksheet.title}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 40px;
                line-height: 1.6;
                color: #333;
            }}
            .header {{
                text-align: center;
                border-bottom: 2px solid #333;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }}
            h1 {{
                color: #2c3e50;
                margin: 0;
            }}
            .grade-subject {{
                color: #7f8c8d;
                margin: 5px 0;
            }}
            .instructions {{
                background-color: #f8f9fa;
                padding: 15px;
                border-left: 4px solid #3498db;
                margin: 20px 0;
                font-style: italic;
            }}
            .section {{
                margin: 30px 0;
            }}
            .section-title {{
                color: #2c3e50;
                border-bottom: 1px solid #bdc3c7;
                padding-bottom: 5px;
                margin-bottom: 15px;
            }}
            .question {{
                margin: 15px 0;
                padding: 10px 0;
            }}
            .question-number {{
                font-weight: bold;
                color: #2980b9;
            }}
            .answer-space {{
                border-bottom: 1px solid #333;
                display: inline-block;
                min-width: 200px;
                margin: 0 5px;
            }}
            .short-answer-space {{
                border-bottom: 1px solid #333;
                height: 60px;
                margin: 10px 0;
                width: 100%;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{worksheet.title}</h1>
            <div class="grade-subject">Grade {worksheet.grade_level} • {worksheet.subject}</div>
            <div>Name: _________________________ Date: _____________</div>
        </div>
        
        <div class="section">
            <h2 class="section-title">Part A: Fill in the Blanks</h2>"""

    # Add fill-in-the-blank questions
    for i, question in enumerate(worksheet.fill_in_blanks, 1):
        # Replace common blank markers with styled blanks
        question_text = question.question_text
        for blank_marker in ["_____", "[blank]", "___"]:
            question_text = question_text.replace(
                blank_marker, '<span class="answer-space"></span>'
            )

        html_content += f"""
            <div class="question">
                <span class="question-number">{i}.</span> {question_text}
            </div>"""

    html_content += """
        </div>
        
        <div class="section">
            <h2 class="section-title">Part B: Short Answer Questions</h2>"""

    # Add short answer questions
    for i, question in enumerate(worksheet.short_answers, 1):
        html_content += f"""
            <div class="question">
                <div><span class="question-number">{i}.</span> {question.question}</div>
                <div class="short-answer-space"></div>
            </div>"""

    html_content += """
        </div>
        
        <div class="section" style="page-break-before: always; margin-top: 50px;">
            <h2 class="section-title">Answer Key</h2>
            
            <div style="margin: 20px 0;">
                <h3 style="color: #2c3e50; margin-bottom: 10px;">Part A: Fill in the Blanks</h3>"""

    # Add fill-in-the-blank answers
    for i, question in enumerate(worksheet.fill_in_blanks, 1):
        html_content += f"""
                <div style="margin: 8px 0;">
                    <span class="question-number">{i}.</span> {question.answer}
                </div>"""

    html_content += """
            </div>
            
            <div style="margin: 20px 0;">
                <h3 style="color: #2c3e50; margin-bottom: 10px;">Part B: Short Answer Questions</h3>"""

    # Add short answer expected answers
    for i, question in enumerate(worksheet.short_answers, 1):
        html_content += f"""
                <div style="margin: 15px 0; padding: 10px; background-color: #f8f9fa; border-radius: 5px;">
                    <div style="font-weight: bold; margin-bottom: 5px;">
                        <span class="question-number">{i}.</span> {question.question}
                    </div>
                    <div style="color: #2c3e50; font-style: italic;">
                        Expected Answer: {question.expected_answer}
                    </div>
                </div>"""

    html_content += """
            </div>
        </div>
    </body>
</html>"""

    return html_content


def html2pdf(html_content: str) -> io.BytesIO:
    """Convert HTML content to PDF bytes."""
    start = perf_counter()
    font_config = FontConfiguration()
    bytes_io = io.BytesIO()

    doc = HTML(string=html_content).render(font_config=font_config)
    doc.metadata.authors = ["Worksheet Generator"]
    doc.metadata.created = datetime.now(timezone.utc).isoformat()
    doc.metadata.title = "Worksheet"

    doc.write_pdf(bytes_io)
    print(f"PDF generation completed in {perf_counter() - start:.1f}s")
    return bytes_io


def worksheet_to_pdf_bytes(worksheet: WorksheetOutput) -> bytes:
    """Converts a structured worksheet to PDF bytes using WeasyPrint."""
    print(
        f"Converting worksheet '{worksheet.title}' (Grade {worksheet.grade_level}) to PDF..."
    )

    try:
        # Convert worksheet to HTML
        html = create_html_from_worksheet(worksheet)

        # Convert HTML to PDF
        pdf_bytes_io = html2pdf(html)
        pdf_bytes = pdf_bytes_io.getvalue()
        print(f"PDF conversion successful: {len(pdf_bytes)} bytes")

        return pdf_bytes

    except Exception as e:
        print(f"Error converting worksheet to PDF: {e}")
        raise
