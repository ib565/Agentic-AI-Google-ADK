import os
import asyncio
import re
import io
from time import perf_counter
from datetime import datetime
from mistune import markdown
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

# Agent configuration
worksheet_agent = Agent(
    name="worksheet_agent",
    model="gemini-2.0-flash",
    description=("Agent to help a teacher create a worksheet, based on given content."),
    instruction="You are a helpful worksheet assistant. "
    "You will be given an image of a textbook page, and you will need to create a markdown formatted worksheet based on the content of the page. "
    "Create a worksheet that is 10-15 questions long, with a mix of multiple choice questions and fill in the blanks. Keep the formatting minimal."
    "IMPORTANT: Return ONLY the raw markdown content without any code block markers (```markdown, ```, etc.). "
    "Do not wrap your response in code blocks or add any formatting markers. "
    "Start directly with the worksheet title and content.",
)


def clean_llm_response(response_text: str) -> str:
    """
    Clean LLM response by removing code block markers but keeping markdown symbols.

    Args:
        response_text: Raw response from LLM

    Returns:
        Cleaned markdown content
    """
    if not response_text:
        return ""

    # Remove common code block patterns
    patterns_to_remove = [
        r"^```markdown\s*\n",  # Opening ```markdown
        r"^```\s*\n",  # Opening ```
        r"\n```\s*$",  # Closing ```
        r"^```markdown\s*",  # Opening ```markdown without newline
        r"^```\s*",  # Opening ``` without newline
        r"```\s*$",  # Closing ``` without newline
    ]

    cleaned_text = response_text.strip()

    for pattern in patterns_to_remove:
        cleaned_text = re.sub(pattern, "", cleaned_text, flags=re.MULTILINE)

    # Additional cleanup: remove any remaining ``` that might be scattered
    cleaned_text = re.sub(r"```", "", cleaned_text)

    return cleaned_text.strip()


def md2html(md_content: str, title: str = "Worksheet") -> str:
    """Convert markdown content to HTML with styling."""
    html = markdown(md_content)

    html_doc = f"""<!doctype html>
<html>
    <head>
        <meta charset="utf-8">
        <title>{title}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 40px;
                line-height: 1.5;
            }}
            h1 {{
                color: #333;
                border-bottom: 1px solid #ccc;
                padding-bottom: 10px;
            }}
            h2, h3 {{
                color: #555;
            }}
            p {{
                margin: 10px 0;
            }}
            ol, ul {{
                margin: 15px 0;
                padding-left: 30px;
            }}
            li {{
                margin: 8px 0;
            }}
        </style>
    </head>
    <body>{html}</body>
</html>"""
    return html_doc


def html2pdf(html_content: str) -> io.BytesIO:
    """Convert HTML content to PDF bytes."""
    start = perf_counter()
    font_config = FontConfiguration()
    bytes_io = io.BytesIO()

    doc = HTML(string=html_content).render(font_config=font_config)
    doc.metadata.authors = ["Worksheet Generator"]
    doc.metadata.created = datetime.now(
        datetime.utcnow().astimezone().tzinfo
    ).isoformat()
    doc.metadata.title = "Worksheet"

    doc.write_pdf(bytes_io)
    print(f"WeasyPrint PDF building duration: {perf_counter() - start:.1f}s")
    return bytes_io


def markdown_to_pdf_bytes(markdown_text: str) -> bytes:
    """Converts a Markdown string to PDF bytes using WeasyPrint."""
    print("⚙️  Converting Markdown to PDF...")

    # Clean the markdown text first
    cleaned_markdown = clean_llm_response(markdown_text)
    print(f"📝 Cleaned markdown preview: {cleaned_markdown[:200]}...")

    # Convert markdown to HTML
    html = md2html(cleaned_markdown, "Worksheet")

    # Convert HTML to PDF
    pdf_bytes_io = html2pdf(html)
    pdf_bytes = pdf_bytes_io.getvalue()

    return pdf_bytes


