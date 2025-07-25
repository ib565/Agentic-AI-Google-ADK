import logging
from typing import Optional, Dict, Any, Tuple
import uuid
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from google.cloud import translate_v2 as translate
from langcodes import Language
from dotenv import load_dotenv

from ..models import AskSahayakOutput

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Configuration constants
APP_NAME = "ask_sahayak_app"

# Initialize translation client
translate_client = translate.Client()


def detect_language(text: str) -> Optional[str]:
    """Detect the language code of the input text using Google Translate API.

    Args:
        text: The input text to detect language for

    Returns:
        Language code string if successful, None if detection fails
    """
    try:
        result = translate_client.detect_language(text)
        # Log only the detected language, not the potentially sensitive text
        logger.info(f"Detected language: {result.get('language', 'unknown')}")
        return result.get("language")

    except Exception as e:
        logger.error(f"Language detection failed: {e}")
        return None


def get_language_name(lang_code: Optional[str]) -> Optional[str]:
    """Convert language code to full language name (e.g., 'hi' → 'Hindi').

    Args:
        lang_code: ISO language code or None

    Returns:
        Full language name if successful, None if conversion fails or input is None
    """
    if lang_code is None:
        return None
    try:
        return Language.make(language=lang_code).language_name().capitalize()
    except (ValueError, AttributeError, LookupError) as e:
        logger.warning(f"Failed to convert language code '{lang_code}' to name: {e}")
        return None


ask_sahayak_agent = Agent(
    name="ask_sahayak_agent",
    model="gemini-2.0-flash",
    description=(
        "A multilingual conversational assistant that maintains context across conversations. "
        "Provides helpful explanations using analogies in the same language as the input."
    ),
    instruction=(
        "You are an expert teaching assistant and helpful conversational AI. "
        "Always respond in the same language and style as the user's question. "
        "Break down complex topics using analogies and simple explanations. "
        "Be helpful, encouraging, and educational in your responses. "
        "Keep your responses conversational and engaging. "
        "Use simple explanations, real-world analogies, and maintain a helpful tone."
    ),
)


