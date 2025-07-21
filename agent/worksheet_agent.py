import os
import asyncio
import io
from time import perf_counter
from datetime import datetime
from typing import List, Literal
from pydantic import BaseModel
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.artifacts import InMemoryArtifactService
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# Configuration constants
APP_NAME = "worksheet_tutorial_app"
USER_ID = "user_1"
SESSION_ID = "session_001"
IMAGE_PATH = "textbook.png"
OUTPUT_PDF_PATH = "worksheet.pdf"


# Pydantic models for structured worksheet output
class FillInTheBlankQuestion(BaseModel):
    question_text: str  # Text with blanks marked as _____ or [blank]
    answer: str  # The correct answer for the blank


class ShortAnswerQuestion(BaseModel):
    question: str  # The question text
    expected_answer: str  # Sample/expected answer (for teacher reference)


class WorksheetOutput(BaseModel):
    title: str
    grade_level: int
    subject: str
    fill_in_blanks: List[FillInTheBlankQuestion]
    short_answers: List[ShortAnswerQuestion]


# Agent configuration
worksheet_agent = Agent(
    name="worksheet_agent",
    model="gemini-2.0-flash",
    description=("Agent to help a teacher create a worksheet, based on given content."),
    instruction=(
        "You are a helpful worksheet assistant. "
        "You will be given an image of a textbook page, and you will need to create a structured worksheet based on the content of the page. "
        "Create a worksheet that has 6-8 fill-in-the-blank questions and 4-6 short answer questions. "
        "Adjust the difficulty and language complexity appropriately for the specified grade level. "
        "For fill-in-the-blank questions, use clear blanks like ______ in the question text. "
        "For short answer questions, create questions that require 1-3 sentence responses. "
        "Make sure all content is educationally appropriate and directly relates to the textbook content shown. "
        "Respond ONLY with a JSON object of the format: "
        "{"
        '  "title": "string", '
        '  "grade_level": number, '
        '  "subject": "string", '
        '  "fill_in_blanks": ['
        "    {"
        '      "question_text": "string with ______ blanks", '
        '      "answer": "string"'
        "    }"
        "  ], "
        '  "short_answers": ['
        "    {"
        '      "question": "string", '
        '      "expected_answer": "string"'
        "    }"
        "  ]"
        "}"
    ),
    output_schema=WorksheetOutput,
)


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
    doc.metadata.created = datetime.now(datetime.UTC).isoformat()
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


async def setup_session() -> tuple:
    """Set up session and required services."""
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )
    artifact_service = InMemoryArtifactService()
    return session_service, session, artifact_service


def load_image(image_path: str = IMAGE_PATH) -> bytes:
    """Load image file and return as bytes."""
    with open(image_path, "rb") as f:
        return f.read()


def create_message_content(
    image_bytes: bytes, grade: int, image_filename: str = "textbook.png"
) -> types.Content:
    """Create properly formatted message content with image and text."""
    grade_text = (
        f"Create a structured worksheet based on the content of the page. "
        f"Make the worksheet appropriate for grade {grade} students. "
        f"Adjust the difficulty level, vocabulary, and question complexity to match grade {grade} standards. "
        f"Focus on creating fill-in-the-blank questions and short answer questions that test comprehension "
        f"of the key concepts from this textbook page."
    )

    return types.Content(
        role="user",
        parts=[
            types.Part(
                inline_data=types.Blob(
                    data=image_bytes, mime_type="image/png", display_name=image_filename
                )
            ),
            types.Part(text=grade_text),
        ],
    )


