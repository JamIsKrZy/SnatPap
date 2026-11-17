import json
import os
import re
from datetime import datetime
from django.utils import timezone


class BlackBoxProcessor:
    """
    Interface for the external text-to-structured-data conversion system.
    In production, this module coordinates with the external worker/model that
    converts OCR text into formatted JSON and SQL data.
    """

    @classmethod
    def process_document(cls, document, mode='immediate'):
        """
        Process the document.
        - If mode == 'pending': Mark as pending external processing.
        - If mode == 'immediate': Run the black-box conversion simulator to produce
          realistic OCR text, formatted JSON schema, and executable SQL.
        """
        if mode == 'pending':
            document.status = 'pending'
            document.save(update_fields=['status'])
            return document

        document.status = 'processing'
        document.save(update_fields=['status'])

        try:
            # 1. Extract or simulate OCR text
            raw_text = cls._extract_raw_text(document)
            
            # 2. Convert to formatted JSON
            json_data = cls._generate_json_data(document, raw_text)
            
            # 3. Convert to formatted SQL
            sql_data = cls._generate_sql_data(document, json_data)

            # 4. Save results
            document.extracted_text = raw_text
            document.json_output = json_data
            document.sql_output = sql_data
            document.status = 'completed'
            document.completed_at = timezone.now()
            document.error_message = ''
            document.save(update_fields=[
                'extracted_text',
                'json_output',
                'sql_output',
                'status',
                'completed_at',
                'error_message'
            ])
            return document
        except Exception as exc:
            document.status = 'failed'
            document.error_message = str(exc)
            document.save(update_fields=['status', 'error_message'])
            return document

    @classmethod
    def _extract_raw_text(cls, document):
        """Read actual file text if text/csv, or simulate OCR for images/scans."""
        file_path = document.file.path if document.file else None
        ext = document.file_extension

        if file_path and os.path.exists(file_path) and ext in ['txt', 'csv', 'log', 'json']:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if content.strip():
                        return content
            except Exception:
                pass

        # Simulated OCR text tailored to the document category
        doc_type = document.doc_type
        doc_name = document.title or document.original_filename
        date_str = datetime.now().strftime('%Y-%m-%d %H:%M')

        if doc_type == 'receipt':
            return (
                f"--- OCR TEXT EXTRACTION: {doc_name} ---\n"
                f"MERCHANT: Metro Supermart & Supplies\n"
                f"STORE #402 - Quezon City\n"
                f"DATE/TIME: {date_str}\n"
                f"TRANS ID: TXN-{abs(hash(doc_name)) % 1000000:06d}\n"
                f"CASHIER: Staff #14\n"
                f"----------------------------------------\n"
                f"1x Thermal Paper Roll (50pcs)       ₱ 450.00\n"
                f"2x Wireless Optical Mouse           ₱ 980.00\n"
                f"1x USB-C Multiport Hub              ₱ 1,250.00\n"
                f"3x Office Gel Pens (Pack of 12)     ₱ 360.00\n"
                f"----------------------------------------\n"
                f"SUBTOTAL:                           ₱ 3,040.00\n"
                f"VAT (12%):                          ₱ 364.80\n"
                f"TOTAL AMOUNT:                       ₱ 3,404.80\n"
                f"PAYMENT: GCash / Electronic Transfer\n"
                f"APPROVAL CODE: APV-883921\n"
                f"STATUS: PAID IN FULL\n"
                f"THANK YOU FOR YOUR BUSINESS!"
            )
        elif doc_type == 'invoice':
            return (
                f"--- OCR TEXT EXTRACTION: {doc_name} ---\n"
                f"INVOICE NUMBER: INV-2026-{abs(hash(doc_name)) % 10000:04d}\n"
                f"ISSUER: SnatPap Technologies Inc.\n"
                f"TAX ID: 009-241-883-000\n"
                f"BILL TO: {document.user.get_full_name() or document.user.username}\n"
                f"INVOICE DATE: {datetime.now().strftime('%Y-%m-%d')}\n"
                f"DUE DATE: {datetime.now().strftime('%Y-%m-%d')}\n"
                f"LINE ITEMS:\n"
                f"- Software Integration Consulting (10 hrs @ ₱1,500/hr) = ₱15,000.00\n"
                f"- Data Migration & Pipeline Setup (1 unit) = ₱8,500.00\n"
                f"- Cloud Server Allocation (1 month) = ₱3,200.00\n"
                f"NET TOTAL: ₱26,700.00\n"
                f"TAX: ₱3,204.00\n"
                f"AMOUNT DUE: ₱29,904.00\n"
                f"TERMS: Net 30 days"
            )
        elif doc_type == 'record':
            return (
                f"--- OCR TEXT EXTRACTION: {doc_name} ---\n"
                f"OFFICIAL RECORD / ARCHIVE DOSSIER\n"
                f"RECORD ID: REC-{abs(hash(doc_name)) % 999999:06d}\n"
                f"CLASSIFICATION: Administrative Registry\n"
                f"TIMESTAMP: {date_str}\n"
                f"FILING OFFICER: {document.user.username}\n"
                f"SUBJECT: Asset & Document Processing Verification\n"
                f"PARAMETERS RECORDED:\n"
                f"- Verification Hash: SHA256:{abs(hash(doc_name)):x}98a4f10c\n"
                f"- Verification Status: Verified & Recorded\n"
                f"- Compliance Standard: ISO/IEC 27001 & DPA 2012\n"
                f"- Audit Checksum: OK"
            )
        else:
            return (
                f"--- OCR TEXT EXTRACTION: {doc_name} ---\n"
                f"DOCUMENT: {doc_name}\n"
                f"TYPE: {document.get_doc_type_display()}\n"
                f"INGESTION DATE: {date_str}\n"
                f"PARSED PARAGRAPHS:\n"
                f"Section 1: Summary of Document Contents and Metadata Attributes.\n"
                f"Section 2: Extracted Key-Value Entities and Quantitative Metrics.\n"
                f"Section 3: Audit trail completed without format anomalies."
            )

    @classmethod
    def _generate_json_data(cls, document, raw_text):
        """Generate structured JSON representation from raw text."""
        doc_type = document.doc_type
        doc_id = f"DOC-{abs(hash(document.original_filename)) % 100000:05d}"
        now_iso = timezone.now().isoformat()

        if doc_type == 'receipt':
            return {
                "document_id": doc_id,
                "document_type": "Receipt",
                "vendor": {
                    "name": "Metro Supermart & Supplies",
                    "store_id": "STORE-402",
                    "location": "Quezon City, PH"
                },
                "transaction": {
                    "receipt_number": f"REC-2026-{document.id:04d}",
                    "date": datetime.now().strftime('%Y-%m-%d'),
                    "time": datetime.now().strftime('%H:%M:%S'),
                    "payment_method": "GCash / Electronic",
                    "status": "PAID"
                },
                "items": [
                    {"sku": "SKU-101", "name": "Thermal Paper Roll (50pcs)", "quantity": 1, "unit_price": 450.00, "total": 450.00},
                    {"sku": "SKU-205", "name": "Wireless Optical Mouse", "quantity": 2, "unit_price": 490.00, "total": 980.00},
                    {"sku": "SKU-312", "name": "USB-C Multiport Hub", "quantity": 1, "unit_price": 1250.00, "total": 1250.00},
                    {"sku": "SKU-440", "name": "Office Gel Pens (Pack of 12)", "quantity": 3, "unit_price": 120.00, "total": 360.00}
                ],
                "financials": {
                    "currency": "PHP",
                    "subtotal": 3040.00,
                    "tax_rate": 0.12,
                    "tax_amount": 364.80,
                    "grand_total": 3404.80
                },
                "metadata": {
                    "file_name": document.original_filename,
                    "processed_at": now_iso,
                    "engine": "BlackBox-OCR-v2.4"
                }
            }
        elif doc_type == 'invoice':
            return {
                "document_id": doc_id,
                "document_type": "Invoice",
                "invoice_number": f"INV-2026-{document.id:04d}",
                "issuer": {
                    "company": "SnatPap Technologies Inc.",
                    "tax_id": "009-241-883-000",
                    "email": "billing@snatpap.local"
                },
                "customer": {
                    "client_name": document.user.get_full_name() or document.user.username,
                    "username": document.user.username,
                    "account_ref": f"USR-{document.user.id:04d}"
                },
                "dates": {
                    "issue_date": datetime.now().strftime('%Y-%m-%d'),
                    "due_date": datetime.now().strftime('%Y-%m-%d'),
                    "terms": "Net 30"
                },
                "line_items": [
                    {"description": "Software Integration Consulting", "hours": 10, "rate": 1500.00, "amount": 15000.00},
                    {"description": "Data Migration & Pipeline Setup", "quantity": 1, "rate": 8500.00, "amount": 8500.00},
                    {"description": "Cloud Server Allocation", "period": "1 month", "rate": 3200.00, "amount": 3200.00}
                ],
                "summary": {
                    "currency": "PHP",
                    "net_amount": 26700.00,
                    "tax": 3204.00,
                    "total_payable": 29904.00,
                    "payment_status": "PENDING"
                },
                "metadata": {
                    "file_name": document.original_filename,
                    "processed_at": now_iso
                }
            }
        elif doc_type == 'record':
            return {
                "record_id": doc_id,
                "record_type": "Official Archive",
                "registered_by": document.user.username,
                "subject": document.title or "Administrative Verification",
                "classification": "CONFIDENTIAL_REGISTRY",
                "verification": {
                    "hash_algorithm": "SHA-256",
                    "digital_signature_valid": True,
                    "compliance": ["ISO-27001", "DPA-2012"],
                    "verification_date": datetime.now().strftime('%Y-%m-%d')
                },
                "attributes": {
                    "original_file": document.original_filename,
                    "size_bytes": document.file_size,
                    "file_type": document.content_type or document.file_extension,
                    "tokens_allocated": document.tokens_cost
                },
                "metadata": {
                    "processed_at": now_iso,
                    "engine": "BlackBox-RecordParser-v1.8"
                }
            }
        else:
            return {
                "document_id": doc_id,
                "title": document.title or document.original_filename,
                "document_type": document.get_doc_type_display(),
                "file_info": {
                    "filename": document.original_filename,
                    "extension": document.file_extension,
                    "size_bytes": document.file_size
                },
                "extracted_fields": {
                    "author": document.user.username,
                    "status": "PARSED_SUCCESSFULLY",
                    "page_count": 1,
                    "word_count": len(raw_text.split()),
                    "detected_language": "en"
                },
                "metadata": {
                    "processed_at": now_iso,
                    "black_box_model": "TextExtract-Neural-Engine"
                }
            }

    @classmethod
    def _generate_sql_data(cls, document, json_data):
        """Generate structured SQL DDL and DML statements from JSON data."""
        doc_type = document.doc_type
        table_prefix = f"doc_{document.id}"

        if doc_type == 'receipt':
            inv_num = json_data.get('transaction', {}).get('receipt_number', f"REC-{document.id}")
            vendor = json_data.get('vendor', {}).get('name', 'Merchant')
            subtotal = json_data.get('financials', {}).get('subtotal', 0.0)
            tax = json_data.get('financials', {}).get('tax_amount', 0.0)
            total = json_data.get('financials', {}).get('grand_total', 0.0)
            pay_method = json_data.get('transaction', {}).get('payment_method', 'Cash')
            tx_date = json_data.get('transaction', {}).get('date', datetime.now().strftime('%Y-%m-%d'))

            items_sql = []
            for item in json_data.get('items', []):
                name = item.get('name', '').replace("'", "''")
                sku = item.get('sku', '')
                qty = item.get('quantity', 1)
                unit_price = item.get('unit_price', 0.0)
                tot = item.get('total', 0.0)
                items_sql.append(
                    f"INSERT INTO receipt_items (receipt_id, sku, item_name, quantity, unit_price, total_price)\n"
                    f"VALUES ('{inv_num}', '{sku}', '{name}', {qty}, {unit_price:.2f}, {tot:.2f});"
                )
            items_inserts = "\n".join(items_sql)

            return (
                f"-- ========================================================\n"
                f"-- SnatPap Auto-Generated SQL for Receipt: {document.original_filename}\n"
                f"-- ========================================================\n\n"
                f"CREATE TABLE IF NOT EXISTS receipts (\n"
                f"    receipt_id VARCHAR(50) PRIMARY KEY,\n"
                f"    vendor_name VARCHAR(150) NOT NULL,\n"
                f"    transaction_date DATE NOT NULL,\n"
                f"    subtotal DECIMAL(10, 2) NOT NULL,\n"
                f"    tax_amount DECIMAL(10, 2) NOT NULL,\n"
                f"    total_amount DECIMAL(10, 2) NOT NULL,\n"
                f"    payment_method VARCHAR(50),\n"
                f"    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n"
                f");\n\n"
                f"CREATE TABLE IF NOT EXISTS receipt_items (\n"
                f"    item_id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
                f"    receipt_id VARCHAR(50) REFERENCES receipts(receipt_id),\n"
                f"    sku VARCHAR(50),\n"
                f"    item_name VARCHAR(255) NOT NULL,\n"
                f"    quantity INTEGER NOT NULL,\n"
                f"    unit_price DECIMAL(10, 2) NOT NULL,\n"
                f"    total_price DECIMAL(10, 2) NOT NULL\n"
                f");\n\n"
                f"INSERT INTO receipts (receipt_id, vendor_name, transaction_date, subtotal, tax_amount, total_amount, payment_method)\n"
                f"VALUES ('{inv_num}', '{vendor}', '{tx_date}', {subtotal:.2f}, {tax:.2f}, {total:.2f}, '{pay_method}');\n\n"
                f"{items_inserts}\n"
            )
        elif doc_type == 'invoice':
            inv_num = json_data.get('invoice_number', f"INV-{document.id}")
            company = json_data.get('issuer', {}).get('company', 'Issuer')
            client = json_data.get('customer', {}).get('client_name', 'Client').replace("'", "''")
            net = json_data.get('summary', {}).get('net_amount', 0.0)
            tax = json_data.get('summary', {}).get('tax', 0.0)
            total = json_data.get('summary', {}).get('total_payable', 0.0)
            issue_date = json_data.get('dates', {}).get('issue_date', datetime.now().strftime('%Y-%m-%d'))

            return (
                f"-- ========================================================\n"
                f"-- SnatPap Auto-Generated SQL for Invoice: {document.original_filename}\n"
                f"-- ========================================================\n\n"
                f"CREATE TABLE IF NOT EXISTS invoices (\n"
                f"    invoice_number VARCHAR(50) PRIMARY KEY,\n"
                f"    issuer_company VARCHAR(150) NOT NULL,\n"
                f"    client_name VARCHAR(150) NOT NULL,\n"
                f"    issue_date DATE NOT NULL,\n"
                f"    net_amount DECIMAL(12, 2) NOT NULL,\n"
                f"    tax_amount DECIMAL(12, 2) NOT NULL,\n"
                f"    total_payable DECIMAL(12, 2) NOT NULL,\n"
                f"    status VARCHAR(30) DEFAULT 'PENDING'\n"
                f");\n\n"
                f"INSERT INTO invoices (invoice_number, issuer_company, client_name, issue_date, net_amount, tax_amount, total_payable, status)\n"
                f"VALUES ('{inv_num}', '{company}', '{client}', '{issue_date}', {net:.2f}, {tax:.2f}, {total:.2f}, 'PENDING');\n"
            )
        else:
            doc_id = json_data.get('document_id', f"DOC-{document.id}")
            title = (document.title or document.original_filename).replace("'", "''")
            d_type = document.doc_type
            f_size = document.file_size
            u_name = document.user.username

            return (
                f"-- ========================================================\n"
                f"-- SnatPap Auto-Generated SQL for Document: {document.original_filename}\n"
                f"-- ========================================================\n\n"
                f"CREATE TABLE IF NOT EXISTS document_records (\n"
                f"    record_id VARCHAR(50) PRIMARY KEY,\n"
                f"    title VARCHAR(255) NOT NULL,\n"
                f"    category VARCHAR(50) NOT NULL,\n"
                f"    uploaded_by VARCHAR(150) NOT NULL,\n"
                f"    file_size_bytes INTEGER NOT NULL,\n"
                f"    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n"
                f");\n\n"
                f"INSERT INTO document_records (record_id, title, category, uploaded_by, file_size_bytes)\n"
                f"VALUES ('{doc_id}', '{title}', '{d_type}', '{u_name}', {f_size});\n"
            )

    @classmethod
    def apply_external_result(cls, document_id, extracted_text=None, json_output=None, sql_output=None, status='completed', error_message=''):
        """
        Invoked when the external converter program submits results back to SnatPap.
        """
        from .models import UploadedDocument
        try:
            document = UploadedDocument.objects.get(id=document_id)
            if extracted_text is not None:
                document.extracted_text = extracted_text
            if json_output is not None:
                if isinstance(json_output, str):
                    try:
                        document.json_output = json.loads(json_output)
                    except Exception:
                        document.json_output = {"raw": json_output}
                else:
                    document.json_output = json_output
            if sql_output is not None:
                document.sql_output = sql_output
            document.status = status
            document.error_message = error_message
            if status == 'completed':
                document.completed_at = timezone.now()
            document.save()
            return True, "Updated successfully"
        except UploadedDocument.DoesNotExist:
            return False, "Document not found"
        except Exception as exc:
            return False, str(exc)
