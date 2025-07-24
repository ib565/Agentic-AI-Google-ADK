import os
import json
import logging
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from dotenv import load_dotenv

from ..models import StudyMaterialOutput

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Configuration constants
APP_NAME = "learning_material_app"
USER_ID = "user_1"
SESSION_ID = "material_session_001"


# Agent configuration
study_material_agent = Agent(
    name="study_material_agent",
    model="gemini-2.0-flash",
    description=(
        "Agent to help teachers create detailed educational content that provides comprehensive explanations and study material like a textbook."
    ),
    instruction=(
        "You are an educational content creator that writes detailed, comprehensive study materials to help teachers. "
        "Create educational content that teaches concepts thoroughly with detailed explanations, examples, and practice problems. "
        ""
        "Guidelines: "
        "• Provide clear, thorough explanations of concepts "
        "• Include concrete examples with step-by-step solutions "
        "• Add real-world applications to make concepts relevant "
        "• Use engaging language appropriate for the target audience "
        "• Include practice problems when helpful "
        "• Focus on depth and understanding over breadth "
        "• Organize content into logical sections and subsections "
        ""
        "Write as if explaining directly to students, using analogies and relatable examples. "
        "Make the content comprehensive enough to serve as primary study material. "
        "If grade level or other details aren't specified, make reasonable assumptions based on topic complexity. "
        "Respond ONLY with a JSON object of the format: "
        "{"
        '  "title": "string", '
        '  "grade_level": "string", '
        '  "subject": "string", '
        '  "overview": "string", '
        '  "learning_objectives": "string", '
        '  "sections": ['
        "    {"
        '      "section_title": "string", '
        '      "content": "string"'
        "    }"
        "  ], "
        '  "key_concepts": "string", '
        '  "practice_problems": "string"'
        "}"
    ),
    output_schema=StudyMaterialOutput,
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
    subject: str, grade: int, topic: str = None, description: str = None
) -> types.Content:
    """Create properly formatted message content with structured parameters."""

    prompt_text = (
        f"Create comprehensive study materials with the following specifications:\n\n"
        f"Subject: {subject}\n"
        f"Grade Level: {grade}\n"
    )

    if topic:
        prompt_text += f"Topic: {topic}\n"

    if description:
        prompt_text += f"Additional Instructions: {description}\n"

    prompt_text += (
        f"\nPlease create detailed study materials with topics and subtopics appropriate for "
        f"grade {grade} students studying {subject}. Make the content comprehensive enough to "
        f"serve as primary study material, with age-appropriate language and examples. "
        f"Include clear learning objectives, well-organized sections, key concepts summary, "
        f"and practice problems where appropriate."
    )

    return types.Content(
        role="user",
        parts=[
            types.Part(text=prompt_text),
        ],
    )


async def run_study_material_agent(
    runner: Runner, message_content: types.Content
) -> StudyMaterialOutput:
    """Run the study material agent and return the structured study material."""
    logger.info("Running study material agent...")

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
                            study_material = StudyMaterialOutput(
                                **part.function_response
                            )
                            logger.info(
                                f"Successfully created study material: '{study_material.title}'"
                            )
                            return study_material
                        except Exception as e:
                            logger.error(f"Error parsing function_response: {e}")
                            continue

                    # Check if it's text content
                    elif hasattr(part, "text") and part.text:
                        text_content = part.text.strip()
                        try:
                            data = json.loads(text_content)
                            study_material = StudyMaterialOutput(**data)
                            logger.info(
                                f"Successfully created study material: '{study_material.title}'"
                            )
                            return study_material
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON parsing error: {e}")
                        except Exception as e:
                            logger.error(f"Error creating StudyMaterialOutput: {e}")

        raise Exception("Failed to extract study material data from agent response")

    except Exception as e:
        logger.error(f"Error running study material agent: {e}")
        raise


async def generate_study_material(
    subject: str, grade: int, topic: str = None, description: str = None
) -> StudyMaterialOutput:
    """Generate study materials from structured parameters."""
    try:
        logger.info(
            f"Generating study material: subject={subject}, grade={grade}, topic={topic}"
        )

        # Setup session and services
        logger.debug("Setting up session and services...")
        session_service, session = await setup_session()

        # Create runner
        runner = Runner(
            app_name=APP_NAME,
            agent=study_material_agent,
            session_service=session_service,
        )

        # Create message content
        message_content = create_message_content(subject, grade, topic, description)

        # Run agent to generate study material
        study_material = await run_study_material_agent(runner, message_content)

        logger.info("Successfully generated study material")
        return study_material

    except Exception as e:
        logger.error(f"Error generating study material: {e}")
        raise
