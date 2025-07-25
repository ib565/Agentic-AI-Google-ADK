import json
import logging
from abc import ABC, abstractmethod
from typing import Any, TypeVar, Generic
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Generic type for output models
T = TypeVar("T")

# Configuration constants
DEFAULT_APP_NAME = "sahayak_app"
DEFAULT_USER_ID = "user_1"


class BaseAgent(ABC, Generic[T]):
    """Base class for all educational AI agents with common functionality."""

    def __init__(self, agent: Agent, app_name: str = None, session_id: str = None):
        self.agent = agent
        self.app_name = app_name or DEFAULT_APP_NAME
        self.session_id = session_id or f"{agent.name}_session_001"
        self.user_id = DEFAULT_USER_ID

    async def setup_session(self) -> tuple:
        """Set up session and required services."""
        try:
            session_service = InMemorySessionService()
            session = await session_service.create_session(
                app_name=self.app_name, user_id=self.user_id, session_id=self.session_id
            )
            logger.debug("Session setup completed successfully")
            return session_service, session
        except Exception as e:
            logger.error(f"Failed to setup session: {e}")
            raise

    @abstractmethod
    def create_message_content(self, **kwargs) -> types.Content:
        """Create properly formatted message content. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def parse_response_to_output(self, response_data: dict) -> T:
        """Parse agent response to output model. Must be implemented by subclasses."""
        pass

    async def run_agent(self, message_content: types.Content) -> T:
        """Run the agent and return the structured output."""
        logger.info(f"Running {self.agent.name}...")

        try:
            # Setup session and services
            session_service, session = await self.setup_session()

            # Create runner
            runner = Runner(
                app_name=self.app_name,
                agent=self.agent,
                session_service=session_service,
            )

            async for event in runner.run_async(
                user_id=self.user_id,
                session_id=self.session_id,
                new_message=message_content,
            ):
                if event.is_final_response():
                    if not event.content or not event.content.parts:
                        continue

                    for part in event.content.parts:
                        # Check if it's a function response (structured output)
                        if (
                            hasattr(part, "function_response")
                            and part.function_response
                        ):
                            try:
                                output = self.parse_response_to_output(
                                    part.function_response
                                )
                                logger.info(
                                    f"Successfully created output from {self.agent.name}"
                                )
                                return output
                            except Exception as e:
                                logger.error(f"Error parsing function_response: {e}")
                                continue

                        # Check if it's text content
                        elif hasattr(part, "text") and part.text:
                            text_content = part.text.strip()
                            try:
                                data = json.loads(text_content)
                                output = self.parse_response_to_output(data)
                                logger.info(
                                    f"Successfully created output from {self.agent.name}"
                                )
                                return output
                            except json.JSONDecodeError as e:
                                logger.error(f"JSON parsing error: {e}")
                            except Exception as e:
                                logger.error(f"Error creating output: {e}")

            raise Exception(f"Failed to extract data from {self.agent.name} response")

        except Exception as e:
            logger.error(f"Error running {self.agent.name}: {e}")
            raise

    async def generate(self, **kwargs) -> T:
        """Generate output using the agent. Must be implemented by subclasses."""
        try:
            logger.info(f"Generating output with {self.agent.name}")

            # Create message content
            message_content = self.create_message_content(**kwargs)

            # Run agent to generate output
            output = await self.run_agent(message_content)

            logger.info(f"Successfully generated output with {self.agent.name}")
            return output

        except Exception as e:
            logger.error(f"Error generating output with {self.agent.name}: {e}")
            raise
