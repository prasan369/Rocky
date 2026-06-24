import time
import re
from groq import Groq, RateLimitError
from dotenv import load_dotenv

load_dotenv()

client = Groq()

try:
    # Your API call here
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "Hello"}]
    )
except RateLimitError as e:
    # Use regex to find the time remaining in the error string
    match = re.search(r"try again in ([\w\.]+)", str(e))
    if match:
        remaining_time = match.group(1)
        print(f"Time remaining: {remaining_time}")