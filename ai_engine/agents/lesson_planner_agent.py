import logging
from google.adk.agents import Agent
from google.genai import types

from .base_agent import BaseAgent
from ..models import LessonPlanOutput

# Configure logging
logger = logging.getLogger(__name__)


class LessonPlannerAgent(BaseAgent[LessonPlanOutput]):
    """Agent for creating comprehensive lesson plans."""

    def __init__(self):
        # Agent configuration
        agent = Agent(
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

        super().__init__(agent, app_name="lesson_planner_app")

    def create_message_content(
        self, subject: str, grade: int, topic: str = None, description: str = None
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

    def parse_response_to_output(self, response_data: dict) -> LessonPlanOutput:
        """Parse agent response to LessonPlanOutput."""
        return LessonPlanOutput(**response_data)


# Create a global instance of the agent
_lesson_planner_agent = LessonPlannerAgent()


async def generate_lesson_plan(
    subject: str, grade: int, topic: str = None, description: str = None
) -> LessonPlanOutput:
    """Generate a lesson plan from structured parameters."""
    return await _lesson_planner_agent.generate(
        subject=subject, grade=grade, topic=topic, description=description
    )
