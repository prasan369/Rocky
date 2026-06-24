import os
import json
import glob
import subprocess
import webbrowser
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.tools import DuckDuckGoSearchRun
from langgraph.prebuilt import create_react_agent
from langchain.tools import tool
from rapidfuzz import process, fuzz
from gmail_tool import read_emails, send_email,send_job_application
from camera_tool import look_and_describe, read_text_from_camera

load_dotenv()

MEMORY_FILE = "rocky_memory.json"
NOTES_FILE = "rocky_notes.txt"

# LLM
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=os.getenv("GROQ_API_KEY")
)

# Tools
search_tool = DuckDuckGoSearchRun()

@tool
def open_url(url: str) -> str:
    """Opens a URL in the default web browser. Use this when the user wants to open a website."""
    webbrowser.open(url)
    return f"Opened {url} in browser. Do not call this tool again."

def get_all_start_menu_apps() -> dict[str, str]:
    """Scan Start Menu and return {app_name: full_path} dict."""
    start_menu_dirs = [
        os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
        os.path.expandvars(r"%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs"),
    ]

    apps = {}
    for directory in start_menu_dirs:
        for ext in ["*.lnk", "*.exe"]:
            pattern = os.path.join(directory, "**", ext)
            matches = glob.glob(pattern, recursive=True)
            for match in matches:
                name = Path(match).stem.lower()
                apps[name] = match

    return apps

def find_best_app_match(app_name: str, apps: dict[str, str]) -> tuple[str, str] | None:
    """Use fuzzy matching to find the best app match."""
    if not apps:
        return None

    result = process.extractOne(
        app_name.lower(),
        apps.keys(),
        scorer=fuzz.WRatio,
        score_cutoff=60
    )

    if result:
        matched_name, score, _ = result
        return matched_name, apps[matched_name]

    return None

@tool
def open_application(app_name: str) -> str:
    """Opens an application on Windows by searching the Start Menu with fuzzy matching.
    Use this when the user wants to open any program or app.
    Only call this tool ONCE per request."""

    apps = get_all_start_menu_apps()
    match = find_best_app_match(app_name, apps)

    if match:
        matched_name, path = match
        subprocess.Popen(f'"{path}"', shell=True)
        return f"Successfully opened {matched_name}. Do not call this tool again."
    else:
        try:
            subprocess.Popen(app_name, shell=True)
            return f"Successfully opened {app_name}. Do not call this tool again."
        except Exception as e:
            return f"Could not find '{app_name}' on your system."

@tool
def save_note(note: str) -> str:
    """Saves a note to a local file. Use this when the user wants to remember something or save a note."""
    with open(NOTES_FILE, "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        f.write(f"[{timestamp}] {note}\n")
    return "Note saved. Do not call this tool again."

@tool
def read_notes(query: str = "") -> str:
    """Reads saved notes. Use this when the user wants to see their notes."""
    if not os.path.exists(NOTES_FILE):
        return "No notes saved yet."
    with open(NOTES_FILE, "r", encoding="utf-8") as f:
        notes = f.read().strip()
    if not notes:
        return "No notes saved yet."
    return f"Here are your notes:\n{notes}"

@tool
def clear_notes(confirm: str) -> str:
    """Clears all saved notes. Only call this if the user explicitly asks to clear or delete all their notes."""
    if os.path.exists(NOTES_FILE):
        open(NOTES_FILE, "w").close()
    return "All notes cleared. Do not call this tool again."

tools = [search_tool, open_url, open_application, save_note, read_notes, clear_notes, read_emails, send_email, send_job_application, look_and_describe, read_text_from_camera]

# Agent
agent = create_react_agent(llm, tools)


def load_memory() -> str:
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            data = json.load(f)
            return data.get("summary", "")
    return ""


def save_memory(summary: str):
    with open(MEMORY_FILE, "w") as f:
        json.dump({"summary": summary}, f, indent=2)


def summarize_conversation(conversation_history: list) -> str:
    if not conversation_history:
        return ""

    history_text = "\n".join(
        f"{msg['role'].upper()}: {msg['content']}"
        for msg in conversation_history
    )

    prompt = f"""You are summarizing a conversation for long-term memory of a personal AI assistant named Rocky.
Extract and preserve:
- Important facts about the user
- Tasks that were completed
- Preferences the user mentioned
- Anything useful to remember for future conversations

Previous summary (if any):
{load_memory()}

New conversation:
{history_text}

Write a concise updated summary:"""

    result = llm.invoke(prompt)
    return result.content


def get_initial_messages(past_summary: str) -> list:
    system_prompt = """You are Rocky, a personal AI assistant running inside a desktop chat window.
Important rules:
- When you use a tool and it returns success, do NOT call it again. One tool call per task is enough.
- After opening an app or URL, just confirm to the user that it's done.
- For saving notes, extract the actual note content from what the user said and save just that.
- When reading notes, display them clearly to the user.
- NEVER call send_email more than once per request. One call is enough. If it returns success, stop immediately.
- When sending emails, avoid using apostrophes or special characters in subject and body fields.
- When the user wants to apply for a job or send their CV, use send_job_application not send_email.
- NEVER use markdown formatting. No tables, no **bold**, no # headers, no bullet points with *.
- Format all responses as plain text only. Use simple dashes or numbers for lists.
- Keep responses concise and clean.
- When the user says "look", "can you see", "what do you see", "read this", "what is this", ALWAYS use the look_and_describe tool. Never say you cannot see.
"""
    if past_summary:
        system_prompt += f"\nHere is what you remember from past conversations with the user:\n{past_summary}"

    return [{"role": "system", "content": system_prompt}]


def ask_rocky(user_input: str, conversation_history: list) -> tuple[str, list]:
    conversation_history.append({"role": "user", "content": user_input})

    result = agent.invoke(
        {"messages": conversation_history},
        config={"recursion_limit": 5}
    )

    response = result["messages"][-1].content
    conversation_history.append({"role": "assistant", "content": response})

    return response, conversation_history


def end_session(conversation_history: list):
    """Call this when the popup is closed to save memory."""
    if conversation_history:
        summary = summarize_conversation(conversation_history)
        save_memory(summary)