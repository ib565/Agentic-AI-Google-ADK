import os
import json
import logging
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from dotenv import load_dotenv

from ..models import WorksheetOutput

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Configuration constants
APP_NAME = "worksheet_tutorial_app"
USER_ID = "user_1"
SESSION_ID = "session_001"


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


async def setup_session() -> tuple:
    """Set up session and required services."""
    try:
        session_service = InMemorySessionService()
        session = await session_service.create_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
        )
        logger.debug("Session setup completed successfully")
        return session_service, session
    except Exception as e:
        logger.error(f"Failed to setup session: {e}")
        raise


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
    logger.info("Running worksheet agent...")

    try:
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
                            worksheet = WorksheetOutput(**part.function_response)
                            logger.info(
                                f"Successfully created worksheet: '{worksheet.title}'"
                            )
                            return worksheet
                        except Exception as e:
                            logger.error(f"Error parsing function_response: {e}")
                            continue

                    # Check if it's text content
                    elif hasattr(part, "text") and part.text:
                        text_content = part.text.strip()
                        try:
                            data = json.loads(text_content)
                            worksheet = WorksheetOutput(**data)
                            logger.info(
                                f"Successfully created worksheet: '{worksheet.title}'"
                            )
                            return worksheet
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON parsing error: {e}")
                        except Exception as e:
                            logger.error(f"Error creating WorksheetOutput: {e}")

        raise Exception("Failed to extract worksheet data from agent response")

    except Exception as e:
        logger.error(f"Error running worksheet agent: {e}")
        raise


async def generate_worksheet_from_image(
    image_bytes: bytes, grade: int, filename: str = "image.png"
) -> WorksheetOutput:
    """Generate a worksheet from image bytes for a specific grade level."""
    try:
        logger.info(f"Generating worksheet for grade {grade} from image: {filename}")

        # Setup session and services
        logger.debug("Setting up session and services...")
        session_service, session = await setup_session()

        # Create runner
        runner = Runner(
            app_name=APP_NAME,
            agent=worksheet_agent,
            session_service=session_service,
        )

        # Create message content
        message_content = create_message_content(image_bytes, grade, filename)

        # Run agent to generate structured worksheet
        worksheet = await run_worksheet_agent(runner, message_content)

        logger.info(f"Successfully generated worksheet for grade {grade}")
        return worksheet

    except Exception as e:
        logger.error(f"Error generating worksheet: {e}")
        raise
