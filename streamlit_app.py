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
        st.error("🛑 Daily API Limit Reached! Switch models or upgrade your plan in AI Studio to continue testing.")
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
        
    if isinstance(result, ExtractionError):
        st.error(f"❌ Extraction failed: {result.error_message}")
    else:
        invoice = result.invoice

        if result.is_valid:
            st.success("✅ Extraction validated — numbers reconcile.")
        else:
            st.warning(f"⚠️ Validation mismatch of {result.difference} — please review manually.")

        st.subheader("Invoice Summary")
        col1, col2 = st.columns(2)
        col1.metric("Vendor", invoice.vendor_name)
        col2.metric("Total Amount", f"₹{invoice.total_amount:,.2f}")

        st.write(f"**Invoice Number:** {invoice.invoice_number}")
        st.write(f"**Invoice Date:** {invoice.invoice_date}")

        st.subheader("Line Items")
        line_items_data = [
            {
                "Description": item.description,
                "Quantity": item.quantity,
                "Unit Price": item.unit_price,
            }
            for item in invoice.line_items
        ]
        st.table(line_items_data)

        st.subheader("Charges Breakdown")
        st.write(f"Subtotal: ₹{invoice.subtotal:,.2f}")
        st.write(f"Discount: −₹{invoice.discount:,.2f}")
        st.write(f"Tax: ₹{invoice.tax:,.2f}")
        st.write(f"Shipping: ₹{invoice.shipping:,.2f}")

        # Build a DataFrame for export
        df_line_items = pd.DataFrame(line_items_data)

        st.subheader("Export")
        col1, col2 = st.columns(2)

        csv_data = df_line_items.to_csv(index=False)
        col1.download_button(
            label="Download Line Items as CSV",
            data=csv_data,
            file_name=f"{invoice.invoice_number}_line_items.csv",
            mime="text/csv",
        )

        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            df_line_items.to_excel(writer, sheet_name="Line Items", index=False)
            df_summary = pd.DataFrame([{
                "Vendor": invoice.vendor_name,
                "Invoice Number": invoice.invoice_number,
                "Invoice Date": invoice.invoice_date,
                "Subtotal": invoice.subtotal,
                "Discount": invoice.discount,
                "Tax": invoice.tax,
                "Shipping": invoice.shipping,
                "Total": invoice.total_amount,
            }])
            df_summary.to_excel(writer, sheet_name="Summary", index=False)

        col2.download_button(
            label="Download Full Report as Excel",
            data=excel_buffer.getvalue(),
            file_name=f"{invoice.invoice_number}_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )