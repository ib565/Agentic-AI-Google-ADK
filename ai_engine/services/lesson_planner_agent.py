import os
import logging
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from dotenv import load_dotenv

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
        "You will be given a description from a teacher that may or may not include topic, grade level, number of lessons, duration, learning objectives, and other specific requirements."
        "The input may be very detailed or just a simple topic - adapt accordingly. "
        "Create a comprehensive lesson plan that includes: "
        "1. LESSON PLAN OVERVIEW with title, goal/objectives, target grade level, total duration, and brief description "
        "2. INDIVIDUAL LESSONS - each with lesson number, title, content/activities, duration "
        "Structure your response as follows: "
        "LESSON PLAN TITLE: [Creative, engaging title] "
        "GRADE LEVEL: [Target grade] "
        "TOTAL DURATION: [Overall timeframe] "
        "LEARNING GOALS: [Clear, measurable objectives] "
        "OVERVIEW: [Brief description of what students will learn] "
        ""
        "LESSON BREAKDOWN: "
        "Lesson [#]: [Title] "
        "Duration: [Time needed] "
        "Content: [Detailed description of activities, concepts to cover, teaching methods] "
        "Key Learning Points: [What students should understand] "
        ""
        "[Repeat for each lesson] "
        "Make the content age-appropriate, engaging, and educationally sound. "
        "Include diverse teaching methods (discussion, hands-on activities, multimedia, etc.). "
        "Ensure lessons build upon each other logically. "
        "Be specific about activities and learning outcomes. "
        "If number of lessons isn't specified, create 5-8 lessons. "
        "If duration isn't specified, assume 60-minute class periods. "
    ),
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


def create_message_content(teacher_input: str) -> types.Content:
    """Create properly formatted message content with teacher's requirements."""

    prompt_text = (
        f"Create a comprehensive lesson plan based on the following teacher requirements: "
        f"\n\nTeacher Input: {teacher_input}\n\n"
        f"Please analyze the input and create an appropriate lesson plan. "
        f"If any key details are missing (grade level, number of lessons, duration), "
        f"make reasonable assumptions."
    )

    return types.Content(
        role="user",
        parts=[
            types.Part(text=prompt_text),
        ],
    )


async def run_lesson_planner_agent(
    runner: Runner, message_content: types.Content
) -> str:
    """Run the lesson planner agent and return the lesson plan text."""
    logger.info("Running lesson planner agent...")

    try:
        lesson_plan_text = ""

        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=message_content,
        ):
            if event.is_final_response():
                if not event.content or not event.content.parts:
                    continue

                for part in event.content.parts:
                    # Check if it's text content
                    if hasattr(part, "text") and part.text:
                        lesson_plan_text = part.text.strip()
                        logger.info("Successfully generated lesson plan")
                        return lesson_plan_text

        if not lesson_plan_text:
            raise Exception("Failed to extract lesson plan from agent response")

        return lesson_plan_text

    except Exception as e:
        logger.error(f"Error running lesson planner agent: {e}")
        raise


async def generate_lesson_plan(teacher_input: str) -> str:
    """Generate a lesson plan from teacher's requirements string."""
    try:
        logger.info(
            f"Generating lesson plan from teacher input: {teacher_input[:100]}..."
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
        message_content = create_message_content(teacher_input)

        # Run agent to generate lesson plan
        lesson_plan = await run_lesson_planner_agent(runner, message_content)

        logger.info("Successfully generated lesson plan")
        return lesson_plan

    except Exception as e:
        logger.error(f"Error generating lesson plan: {e}")
        raise
