import os
import asyncio
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

from dotenv import load_dotenv

load_dotenv()


worksheet_agent = Agent(
    name="worksheet_agent",
    model="gemini-2.0-flash",
    description=("Agent to help a teacher create a worksheet, based on given content."),
    instruction="You are a helpful worksheet assistant. "
    "You will be given an image of a textbook page, and you will need to create a worksheet based on the content of the page."
    "You will need to create a worksheet that is 10 questions long, and each question will be a multiple choice question.",
)

session_service = InMemorySessionService()

APP_NAME = "worksheet_tutorial_app"
USER_ID = "user_1"
SESSION_ID = "session_001"

runner = Runner(
    app_name=APP_NAME,
    agent=worksheet_agent,
    session_service=session_service,
)


async def main():
    # Create session inside async function so we can await it
    session = await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )

    print(f"Session: {session}")

    # load textbook.png into bytes
    with open("textbook.png", "rb") as f:
        bytes_data = f.read()

    # Create properly formatted message content
    message_content = types.Content(
        role="user",
        parts=[
            types.Part(
                inline_data=types.Blob(
                    data=bytes_data, mime_type="image/png", display_name="textbook.png"
                )
            )
        ],
    )

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=message_content,
    ):

        if event.is_final_response() and event.content and event.content.parts:
            # For output_schema, the content is the JSON string itself
            final_response_content = event.content.parts[0].text

    print(f"Final response: {final_response_content}")


asyncio.run(main())
