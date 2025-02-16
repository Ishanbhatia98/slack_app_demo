import os
import threading

import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import FastAPI
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from app.model.message import Message

from .database import Base, SessionLocal, engine

env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

Base.metadata.create_all(engine)


SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)


app = FastAPI(description="Slack Bot Demo")


@app.get("/demo/health")
def health_check():
    return {"message": "Slack Bot is running with Socket Mode and FastAPI"}


slack_app = App(token=SLACK_BOT_TOKEN)


@slack_app.event("app_mention")
def handle_mention(body, say):
    event = body["event"]
    channel = event["channel"]
    thread_ts = event.get("thread_ts", event["ts"])
    user_message = event["text"]
    user = event["user"]
    timestamp = event["ts"]

    session = SessionLocal()
    new_message = Message(
        channel=channel, user=user, text=user_message, timestamp=timestamp
    )
    session.add(new_message)
    session.commit()

    messages = (
        session.query(Message)
        .filter_by(channel=channel)
        .order_by(Message.id.desc())
        .limit(5)
        .all()
    )
    session.close()

    conversation = "\n".join([f"{msg.user}: {msg.text}" for msg in reversed(messages)])
    prompt = (
        "You are an AI assistant in a Slack workspace, helping users by answering their questions and engaging in meaningful conversations.\n"
        "Respond concisely, accurately, and professionally while maintaining a friendly tone.\n"
        "Use the given conversation history to understand the context before responding.\n\n"
        f"Conversation history:\n{conversation}\n\n"
        f"User ({user}) asked: {user_message}\n"
        "Bot:"
    )

    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        print(response.text)
        bot_reply = (
            response.text if response.text else "I couldn't generate a response."
        )

    except Exception as e:
        print(f"Error calling Google Gemini API: {e}")
        bot_reply = "Sorry, I encountered an error while processing your request."
    say(text=bot_reply, channel=channel, thread_ts=thread_ts)


def start_socket_mode():
    handler = SocketModeHandler(slack_app, SLACK_APP_TOKEN)
    handler.start()


slack_thread = threading.Thread(target=start_socket_mode, daemon=True)
slack_thread.start()
