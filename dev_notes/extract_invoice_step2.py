import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Define the exact structure we want back
class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float

class Invoice(BaseModel):
    vendor_name: str
    invoice_number: str
    invoice_date: str
    line_items: list[LineItem]
    subtotal: float
    discount: float
    tax: float
    shipping: float
    total_amount: float

with open("sample_invoice.pdf", "rb") as f:
    pdf_bytes = f.read()

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=[
        types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
        "Extract the invoice details, including subtotal, any discount, tax, and shipping charges. If a value is not present on the invoice, use 0."
    ],
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=Invoice,
    ),
)

invoice = Invoice.model_validate_json(response.text)
print(invoice.vendor_name)
print(invoice.total_amount)
print("Line items:")
for item in invoice.line_items:
    print(f"  - {item.description}: {item.quantity} x {item.unit_price}")


# Validation: does the math actually add up?
calculated_total = invoice.subtotal - invoice.discount + invoice.tax + invoice.shipping
difference = round(calculated_total - invoice.total_amount, 2)

print(f"\nSubtotal: {invoice.subtotal}")
print(f"Discount: {invoice.discount}")
print(f"Tax: {invoice.tax}")
print(f"Shipping: {invoice.shipping}")
print(f"Reported total: {invoice.total_amount}")
print(f"Calculated total: {calculated_total}")

if abs(difference) < 0.01:
    print("✅ Validation passed — numbers reconcile.")
else:
    print(f"⚠️ Validation FAILED — mismatch of {difference}. Needs manual review.")