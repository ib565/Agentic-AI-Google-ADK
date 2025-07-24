import os
import json
import logging
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from dotenv import load_dotenv

from ..models import LessonPlanOutput

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Configuration constants
APP_NAME = "lesson_planner_app"
USER_ID = "user_1"
SESSION_ID = "lesson_session_001"


# Agent configuration
lesson_planner_agent = Agent(
    name="lesson_planner_agent",
    model="gemini-2.0-flash",
    description=(
        "Agent to help teachers create comprehensive lesson plans based on given requirements."
    ),
    instruction=(
        "You are a helpful lesson planning assistant for teachers. "
        "You will be given a description from a teacher that may or may not include topic, grade level, number of lessons, duration, learning objectives, and other specific requirements. "
        "The input may be very detailed or just a simple topic - adapt accordingly. "
        "Create a comprehensive lesson plan with individual lessons. "
        "Make the content age-appropriate, engaging, and educationally sound. "
        "Include diverse teaching methods (discussion, hands-on activities, multimedia, etc.). "
        "Ensure lessons build upon each other logically. "
        "Be specific about activities and learning outcomes. "
        "If number of lessons isn't specified, create 5-8 lessons. "
        "If duration isn't specified, assume 60-minute class periods. "
        "Respond ONLY with a JSON object of the format: "
        "{"
        '  "title": "string", '
        '  "grade_level": "string", '
        '  "total_duration": "string", '
        '  "learning_goals": "string", '
        '  "overview": "string", '
        '  "lessons": ['
        "    {"
        '      "lesson_number": number, '
        '      "title": "string", '
        '      "duration": "string", '
        '      "content": "string", '
        '      "key_learning_points": "string"'
        "    }"
        "  ]"
        "}"
    ),
    output_schema=LessonPlanOutput,
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
        f"Create a comprehensive lesson plan with the following specifications:\n\n"
        f"Subject: {subject}\n"
        f"Grade Level: {grade}\n"
    )

    if topic:
        prompt_text += f"Topic: {topic}\n"

    if description:
        prompt_text += f"Additional Instructions: {description}\n"

    prompt_text += (
        f"\nPlease create an appropriate lesson plan for grade {grade} students in {subject}. "
        f"If any key details are missing (number of lessons, duration), make reasonable assumptions "
        f"based on the grade level and subject. Make the content age-appropriate and engaging."
    )

    return types.Content(
        role="user",
        parts=[
            types.Part(text=prompt_text),
        ],
    )


async def run_lesson_planner_agent(
    runner: Runner, message_content: types.Content
) -> LessonPlanOutput:
    """Run the lesson planner agent and return the structured lesson plan."""
    logger.info("Running lesson planner agent...")

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
                            lesson_plan = LessonPlanOutput(**part.function_response)
                            logger.info(
                                f"Successfully created lesson plan: '{lesson_plan.title}'"
                            )
                            return lesson_plan
                        except Exception as e:
                            logger.error(f"Error parsing function_response: {e}")
                            continue

                    # Check if it's text content
                    elif hasattr(part, "text") and part.text:
                        text_content = part.text.strip()
                        try:
                            data = json.loads(text_content)
                            lesson_plan = LessonPlanOutput(**data)
                            logger.info(
                                f"Successfully created lesson plan: '{lesson_plan.title}'"
                            )
                            return lesson_plan
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON parsing error: {e}")
                        except Exception as e:
                            logger.error(f"Error creating LessonPlanOutput: {e}")

        raise Exception("Failed to extract lesson plan data from agent response")

    except Exception as e:
        logger.error(f"Error running lesson planner agent: {e}")
        raise


async def generate_lesson_plan(
    subject: str, grade: int, topic: str = None, description: str = None
) -> LessonPlanOutput:
    """Generate a lesson plan from structured parameters."""
    try:
        logger.info(
            f"Generating lesson plan: subject={subject}, grade={grade}, topic={topic}"
        )

        # Setup session and services
        logger.debug("Setting up session and services...")
        session_service, session = await setup_session()

        # Create runner
        runner = Runner(
            app_name=APP_NAME,
            agent=lesson_planner_agent,
            session_service=session_service,
        )

        # Create message content
        message_content = create_message_content(subject, grade, topic, description)

        # Run agent to generate lesson plan
        lesson_plan = await run_lesson_planner_agent(runner, message_content)

        logger.info("Successfully generated lesson plan")
        return lesson_plan

    except Exception as e:
        logger.error(f"Error generating lesson plan: {e}")
        raise
