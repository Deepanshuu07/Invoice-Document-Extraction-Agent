import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Read the PDF file as raw bytes
with open("sample_invoice.pdf", "rb") as f:
    pdf_bytes = f.read()

# Send the PDF + a prompt together
response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=[
        types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
        "List the vendor name, invoice number, invoice date, and total amount from this invoice."
    ]
)

print(response.text)