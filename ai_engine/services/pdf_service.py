import io
import logging
from time import perf_counter
from datetime import datetime, timezone
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration
import markdown
import re

from ..models import WorksheetOutput, LessonPlanOutput, StudyMaterialOutput

# Configure logging
logger = logging.getLogger(__name__)


def process_markdown_content(text: str) -> str:
    """Convert markdown text to HTML, handling common formatting and newlines."""
    if not text:
        return ""

    # Initialize markdown with extensions for better formatting
    md = markdown.Markdown(extensions=["nl2br", "fenced_code"])

    # Convert markdown to HTML
    html = md.convert(text)

    # Remove outer <p> tags since we'll add our own structure
    html = re.sub(r"^<p>(.*)</p>$", r"\1", html, flags=re.DOTALL)

    return html


def create_html_from_study_material(study_material: StudyMaterialOutput) -> str:
    """Convert structured study material data to HTML."""
    html_content = f"""<!doctype html>
<html>
    <head>
        <meta charset="utf-8">
        <title>{study_material.title}</title>
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
            .meta-info {{
                color: #7f8c8d;
                margin: 5px 0;
            }}
            .overview {{
                background-color: #f8f9fa;
                padding: 15px;
                border-left: 4px solid #3498db;
                margin: 20px 0;
            }}
            .overview p, .learning-objectives p, .key-concepts p, .practice-problems p {{
                margin: 8px 0;
            }}
            .overview strong, .learning-objectives strong, .key-concepts strong, .practice-problems strong {{
                font-weight: bold;
                color: #2c3e50;
            }}
            .overview em, .learning-objectives em, .key-concepts em, .practice-problems em {{
                font-style: italic;
            }}
            .learning-objectives {{
                background-color: #e8f5e8;
                padding: 15px;
                border-left: 4px solid #27ae60;
                margin: 20px 0;
            }}
            .section {{
                margin: 30px 0;
                padding: 20px;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
            }}
            .section-title {{
                color: #2c3e50;
                margin-bottom: 15px;
                border-bottom: 1px solid #bdc3c7;
                padding-bottom: 5px;
            }}
            .section-content {{
                margin: 15px 0;
                text-align: justify;
            }}
            .section-content p {{
                margin: 10px 0;
            }}
            .section-content strong {{
                font-weight: bold;
                color: #2c3e50;
            }}
            .section-content em {{
                font-style: italic;
            }}
            .section-content ul, .section-content ol {{
                margin: 10px 0;
                padding-left: 25px;
            }}
            .section-content li {{
                margin: 5px 0;
            }}
            .key-concepts {{
                background-color: #fff3cd;
                padding: 15px;
                border-left: 4px solid #ffc107;
                margin: 20px 0;
            }}
            .practice-problems {{
                background-color: #f0f8ff;
                padding: 15px;
                border-left: 4px solid #17a2b8;
                margin: 20px 0;
            }}
            .section-header {{
                color: #2c3e50;
                margin: 20px 0 10px 0;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{study_material.title}</h1>
            <div class="meta-info">Grade Level: {study_material.grade_level}</div>
            <div class="meta-info">Subject: {study_material.subject}</div>
        </div>
        
        <div class="overview">
            <h3>Overview</h3>
            <div>{process_markdown_content(study_material.overview)}</div>
        </div>
        
        <div class="learning-objectives">
            <h3>Learning Objectives</h3>
            <div>{process_markdown_content(study_material.learning_objectives)}</div>
        </div>
        
        <div class="section-header">
            <h2>Study Content</h2>
        </div>"""

    # Add individual sections
    for section in study_material.sections:
        html_content += f"""
        <div class="section">
            <h3 class="section-title">{section.section_title}</h3>
            <div class="section-content">
                {process_markdown_content(section.content)}
            </div>
        </div>"""

    # Add key concepts if provided
    if study_material.key_concepts:
        html_content += f"""
        <div class="key-concepts">
            <h3>Key Concepts</h3>
            <div>{process_markdown_content(study_material.key_concepts)}</div>
        </div>"""

    # Add practice problems if provided
    if study_material.practice_problems:
        html_content += f"""
        <div class="practice-problems">
            <h3>Practice Problems</h3>
            <div>{process_markdown_content(study_material.practice_problems)}</div>
        </div>"""

    html_content += """
    </body>
</html>"""

    return html_content


