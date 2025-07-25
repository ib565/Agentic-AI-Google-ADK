import logging
from google.adk.agents import Agent
from google.genai import types

from .base_agent import BaseAgent
from ..models import StudyMaterialOutput

# Configure logging
logger = logging.getLogger(__name__)


class StudyMaterialAgent(BaseAgent[StudyMaterialOutput]):
    """Agent for creating detailed educational study materials."""

    def __init__(self):
        # Agent configuration
        agent = Agent(
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

        super().__init__(agent, app_name="learning_material_app")

    def create_message_content(
        self, subject: str, grade: int, topic: str = None, description: str = None
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

    def parse_response_to_output(self, response_data: dict) -> StudyMaterialOutput:
        """Parse agent response to StudyMaterialOutput."""
        return StudyMaterialOutput(**response_data)


# Create a global instance of the agent
_study_material_agent = StudyMaterialAgent()


async def generate_study_material(
    subject: str, grade: int, topic: str = None, description: str = None
) -> StudyMaterialOutput:
    """Generate study materials from structured parameters."""
    return await _study_material_agent.generate(
        subject=subject, grade=grade, topic=topic, description=description
    )
