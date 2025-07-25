import logging
from google.adk.agents import Agent
from google.genai import types

from .base_agent import BaseAgent
from ..models import QuizOutput

# Configure logging
logger = logging.getLogger(__name__)


class QuizAgent(BaseAgent[QuizOutput]):
    """Agent for creating educational quizzes and assessments."""

    def __init__(self):
        # Agent configuration
        agent = Agent(
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
            ),
            output_schema=QuizOutput,
        )

        super().__init__(agent, app_name="quiz_app")

    def create_message_content(
        self, subject: str, grade: int, topic: str = None, description: str = None
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

    def parse_response_to_output(self, response_data: dict) -> QuizOutput:
        """Parse agent response to QuizOutput."""
        return QuizOutput(**response_data)


# Create a global instance of the agent
_quiz_agent = QuizAgent()


async def generate_quiz(
    subject: str, grade: int, topic: str = None, description: str = None
) -> QuizOutput:
    """Generate quiz from structured parameters."""
    return await _quiz_agent.generate(
        subject=subject, grade=grade, topic=topic, description=description
    )
