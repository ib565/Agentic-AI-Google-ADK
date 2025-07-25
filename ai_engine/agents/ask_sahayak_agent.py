import logging
from typing import Optional
import uuid
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from google.cloud import translate_v2 as translate
from dotenv import load_dotenv

from ..models import AskSahayakOutput

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Initialize translation client
translate_client = translate.Client()


def detect_language(text: str) -> Optional[str]:
    """Detect the language code of the input text using Google Translate API."""
    try:
        result = translate_client.detect_language(text)
        return result.get("language")
    except Exception as e:
        logger.error(f"Language detection failed: {e}")
        return None


class AskSahayakAgent:
    """Simplified agent for multilingual conversational assistance with session management."""

    def __init__(self):
        self.agent = Agent(
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
        self.session_service = InMemorySessionService()
        self.app_name = "ask_sahayak_app"

    async def setup_session(self, user_id: str, session_id: Optional[str] = None):
        """Setup session - create new if no session_id provided, else fetch existing."""
        if session_id is None:
            # Create new session with new ID
            session_id = str(uuid.uuid4())
            session = await self.session_service.create_session(
                app_name=self.app_name,
                user_id=user_id,
                session_id=session_id,
            )
            logger.info(f"Created new session: {session_id}")
        else:
            # Fetch existing session
            session = await self.session_service.get_session(
                app_name=self.app_name, user_id=user_id, session_id=session_id
            )
            if session is None:
                raise Exception(f"Session {session_id} not found for user {user_id}")
            logger.info(f"Retrieved existing session: {session_id}")

        return session

    def create_message_content(self, question: str) -> types.Content:
        """Create message content with optional language instruction."""
        lang_code = detect_language(question)

        if lang_code and lang_code != "en":
            try:
                from langcodes import Language

                lang_name = (
                    Language.make(language=lang_code).language_name().capitalize()
                )
                message = f"Answer in the same language as the following question ({lang_name}).\n\n{question}"
            except:
                message = question
        else:
            message = question

        return types.Content(
            role="user",
            parts=[types.Part(text=message)],
        )

    async def run_agent(
        self, message_content: types.Content, user_id: str, session_id: str
    ) -> str:
        """Run the agent and extract text response."""
        runner = Runner(
            app_name=self.app_name,
            agent=self.agent,
            session_service=self.session_service,
        )

        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=message_content,
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            return part.text.strip()

        raise Exception("No valid response from agent")

    async def ask_question(
        self,
        question: str,
        user_id: str = "default_user",
        session_id: Optional[str] = None,
    ) -> AskSahayakOutput:
        """Main function to ask a question with session context."""
        try:
            # Setup session (create new if session_id is None, else fetch existing)
            session = await self.setup_session(user_id, session_id)

            # Create message content with language detection
            message_content = self.create_message_content(question)

            # Run agent and get response
            response = await self.run_agent(message_content, user_id, session.id)

            return AskSahayakOutput(response=response, session_id=session.id)

        except Exception as e:
            logger.error(f"Error processing question: {e}")
            raise


# Create global instance
_ask_sahayak_agent = AskSahayakAgent()


async def ask_sahayak_question(
    question: str, user_id: str = "default_user", session_id: Optional[str] = None
) -> AskSahayakOutput:
    """Convenience function to ask a question to Sahayak with session memory."""
    return await _ask_sahayak_agent.ask_question(question, user_id, session_id)
