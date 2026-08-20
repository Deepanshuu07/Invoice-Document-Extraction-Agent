import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


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


class ExtractionResult(BaseModel):
    invoice: Invoice
    calculated_total: float
    difference: float
    is_valid: bool


class ExtractionError(BaseModel):
    success: bool = False
    error_message: str

def extract_invoice(pdf_bytes: bytes) -> ExtractionResult | ExtractionError:
    """Takes raw PDF bytes, returns a validated invoice + reconciliation check,
    or an ExtractionError if anything goes wrong."""

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=[
                types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
                "Extract the invoice details, including subtotal, any discount, "
                "tax, and shipping charges. If a value is not present on the "
                "invoice, use 0. If this document is not an invoice, respond "
                "with all fields empty or zero.",
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=Invoice,
            ),
        )
    except Exception as e:
        return ExtractionError(error_message=f"API call failed: {e}")

    try:
        invoice = Invoice.model_validate_json(response.text)
    except Exception as e:
        return ExtractionError(error_message=f"Could not parse a valid invoice from this document: {e}")

    if not invoice.vendor_name or not invoice.invoice_number:
        return ExtractionError(error_message="This doesn't look like a valid invoice — missing vendor or invoice number.")

    calculated_total = invoice.subtotal - invoice.discount + invoice.tax + invoice.shipping
    difference = round(calculated_total - invoice.total_amount, 2)
    is_valid = abs(difference) < 0.01

    return ExtractionResult(
        invoice=invoice,
        calculated_total=calculated_total,
        difference=difference,
        is_valid=is_valid,
    )