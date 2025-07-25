import os
import json
import logging
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from dotenv import load_dotenv

from ..models import QuizOutput

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Configuration constants
APP_NAME = "quiz_app"
USER_ID = "user_1"
SESSION_ID = "quiz_session_001"


# Agent configuration
quiz_agent = Agent(
    name="quiz_agent",
    model="gemini-2.0-flash",
    description=(
        "Agent to help teachers create quiz content that is instrumental in evaluating students on their understading of a subject and topic."
    ),
    instruction=(
        "You are an educational content creator that creates quizzes to help teachers evaluate students. "
        "Create quizzes which are either Multiple choice, Single choice or True/False questions which are targeted at gauging student understanding on a subject/topic "
        ""
        "Guidelines: "
        "• Give the total marks of the entire quiz "
        "• Provide marks to each question based on the weightage "
        "• Provide appropriate options based on the question type "
        "• The questions should be clear and concise "
        "• Include the correct answer in your output as well"
        "• Generate sequential question numbers which can be later used for evaluation "
        ""
        "Create quiz as if students are taking the exam and have been given the set of questions.  "
        "Make the content comprehensive enough to cover all aspects of the given topic and subject. "
        "If grade level or other details aren't specified, make reasonable assumptions based on topic complexity. "
        # "Respond ONLY with a JSON object of the format: "
        # "{"
        # '  "title": "string", '
        # '  "grade_level": "string", '
        # '  "subject": "string", '
        # '  "overview": "string", '
        # '  "learning_objectives": "string", '
        # '  "sections": ['
        # "    {"
        # '      "section_title": "string", '
        # '      "content": "string"'
        # "    }"
        # "  ], "
        # '  "key_concepts": "string", '
        # '  "practice_problems": "string"'
        # "}"
    ),
    output_schema=QuizOutput,
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
        f"Create comprehensive quiz for student with the following specifications:\n\n"
        f"Subject: {subject}\n"
        f"Grade Level: {grade}\n"
    )

    if topic:
        prompt_text += f"Topic: {topic}\n"

    if description:
        prompt_text += f"Additional Instructions: {description}\n"

    prompt_text += (
        f"\nPlease create detailed quiz with topics and subtopics appropriate for "
        f"grade {grade} students studying {subject}. Make the content comprehensive enough to "
        f"serve as an instrument for the teacher to be able to evaluate the students on their understanding. "
        f"The questions should be appropriate as per the grade of the students."
    )

    return types.Content(
        role="user",
        parts=[
            types.Part(text=prompt_text),
        ],
    )


async def run_quiz_agent(
    runner: Runner, message_content: types.Content
) -> QuizOutput:
    """Run the squiz agent and return the structured quiz material."""
    logger.info("Running quiz agent...")

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
                            quiz = QuizOutput(
                                **part.function_response
                            )
                            logger.info(
                                f"Successfully created quiz"
                            )
                            return quiz
                        except Exception as e:
                            logger.error(f"Error parsing function_response: {e}")
                            continue

                    # Check if it's text content
                    elif hasattr(part, "text") and part.text:
                        text_content = part.text.strip()
                        try:
                            data = json.loads(text_content)
                            quiz = QuizOutput(**data)
                            print(f"Data: {data}")
                            logger.info(
                                f"Successfully created quiz"
                            )
                            return quiz
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON parsing error: {e}")
                        except Exception as e:
                            logger.error(f"Error creating QuizOutput: {e}")

        raise Exception("Failed to extract quiz data from agent response")

    except Exception as e:
        logger.error(f"Error running quiz agent: {e}")
        raise


async def generate_quiz(
    subject: str, grade: int, topic: str = None, description: str = None
) -> QuizOutput:
    """Generate quiz from structured parameters."""
    try:
        logger.info(
            f"Generating quiz: subject={subject}, grade={grade}, topic={topic}"
        )

        # Setup session and services
        logger.debug("Setting up session and services...")
        session_service, session = await setup_session()

        # Create runner
        runner = Runner(
            app_name=APP_NAME,
            agent=quiz_agent,
            session_service=session_service,
        )

        # Create message content
        message_content = create_message_content(subject, grade, topic, description)

        # Run agent to generate study material
        quiz = await run_quiz_agent(runner, message_content)

        logger.info("Successfully generated quiz")
        return quiz

    except Exception as e:
        logger.error(f"Error generating quiz: {e}")
        raise
