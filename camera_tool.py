import os
import cv2
import base64
import tempfile
from langchain.tools import tool
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

vision_llm = ChatGroq(
    model="qwen/qwen3.6-27b",
    api_key=os.getenv("GROQ_API_KEY")
)

def capture_frame() -> str:
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        raise Exception("Could not access webcam.")
    
    for _ in range(15):
        cap.read()
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        raise Exception("Failed to capture frame.")
    
    temp_path = tempfile.mktemp(suffix=".jpg")
    cv2.imwrite(temp_path, frame)
    return temp_path

def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

@tool
def look_and_describe(question: str = "What do you see?") -> str:
    """Uses the webcam to capture an image and answers a question about what it sees.
    Use this when the user says look, can you see, what do you see, or anything about the camera.
    Only call this tool ONCE per request."""
    try:
        image_path = capture_frame()
        image_data = encode_image(image_path)
        os.remove(image_path)

        message = HumanMessage(content=[
            {"type": "text", "text": f"You are Rocky, a personal AI assistant with vision. Answer this: {question}. Be concise and direct."},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
        ])

        response = vision_llm.invoke([message])
        print("VISION RESPONSE:", response.content)
        return response.content

    except Exception as e:
        print("CAMERA ERROR:", str(e))
        return f"Camera error: {str(e)}"

@tool
def read_text_from_camera(query: str = "") -> str:
    """Uses the webcam to read and extract text from whatever is in front of the camera.
    Use this when the user wants Rocky to read a document, book, whiteboard, or any text.
    Only call this tool ONCE per request."""
    try:
        image_path = capture_frame()
        image_data = encode_image(image_path)
        os.remove(image_path)

        message = HumanMessage(content=[
            {"type": "text", "text": "Extract and transcribe ALL text visible in this image accurately. If no text, describe what you see."},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
        ])

        response = vision_llm.invoke([message])
        print("VISION RESPONSE:", response.content)
        return response.content

    except Exception as e:
        print("CAMERA ERROR:", str(e))
        return f"Camera error: {str(e)}"