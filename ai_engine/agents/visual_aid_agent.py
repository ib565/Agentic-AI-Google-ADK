import logging
from google.adk.agents import Agent
from google.genai import types

from .base_agent import BaseAgent
from ..models import VisualAidOutput
from ..services import mermaid_service

# Configure logging
logger = logging.getLogger(__name__)


class VisualAidDesignerAgent(BaseAgent[VisualAidOutput]):
    """Agent for creating visual aids and diagrams from teacher descriptions."""

    def __init__(self):
        # Agent configuration
        agent = Agent(
            name="visual_aid_agent",
            model="gemini-2.5-flash",
            description=(
                "Agent to help teachers create visual aids and diagrams to help students understand the topic. "
                "Generates Mermaid syntax for educational diagrams based on teacher descriptions."
            ),
            instruction=(
                "You are a visual aid designer for teachers. Your job is to create simple, educational diagrams "
                "using Mermaid syntax that teachers can use to explain the topic to students.\n\n"
                "DIAGRAM TYPES TO USE:\n"
                "• FLOWCHART: For processes, cycles, step-by-step procedures (water cycle, scientific method)\n"
                "• MIND MAP: For concept relationships, categories, hierarchies (animal classification, government branches)\n"
                "• CLASS/ER DIAGRAM: For relationships, structures, comparisons\n"
                "DESIGN PRINCIPLES:\n"
                "• Keep it simple and educational\n"
                "• Focus only on essential elements that help students understand\n"
                "• Use clear, readable labels\n"
                "• Avoid complex styling or colors\n"
                "• DO NOT USE BRACKETS WITHIN LABELS\n"
                "OUTPUT FORMAT:\n"
                "Always respond with ONLY this JSON structure:\n"
                "{\n"
                '  "title": "Clear, descriptive title for the diagram",\n'
                '  "reasoning": "Explanation of the diagram"\n'
                '  "mermaid_syntax": "Complete Mermaid code without markdown code blocks"\n'
                "}\n\n"
                "Choose the diagram type that best fits the educational content and create Mermaid syntax "
                "that is simple, correct, and educational."
            ),
            output_schema=VisualAidOutput,
        )

        super().__init__(agent, app_name="visual_aid_designer_app")

    def create_message_content(
        self,
        subject: str,
        grade: int,
        topic: str,
        description: str = None,
    ) -> types.Content:
        """Create properly formatted message content with structured parameters."""

        prompt_text = (
            f"Create a visual aid diagram for:\n"
            f"Subject: {subject}\n"
            f"Grade Level: {grade}\n"
            f"Topic: {topic}\n"
        )

        if description:
            prompt_text += f"Description: {description}\n"

        prompt_text += (
            f"\nCreate an appropriate diagram for '{topic}' that grade {grade} students "
            f"can easily understand and that teachers can draw on a blackboard."
        )

        return types.Content(
            role="user",
            parts=[
                types.Part(text=prompt_text),
            ],
        )

    def parse_response_to_output(self, response_data: dict) -> VisualAidOutput:
        """Parse agent response to VisualAidOutput."""
        return VisualAidOutput(**response_data)

    def _determine_diagram_type(self, mermaid_syntax: str) -> str:
        """Determine diagram type from Mermaid syntax."""
        syntax_lower = mermaid_syntax.lower()

        if "mindmap" in syntax_lower:
            return "mind_map"
        elif "flowchart" in syntax_lower or "graph" in syntax_lower:
            return "flowchart"
        elif "classdiagram" in syntax_lower or "erdiagram" in syntax_lower:
            return "class_diagram"
        else:
            return "simple"

    async def generate(self, **kwargs) -> dict:
        """Generate visual aid with Mermaid syntax and render the diagram."""
        try:
            logger.info("Generating visual aid with Mermaid")

            # Extract input parameters
            subject = kwargs.get("subject", "")
            grade = kwargs.get("grade", "")
            topic = kwargs.get("topic", "")
            description = kwargs.get("description", "")

            # Create message content
            message_content = self.create_message_content(**kwargs)

            # Try generating and rendering (with one retry if render fails)
            max_attempts = 2
            output = None
            diagram_url = None

            for attempt in range(max_attempts):
                try:
                    # Run agent to generate Mermaid syntax
                    output = await self.run_agent(message_content)

                    logger.info(
                        f"Successfully generated Mermaid syntax (attempt {attempt + 1})"
                    )

                    # Generate and upload the diagram
                    diagram_url = mermaid_service.create_and_upload_diagram(
                        mermaid_syntax=output.mermaid_syntax,
                        title=output.title,
                        subject=subject,
                    )

                    if diagram_url:
                        # Success! Break out of retry loop
                        logger.info(
                            f"Successfully rendered diagram on attempt {attempt + 1}"
                        )
                        break
                    else:
                        # Rendering failed
                        if attempt < max_attempts - 1:
                            logger.warning(
                                f"Failed to render diagram on attempt {attempt + 1}, retrying LLM call..."
                            )
                        else:
                            logger.error(
                                f"Failed to render diagram after {max_attempts} attempts, returning output with Mermaid syntax only"
                            )

                except Exception as e:
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Error on attempt {attempt + 1}: {e}, retrying..."
                        )
                    else:
                        logger.error(f"Error on final attempt {attempt + 1}: {e}")
                        raise

            # Build complete response with programmatically determined fields
            result = {
                "title": output.title,
                "description": description or f"Visual aid for {topic}",
                "mermaid_syntax": output.mermaid_syntax,
                "diagram_url": diagram_url or "",
                "diagram_type": self._determine_diagram_type(output.mermaid_syntax),
                "grade_level": str(grade),
                "subject": subject,
            }

            logger.info(f"Successfully created visual aid: {result['title']}")
            return result

        except Exception as e:
            logger.error(f"Error generating visual aid: {e}")
            raise


# Create a global instance of the agent
_visual_aid_agent = VisualAidDesignerAgent()


async def generate_visual_aid(
    subject: str,
    grade: int,
    topic: str,
    description: str = None,
) -> dict:
    """Generate a visual aid from teacher topic and optional description."""
    return await _visual_aid_agent.generate(
        subject=subject,
        grade=grade,
        topic=topic,
        description=description,
    )
