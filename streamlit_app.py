import streamlit as st
import pandas as pd
import io
from invoice_extractor import extract_invoice
from invoice_extractor import extract_invoice, ExtractionError
from classifier import classify_document, DocumentType

st.title("Invoice Extraction Agent")
st.write("Upload an invoice PDF to extract structured data.")

uploaded_file = st.file_uploader("Choose a PDF invoice", type="pdf")

if uploaded_file is not None:
    pdf_bytes = uploaded_file.read()

    with st.spinner("Classifying document..."):
        classification = classify_document(pdf_bytes)

    if classification is None:
        st.error("⚠️ Classification failed — likely a rate limit or API issue. Please wait a moment and try again.")
        st.stop()

    st.caption(
        f"Detected: **{classification.document_type.value}** "
        f"(confidence: {classification.confidence:.0%}) — {classification.reasoning}"
    )

    if classification.document_type != DocumentType.invoice:
        doc_type_label = classification.document_type.value.replace("_", " ")
        st.warning(
            f"This looks like a **{doc_type_label}**, not an invoice. "
            f"Extraction works best on invoices — proceeding anyway, but review the results carefully."
        )

    with st.spinner("Extracting invoice data..."):
        result = extract_invoice(pdf_bytes)