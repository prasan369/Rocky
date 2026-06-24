import os
import base64
import email as email_lib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from langchain.tools import tool

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send"
]

CV_PATH = r"C:\Users\Acer\Desktop_Local\CV.docx"

def get_gmail_service():
    """Authenticate and return Gmail service."""
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


@tool
def read_emails(max_emails: int = 5) -> str:
    """Reads the latest emails from Gmail inbox. Use this when the user wants to check their email or inbox."""
    try:
        service = get_gmail_service()
        results = service.users().messages().list(
            userId="me",
            labelIds=["INBOX"],
            maxResults=max_emails
        ).execute()

        messages = results.get("messages", [])
        if not messages:
            return "No emails found in inbox."

        emails = []
        for msg in messages:
            msg_data = service.users().messages().get(
                userId="me",
                id=msg["id"],
                format="full"
            ).execute()

            headers = msg_data["payload"]["headers"]
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
            sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
            date = next((h["value"] for h in headers if h["name"] == "Date"), "Unknown")

            body = ""
            payload = msg_data["payload"]
            if "parts" in payload:
                for part in payload["parts"]:
                    if part["mimeType"] == "text/plain":
                        data = part["body"].get("data", "")
                        if data:
                            body = base64.urlsafe_b64decode(data).decode("utf-8")[:300]
                            break
            elif "body" in payload:
                data = payload["body"].get("data", "")
                if data:
                    body = base64.urlsafe_b64decode(data).decode("utf-8")[:300]

            emails.append(f"From: {sender}\nDate: {date}\nSubject: {subject}\nPreview: {body}\n{'-'*40}")

        return "\n".join(emails)

    except Exception as e:
        return f"Error reading emails: {str(e)}"


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Sends an email via Gmail.
    IMPORTANT: Only call this tool ONCE per request. Never call it more than once.
    After calling this tool, immediately return the result to the user."""
    try:
        service = get_gmail_service()

        subject = subject.replace("\\'", "'").replace('\\"', '"')
        body = body.replace("\\'", "'").replace('\\"', '"')

        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        service.users().messages().send(
            userId="me",
            body={"raw": raw}
        ).execute()

        return f"Email sent to {to} with subject '{subject}'. Do not call this tool again."

    except Exception as e:
        return f"Error sending email: {str(e)}"


@tool
def send_job_application(to: str, subject: str, body: str) -> str:
    """Sends a job application email with CV attached. Use this when the user wants to apply for a job or send their CV.
    IMPORTANT: Only call this tool ONCE per request. Never call it more than once."""
    try:
        service = get_gmail_service()

        subject = subject.replace("\\'", "'").replace('\\"', '"')
        body = body.replace("\\'", "'").replace('\\"', '"')

        message = MIMEMultipart()
        message["to"] = to
        message["subject"] = subject
        message.attach(MIMEText(body, "plain"))

        if os.path.exists(CV_PATH):
            with open(CV_PATH, "rb") as f:
                attachment = MIMEBase("application", "octet-stream")
                attachment.set_payload(f.read())
                encoders.encode_base64(attachment)
                attachment.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename="Prasan_Thapa_CV.docx"
                )
                message.attach(attachment)
        else:
            return f"CV not found at {CV_PATH}. Please check the path."

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        service.users().messages().send(
            userId="me",
            body={"raw": raw}
        ).execute()

        return f"Job application sent to {to} with CV attached. Do not call this tool again."

    except Exception as e:
        return f"Error sending application: {str(e)}"