async def setup_session() -> tuple:
    """
    Set up session and required services.

    Returns:
        Tuple of (session_service, session, artifact_service)
    """
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )
    artifact_service = InMemoryArtifactService()

    print(f"Session: {session}")
    return session_service, session, artifact_service


def load_image(image_path: str = IMAGE_PATH) -> bytes:
    """
    Load image file and return as bytes.

    Args:
        image_path: Path to the image file

    Returns:
        Image data as bytes
    """
    with open(image_path, "rb") as f:
        return f.read()


def create_message_content(
    image_bytes: bytes, image_filename: str = "textbook.png"
) -> types.Content:
    """
    Create properly formatted message content with image and text.

    Args:
        image_bytes: Image data as bytes
        image_filename: Name of the image file

    Returns:
        Formatted message content
    """
    return types.Content(
        role="user",
        parts=[
            types.Part(
                inline_data=types.Blob(
                    data=image_bytes, mime_type="image/png", display_name=image_filename
                )
            ),
            types.Part(
                text="Create a markdown formatted worksheet based on the content of the page."
            ),
        ],
    )


async def run_worksheet_agent(runner: Runner, message_content: types.Content) -> str:
    """
    Run the worksheet agent and return the final response.

    Args:
        runner: The agent runner
        message_content: The message content to process

    Returns:
        Final response text from the agent
    """
    final_response_content = ""

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=message_content,
    ):
        print(event)
        if event.is_final_response() and event.content and event.content.parts:
            final_response_content = event.content.parts[0].text
            print(f"Final response: {final_response_content}")

    return final_response_content


def save_pdf_locally(pdf_content: bytes, output_path: str = OUTPUT_PDF_PATH) -> None:
    """
    Save PDF content to local file.

    Args:
        pdf_content: PDF data as bytes
        output_path: Path where to save the PDF file
    """
    with open(output_path, "wb") as f:
        f.write(pdf_content)
    print(f"📄 PDF saved locally as '{output_path}'")


async def save_pdf_artifact(
    artifact_service: InMemoryArtifactService,
    pdf_content: bytes,
    filename: str = "worksheet.pdf",
) -> str:
    """
    Save PDF as an artifact and return the version.

    Args:
        artifact_service: The artifact service
        pdf_content: PDF data as bytes
        filename: Name for the artifact file

    Returns:
        Artifact version string
    """
    pdf_artifact = types.Part(
        inline_data=types.Blob(
            data=pdf_content,
            mime_type="application/pdf",
            display_name=filename,
        )
    )

    artifact_version = await artifact_service.save_artifact(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        filename=filename,
        artifact=pdf_artifact,
    )

    print(f"Artifact version: {artifact_version}")
    return artifact_version


async def create_and_save_worksheet(
    image_path: str = IMAGE_PATH, output_path: str = OUTPUT_PDF_PATH
) -> str:
    """
    Main function to create and save worksheet from textbook image.

    Args:
        image_path: Path to the input image file
        output_path: Path where to save the output PDF

    Returns:
        Artifact version string
    """
    # Setup session and services
    session_service, session, artifact_service = await setup_session()

    # Create runner
    runner = Runner(
        app_name=APP_NAME,
        agent=worksheet_agent,
        session_service=session_service,
    )

    # Load and prepare image
    image_bytes = load_image(image_path)
    message_content = create_message_content(image_bytes, os.path.basename(image_path))

    # Run agent to generate worksheet
    final_response_content = await run_worksheet_agent(runner, message_content)

    # Convert to PDF
    pdf_content = markdown_to_pdf_bytes(final_response_content)

    # Save PDF locally and as artifact
    save_pdf_locally(pdf_content, output_path)
    artifact_version = await save_pdf_artifact(artifact_service, pdf_content)

    return artifact_version


async def main():
    """Main entry point."""
    await create_and_save_worksheet()


if __name__ == "__main__":
    asyncio.run(main())
