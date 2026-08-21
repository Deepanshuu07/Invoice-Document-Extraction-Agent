from invoice_extractor import extract_invoice

with open("sample_invoice.pdf", "rb") as f:
    pdf_bytes = f.read()

result = extract_invoice(pdf_bytes)

print(result.invoice.vendor_name)
print(result.invoice.total_amount)
print(f"Valid: {result.is_valid}, difference: {result.difference}")