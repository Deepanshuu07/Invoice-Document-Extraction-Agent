import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel
from enum import Enum
from google.genai.errors import ClientError

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


class DocumentType(str, Enum):
    invoice = "invoice"
    receipt = "receipt"
    purchase_order = "purchase_order"
    other = "other"


class Classification(BaseModel):
    document_type: DocumentType
    confidence: float
    reasoning: str


def classify_document(pdf_bytes: bytes) -> Classification | None:
    """Looks at a PDF and decides what kind of document it is.
    Returns None if classification fails (e.g. rate limit, API error)."""

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=[
                types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
                "Classify this document. Choose the closest matching type. "
                "Give a confidence score between 0 and 1, and a one-sentence reason for your choice.",
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=Classification,
            ),
        )
    except ClientError as e:
        return None

    return Classification.model_validate_json(response.text)