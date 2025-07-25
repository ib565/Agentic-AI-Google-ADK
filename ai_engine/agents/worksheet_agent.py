import logging
from google.adk.agents import Agent
from google.genai import types

from .base_agent import BaseAgent
from ..models import WorksheetOutput

# Configure logging
logger = logging.getLogger(__name__)


class WorksheetAgent(BaseAgent[WorksheetOutput]):
    """Agent for creating educational worksheets from textbook images."""

    def __init__(self):
        # Agent configuration
        agent = Agent(
            name="worksheet_agent",
            model="gemini-2.0-flash",
            description=(
                "Agent to help a teacher create a worksheet, based on given content."
            ),
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

        super().__init__(agent, app_name="worksheet_tutorial_app")

    def create_message_content(
        self,
        image_bytes: bytes,
        grade: int,
        image_filename: str = "textbook.png",
        subject: str = None,
        topic: str = None,
        description: str = None,
    ) -> types.Content:
        """Create properly formatted message content with image and structured parameters."""

        grade_text = (
            f"Create a structured worksheet based on the content of the page. "
            f"Make the worksheet appropriate for grade {grade} students. "
            f"Adjust the difficulty level, vocabulary, and question complexity to match grade {grade} standards. "
        )

        if subject:
            grade_text += f"The worksheet should focus on {subject}. "

        if topic:
            grade_text += f"Pay special attention to the topic of {topic}. "

        if description:
            grade_text += f"Additional instructions: {description}. "

        grade_text += (
            f"Focus on creating fill-in-the-blank questions and short answer questions that test comprehension "
            f"of the key concepts from this textbook page."
        )

        return types.Content(
            role="user",
            parts=[
                types.Part(
                    inline_data=types.Blob(
                        data=image_bytes,
                        mime_type="image/png",
                        display_name=image_filename,
                    )
                ),
                types.Part(text=grade_text),
            ],
        )

    def parse_response_to_output(self, response_data: dict) -> WorksheetOutput:
        """Parse agent response to WorksheetOutput."""
        return WorksheetOutput(**response_data)


# Create a global instance of the agent
_worksheet_agent = WorksheetAgent()


async def generate_worksheet_from_image(
    image_bytes: bytes,
    grade: int,
    filename: str = "image.png",
    subject: str = None,
    topic: str = None,
    description: str = None,
) -> WorksheetOutput:
    """Generate a worksheet from image bytes with structured parameters."""
    return await _worksheet_agent.generate(
        image_bytes=image_bytes,
        grade=grade,
        image_filename=filename,
        subject=subject,
        topic=topic,
        description=description,
    )