async def run_worksheet_agent(
    runner: Runner, message_content: types.Content
) -> WorksheetOutput:
    """Run the worksheet agent and return the structured worksheet."""
    import json

    print("Running worksheet agent...")

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=message_content,
    ):
        if event.is_final_response():
            if not event.content or not event.content.parts:
                continue

            for part in event.content.parts:
                # Check if it's a function response (structured output)
                if hasattr(part, "function_response") and part.function_response:
                    try:
                        return WorksheetOutput(**part.function_response)
                    except Exception as e:
                        print(f"Error parsing function_response: {e}")

                # Check if it's text content
                elif hasattr(part, "text") and part.text:
                    text_content = part.text.strip()
                    try:
                        data = json.loads(text_content)
                        worksheet = WorksheetOutput(**data)
                        print(f"Successfully created worksheet: '{worksheet.title}'")
                        return worksheet
                    except json.JSONDecodeError as e:
                        print(f"JSON parsing error: {e}")
                    except Exception as e:
                        print(f"Error creating WorksheetOutput: {e}")

    print("Failed to extract worksheet data from agent response")
    return None


def save_pdf_locally(
    pdf_content: bytes, grade: int, output_path: str = OUTPUT_PDF_PATH
) -> str:
    """Save PDF content to local file with grade level in filename."""
    base_name, ext = os.path.splitext(output_path)
    graded_output_path = f"{base_name}_grade_{grade}{ext}"

    with open(graded_output_path, "wb") as f:
        f.write(pdf_content)
    print(f"PDF saved as '{graded_output_path}'")
    return graded_output_path


async def save_pdf_artifact(
    artifact_service: InMemoryArtifactService,
    pdf_content: bytes,
    grade: int,
    filename: str = "worksheet.pdf",
) -> str:
    """Save PDF as an artifact and return the version."""
    base_name, ext = os.path.splitext(filename)
    graded_filename = f"{base_name}_grade_{grade}{ext}"

    pdf_artifact = types.Part(
        inline_data=types.Blob(
            data=pdf_content,
            mime_type="application/pdf",
            display_name=graded_filename,
        )
    )

    artifact_version = await artifact_service.save_artifact(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        filename=graded_filename,
        artifact=pdf_artifact,
    )

    return artifact_version


async def create_and_save_worksheet(
    grades: list[int], image_path: str = IMAGE_PATH, output_path: str = OUTPUT_PDF_PATH
) -> dict[int, str]:
    """Main function to create and save worksheets from textbook image for multiple grades."""
    artifact_versions = {}

    try:
        # Setup session and services
        print("Setting up session and services...")
        session_service, session, artifact_service = await setup_session()

        # Create runner
        runner = Runner(
            app_name=APP_NAME,
            agent=worksheet_agent,
            session_service=session_service,
        )

        # Load image once
        if not os.path.exists(image_path):
            print(f"Error: Image file not found: {image_path}")
            return artifact_versions

        image_bytes = load_image(image_path)
        print(f"Image loaded successfully: {len(image_bytes)} bytes")

    except Exception as e:
        print(f"Error during setup: {e}")
        return artifact_versions

    # Process each grade
    for grade in grades:
        print(f"\nProcessing grade {grade}...")

        try:
            # Create grade-specific message content
            message_content = create_message_content(
                image_bytes, grade, os.path.basename(image_path)
            )

            # Run agent to generate structured worksheet
            worksheet = await run_worksheet_agent(runner, message_content)

            if worksheet is None:
                print(f"Failed to generate worksheet for grade {grade}")
                continue

            # Convert to PDF
            pdf_content = worksheet_to_pdf_bytes(worksheet)

            # Save files
            save_pdf_locally(pdf_content, grade, output_path)
            artifact_version = await save_pdf_artifact(
                artifact_service, pdf_content, grade
            )

            artifact_versions[grade] = artifact_version
            print(f"Grade {grade} completed successfully!")

        except Exception as e:
            print(f"Error processing grade {grade}: {e}")
            continue

    return artifact_versions


async def main():
    """Main entry point."""
    grades = [3, 6, 9]  # Elementary, Middle, High school

    print(f"Creating worksheets for grades: {grades}")
    artifact_versions = await create_and_save_worksheet(grades)

    print(f"\nWorksheets created successfully!")
    print("Summary:")
    for grade, version in artifact_versions.items():
        print(f"  Grade {grade}: {version}")


if __name__ == "__main__":
    asyncio.run(main())