class AskSahayakService:
    """Service class to manage Ask Sahayak conversations with session memory."""

    def __init__(self):
        self.session_service = InMemorySessionService()
        self.active_sessions: Dict[str, str] = {}  # session_id -> user_id

    async def setup_session(
        self, user_id: str, session_id: Optional[str] = None
    ) -> Tuple[InMemorySessionService, Any]:
        """Set up session and required services.

        Args:
            user_id: User identifier
            session_id: Optional existing session ID, creates new if None

        Returns:
            Tuple of (session_service, session)

        Raises:
            Exception: If session creation or retrieval fails
        """
        try:
            if session_id is None:
                # Generate new session if no ID provided
                session_id = str(uuid.uuid4())
                session = await self.session_service.create_session(
                    app_name=APP_NAME,
                    user_id=user_id,
                    session_id=session_id,
                )
                logger.info(f"Created new session for user {user_id}: {session_id}")
            else:
                # Return existing session if ID provided
                try:
                    session = await self.session_service.get_session(
                        app_name=APP_NAME, user_id=user_id, session_id=session_id
                    )
                    logger.info(
                        f"Retrieved existing session for user {user_id}: {session_id}"
                    )
                except Exception as e:
                    logger.error(
                        f"Could not retrieve session {session_id} for user {user_id}: {e}"
                    )
                    raise Exception(
                        f"Session {session_id} not found for user {user_id}"
                    ) from e

            if session is None:
                logger.error(
                    f"Failed to create or retrieve session {session_id} for user {user_id}"
                )
                raise Exception("Session creation/retrieval returned None")

            self.active_sessions[session_id] = user_id
            return self.session_service, session

        except Exception as e:
            logger.error(f"Failed to setup session for user {user_id}: {e}")
            raise

    def create_message_content(
        self, question: str, lang_name: Optional[str]
    ) -> types.Content:
        """Create properly formatted message content for Ask Sahayak agent.

        Args:
            question: User's question text
            lang_name: Full language name for context, if detected

        Returns:
            Formatted Content object for the agent
        """
        if lang_name:
            lang_instruction = (
                f"Answer in the same language as the following question ({lang_name})."
            )
            message_content = f"{lang_instruction}\n\n{question}"
            logger.debug(f"Added language instruction for: {lang_name}")
        else:
            message_content = question
            logger.debug("No language instruction added (language not detected)")

        return types.Content(
            role="user",
            parts=[
                types.Part(text=message_content),
            ],
        )

    async def run_ask_sahayak_agent(
        self, runner: Runner, message_content: types.Content, session_id: str
    ) -> AskSahayakOutput:
        """Run the ask sahayak agent and return the response.

        Args:
            runner: Configured Runner instance
            message_content: Formatted message content
            session_id: Active session ID

        Returns:
            AskSahayakOutput with response and session info

        Raises:
            Exception: If agent execution or response extraction fails
        """
        logger.info(f"Running ask sahayak agent for session: {session_id}")

        try:
            user_id = self.active_sessions.get(session_id, "default_user")

            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=message_content,
            ):
                if event.is_final_response():
                    if not event.content or not event.content.parts:
                        logger.warning(
                            f"Empty response content from agent for session: {session_id}"
                        )
                        continue

                    for part in event.content.parts:
                        # Check if it's text content
                        if hasattr(part, "text") and part.text:
                            response_text = part.text.strip()

                            if not response_text:
                                logger.warning(
                                    f"Empty response text from agent for session: {session_id}"
                                )
                                continue

                            result = AskSahayakOutput(
                                response=response_text,
                                session_id=session_id,
                            )

                            logger.info(
                                f"Successfully generated response for session: {session_id}"
                            )
                            return result

            logger.error(
                f"No valid response generated from agent for session: {session_id}"
            )
            raise Exception("Failed to extract valid response from agent")

        except Exception as e:
            logger.error(
                f"Error running ask sahayak agent for session {session_id}: {e}"
            )
            raise

    async def ask_question(
        self,
        question: str,
        user_id: str = "default_user",
        session_id: Optional[str] = None,
    ) -> AskSahayakOutput:
        """Main function to ask a question and get a response with conversation context.

        Args:
            question: User's question text
            user_id: User identifier (defaults to "default_user")
            session_id: Optional session ID for conversation continuity

        Returns:
            AskSahayakOutput with response and session info

        Raises:
            Exception: If question processing fails at any stage
        """
        try:
            logger.info(
                f"Processing question for user {user_id}, session: {session_id or 'new'}"
            )

            # Setup session and services
            session_service, session = await self.setup_session(user_id, session_id)

            if session is None:
                logger.error("Session setup returned None")
                raise Exception("Failed to create or retrieve session")

            # Create runner
            runner = Runner(
                app_name=APP_NAME,
                agent=ask_sahayak_agent,
                session_service=session_service,
            )

            # Detect language of the question with fallback handling
            lang_code = detect_language(question)
            lang_name = get_language_name(lang_code) if lang_code else None

            if lang_code is None:
                logger.info(
                    "Language detection failed, proceeding without language context"
                )
            else:
                logger.debug(f"Language detected: {lang_code} ({lang_name})")

            # Create message content - session system handles context automatically
            message_content = self.create_message_content(question, lang_name)

            # Run agent to get response
            result = await self.run_ask_sahayak_agent(
                runner, message_content, session.id
            )

            logger.info(f"Successfully processed question for session: {session.id}")
            return result

        except Exception as e:
            logger.error(f"Error processing question for user {user_id}: {e}")
            raise


# Create a global service instance
ask_sahayak_service = AskSahayakService()


# Convenience function for external use
async def ask_sahayak_question(
    question: str, user_id: str = "default_user", session_id: Optional[str] = None
) -> AskSahayakOutput:
    """Convenience function to ask a question to Sahayak with session memory.

    Args:
        question: User's question text
        user_id: User identifier (defaults to "default_user")
        session_id: Optional session ID for conversation continuity

    Returns:
        AskSahayakOutput with response and session info
    """
    return await ask_sahayak_service.ask_question(question, user_id, session_id)