def create_html_from_lesson_plan(lesson_plan: LessonPlanOutput) -> str:
    """Convert structured lesson plan data to HTML."""
    html_content = f"""<!doctype html>
<html>
    <head>
        <meta charset="utf-8">
        <title>{lesson_plan.title}</title>
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
            .meta-info {{
                color: #7f8c8d;
                margin: 5px 0;
            }}
            .overview {{
                background-color: #f8f9fa;
                padding: 15px;
                border-left: 4px solid #3498db;
                margin: 20px 0;
            }}
            .lesson {{
                margin: 30px 0;
                padding: 20px;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
            }}
            .lesson-title {{
                color: #2c3e50;
                margin-bottom: 10px;
                border-bottom: 1px solid #bdc3c7;
                padding-bottom: 5px;
            }}
            .lesson-duration {{
                color: #27ae60;
                font-weight: bold;
                margin-bottom: 15px;
            }}
            .lesson-content {{
                margin: 15px 0;
            }}
            .lesson-points {{
                background-color: #f8f9fa;
                padding: 10px;
                border-radius: 3px;
                margin-top: 15px;
            }}
            .section-header {{
                color: #2c3e50;
                margin: 20px 0 10px 0;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{lesson_plan.title}</h1>
            <div class="meta-info">Grade Level: {lesson_plan.grade_level}</div>
            <div class="meta-info">Total Duration: {lesson_plan.total_duration}</div>
        </div>
        
        <div class="section-header">
            <h2>Learning Goals</h2>
        </div>
        <div>{process_markdown_content(lesson_plan.learning_goals)}</div>
        
        <div class="overview">
            <h3>Overview</h3>
            <div>{process_markdown_content(lesson_plan.overview)}</div>
        </div>
        
        <div class="section-header">
            <h2>Lesson Breakdown</h2>
        </div>"""

    # Add individual lessons
    for lesson in lesson_plan.lessons:
        html_content += f"""
        <div class="lesson">
            <h3 class="lesson-title">Lesson {lesson.lesson_number}: {lesson.title}</h3>
            <div class="lesson-duration">Duration: {lesson.duration}</div>
            <div class="lesson-content">
                <h4>Content & Activities:</h4>
                <div>{process_markdown_content(lesson.content)}</div>
            </div>
            <div class="lesson-points">
                <h4>Key Learning Points:</h4>
                <div>{process_markdown_content(lesson.key_learning_points)}</div>
            </div>
        </div>"""

    html_content += """
    </body>
</html>"""

    return html_content


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
    try:
        font_config = FontConfiguration()
        bytes_io = io.BytesIO()

        doc = HTML(string=html_content).render(font_config=font_config)
        doc.metadata.authors = ["Worksheet Generator"]
        doc.metadata.created = datetime.now(timezone.utc).isoformat()
        doc.metadata.title = "Worksheet"

        doc.write_pdf(bytes_io)

        duration = perf_counter() - start
        logger.debug(f"PDF generation completed in {duration:.1f}s")
        return bytes_io

    except Exception as e:
        logger.error(f"Error in PDF generation: {e}")
        raise


def lesson_plan_to_pdf_bytes(lesson_plan: LessonPlanOutput) -> bytes:
    """Converts a structured lesson plan to PDF bytes using WeasyPrint."""
    logger.info(
        f"Converting lesson plan '{lesson_plan.title}' (Grade {lesson_plan.grade_level}) to PDF..."
    )

    try:
        # Convert lesson plan to HTML
        html = create_html_from_lesson_plan(lesson_plan)

        # Convert HTML to PDF
        pdf_bytes_io = html2pdf(html)
        pdf_bytes = pdf_bytes_io.getvalue()

        logger.info(f"PDF conversion successful: {len(pdf_bytes)} bytes")
        return pdf_bytes

    except Exception as e:
        logger.error(f"Error converting lesson plan to PDF: {e}")
        raise


def worksheet_to_pdf_bytes(worksheet: WorksheetOutput) -> bytes:
    """Converts a structured worksheet to PDF bytes using WeasyPrint."""
    logger.info(
        f"Converting worksheet '{worksheet.title}' (Grade {worksheet.grade_level}) to PDF..."
    )

    try:
        # Convert worksheet to HTML
        html = create_html_from_worksheet(worksheet)

        # Convert HTML to PDF
        pdf_bytes_io = html2pdf(html)
        pdf_bytes = pdf_bytes_io.getvalue()

        logger.info(f"PDF conversion successful: {len(pdf_bytes)} bytes")
        return pdf_bytes

    except Exception as e:
        logger.error(f"Error converting worksheet to PDF: {e}")
        raise


def study_material_to_pdf_bytes(study_material: StudyMaterialOutput) -> bytes:
    """Converts a structured study material to PDF bytes using WeasyPrint."""
    logger.info(
        f"Converting study material '{study_material.title}' (Grade {study_material.grade_level}) to PDF..."
    )

    try:
        # Convert study material to HTML
        html = create_html_from_study_material(study_material)

        # Convert HTML to PDF
        pdf_bytes_io = html2pdf(html)
        pdf_bytes = pdf_bytes_io.getvalue()

        logger.info(f"PDF conversion successful: {len(pdf_bytes)} bytes")
        return pdf_bytes

    except Exception as e:
        logger.error(f"Error converting study material to PDF: {e}")
        raise
