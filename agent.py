import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.tools import DuckDuckGoSearchRun
from langgraph.prebuilt import create_react_agent

load_dotenv()

MEMORY_FILE = "rocky_memory.json"

# LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

# Tools
search_tool = DuckDuckGoSearchRun()
tools = [search_tool]

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
    if not past_summary:
        return []
    
    return [{
        "role": "system",
        "content": f"You are Rocky, a personal AI assistant. Here is what you remember from past conversations with the user:\n{past_summary}"
    }]


def ask_rocky(user_input: str, conversation_history: list) -> tuple[str, list]:
    conversation_history.append({"role": "user", "content": user_input})

    result = agent.invoke({"messages": conversation_history})

    response = result["messages"][-1].content
    conversation_history.append({"role": "assistant", "content": response})

    return response, conversation_history


def end_session(conversation_history: list):
    """Call this when the popup is closed to save memory."""
    if conversation_history:
        summary = summarize_conversation(conversation_history)
        save_memory(summary)