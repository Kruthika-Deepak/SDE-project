# Invoice QC Service - Quality Control & Validation System

## Overview

A comprehensive **Invoice Extraction & Quality Control Service** that reads invoice PDFs, extracts structured data, validates against business rules, and provides multiple interfaces (CLI, HTTP API, and Web UI) for integration into larger systems.

### Completed Features

✅ **Extraction Module**: PDF → Structured JSON extraction using pdfplumber
✅ **Validation Core**: Rule-based quality control with 8 comprehensive rules
✅ **CLI Interface**: Command-line tool with extract, validate, and full-run commands
✅ **HTTP API**: RESTful FastAPI service with 6+ endpoints
✅ **Frontend UI** (Bonus): React-based QC Console for upload, validation, and visualization

---

## Schema & Validation Design

### Invoice Schema (15 Fields)

I designed the invoice schema to capture both invoice-level metadata and line-item details commonly found in B2B invoices:

#### **Identifiers**
- `invoice_number` (string): Primary invoice identifier
- `external_reference` (string): Optional external reference/PO number
- `source_file` (string): Original PDF filename for traceability

#### **Dates**
- `invoice_date` (string, ISO format): Invoice issue date
- `due_date` (string, ISO format): Payment due date

#### **Seller Information**
- `seller_name` (string): Vendor/supplier name
- `seller_address` (string): Seller business address
- `seller_tax_id` (string): VAT/Tax ID of seller

#### **Buyer Information**
- `buyer_name` (string): Customer/buyer name
- `buyer_address` (string): Buyer business address
- `buyer_tax_id` (string): VAT/Tax ID of buyer

#### **Financial Details**
- `currency` (string): ISO currency code (EUR, USD, GBP, etc.)
- `net_total` (float): Subtotal before tax
- `tax_amount` (float): Tax/VAT amount
- `gross_total` (float): Total amount including tax
- `payment_terms` (string): Payment terms (e.g., "Net 30")

#### **Line Items** (Array)
- `description` (string): Item/service description
- `quantity` (float): Quantity ordered
- `unit_price` (float): Price per unit
- `line_total` (float): Line item total

**Rationale**: This schema covers essential B2B invoice requirements while remaining flexible enough to handle variations in invoice formats. Line items are included to enable detailed validation and auditing.

---

### Validation Rules (8 Rules)

#### **Completeness Rules**

1. **required_fields** (Error)
   - **Rule**: Core fields must be non-empty: `invoice_number`, `invoice_date`, `seller_name`, `buyer_name`, `currency`, `gross_total`
   - **Rationale**: These fields are essential for invoice processing and payment. Missing data makes the invoice unusable.

2. **date_format** (Error)
   - **Rule**: Dates must be parseable and within range 1900-2100
   - **Rationale**: Invalid dates cause processing failures and indicate OCR/extraction errors. Date range prevents obvious errors.

3. **currency_validation** (Error)
   - **Rule**: Currency must be from known ISO set (EUR, USD, GBP, INR, JPY, CNY, CAD, AUD, CHF, SEK)
   - **Rationale**: Prevents typos and ensures compatibility with payment/accounting systems.

#### **Business Logic Rules**

4. **due_date_logic** (Error)
   - **Rule**: `due_date` must be on or after `invoice_date`
   - **Rationale**: A due date before invoice date is logically impossible and indicates data corruption.

5. **totals_match** (Error, tolerance: 0.02)
   - **Rule**: `net_total + tax_amount ≈ gross_total` (within £0.02 for rounding)
   - **Rationale**: Financial integrity check. Mismatches indicate calculation errors or data corruption.

6. **line_items_total** (Warning, tolerance: 0.02)
   - **Rule**: Sum of line item totals should match `net_total`
   - **Rationale**: Ensures line-level detail matches invoice total. Set as warning because line extraction can be imperfect.

#### **Anomaly Detection Rules**

7. **no_negative_amounts** (Error)
   - **Rule**: `net_total`, `tax_amount`, `gross_total` must not be negative
   - **Rationale**: Negative amounts indicate extraction errors (credit notes should be handled separately).

8. **no_duplicates** (Error)
   - **Rule**: No duplicate invoices with same `invoice_number` + `seller_name` + `invoice_date`
   - **Rationale**: Prevents duplicate processing/payment. Critical for financial control.

---

## Architecture

### Project Structure

```
/app/
├── backend/
│   ├── invoice_qc/              # Core invoice QC package
│   │   ├── __init__.py
│   │   ├── models.py          # Pydantic data models
│   │   ├── extractor.py       # PDF extraction logic
│   │   ├── validator.py       # Validation engine
│   │   ├── rules.py           # Validation rules
│   │   └── cli.py             # CLI interface
│   ├── server.py              # FastAPI application
│   ├── requirements.txt       # Python dependencies
│   └── .env                   # Environment variables
│
├── frontend/                  # React web application
│   ├── src/
│   │   ├── pages/
│   │   │   └── Dashboard.jsx  # Main QC console
│   │   ├── components/
│   │   │   ├── ValidationSummary.jsx
│   │   │   ├── InvoiceResults.jsx
│   │   │   └── JSONInput.jsx
│   │   ├── App.js
│   │   └── App.css
│   ├── package.json
│   └── .env
│
├── sample_invoices/           # Sample PDF invoices (to be added)
├── output/                    # Output directory for reports
└── README.md                  # This file
```

### System Flow

```
[PDFs] → [Extraction] → [JSON] → [Validation] → [Reports/API/UI]

1. PDFs: Input invoice files (manual upload or API)
2. Extraction: pdfplumber extracts text → pattern matching → structured JSON
3. JSON: Normalized invoice data (Invoice model)
4. Validation: Rule engine applies 8 rules → generates results
5. Output:
   - CLI: Terminal summary + JSON report
   - API: JSON response (summary + per-invoice results)
   - UI: Interactive dashboard with filtering
```

### Component Details

#### **Extraction Pipeline** (`extractor.py`)
1. `pdfplumber` opens PDF and extracts raw text + tables
2. Regex patterns match common invoice labels ("Invoice No", "Date", "Total", etc.)
3. Seller/buyer sections identified via keywords ("From", "To", "Bill To")
4. Financial amounts extracted with currency symbols
5. Tables parsed for line items (heuristic: look for Description/Qty/Price columns)
6. Data normalized to Invoice model

#### **Validation Core** (`validator.py` + `rules.py`)
1. Each rule is a class implementing `validate(invoice, all_invoices)` method
2. Rules return list of `ValidationError` objects
3. Validator applies all rules to each invoice
4. Results aggregated into `ValidationReport` with summary statistics
5. Errors vs warnings separated by severity level

#### **CLI** (`cli.py`)
- Built with `typer` for modern CLI with type hints
- Three commands: `extract`, `validate`, `full-run`
- Colored output with progress indicators
- Exit code 1 if validation fails (useful for CI/CD)

#### **API** (`server.py`)
- FastAPI with auto-generated OpenAPI docs
- Endpoints:
  - `POST /api/validate-json`: Validate pre-extracted JSON
  - `POST /api/extract-and-validate`: Upload PDFs, get full pipeline
  - `GET /api/health`: Health check
  - `GET /api/validation-rules`: List all rules
  - `POST /api/save-validation`: Store results in MongoDB
  - `GET /api/validation-history`: Retrieve past validations

#### **Frontend** (Bonus)
- React + shadcn/ui components
- Two input modes:
  - PDF upload: Multi-file upload → extract & validate
  - JSON input: Paste/load sample → validate only
- Real-time validation results with:
  - Summary cards (total/valid/invalid/success rate)
  - Filterable invoice list (all/valid/invalid)
  - Expandable details per invoice (errors, warnings, line items)
  - Error breakdown by rule type

---

## Setup & Installation

### Prerequisites
- **Python**: 3.9+
- **Node.js**: 16+ (for frontend)
- **MongoDB**: Running locally on port 27017 (or update `MONGO_URL` in `.env`)

### Backend Setup

```bash
# Navigate to backend
cd /app/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run API server
uvicorn server:app --reload --host 0.0.0.0 --port 8001

# API will be available at: http://localhost:8001
# API docs: http://localhost:8001/docs
```

### Frontend Setup

```bash
# Navigate to frontend
cd /app/frontend

# Install dependencies
yarn install

# Start development server
yarn start

# App will open at: http://localhost:3000
```

### Environment Configuration

**Backend** (`/app/backend/.env`):
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=invoice_qc_db
CORS_ORIGINS=*
```

**Frontend** (`/app/frontend/.env`):
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

---

## Usage

### CLI Usage

#### 1. Extract Only

Extract invoice data from PDFs and save to JSON:

```bash
cd /app/backend
python -m invoice_qc.cli extract \
  --pdf-dir /app/sample_invoices \
  --output /app/output/extracted_invoices.json
```

**Output**: JSON file with extracted invoice data

#### 2. Validate Only

Validate pre-extracted JSON data:

```bash
python -m invoice_qc.cli validate \
  --input /app/output/extracted_invoices.json \
  --report /app/output/validation_report.json
```

**Output**: 
- Terminal summary (total, valid, invalid, top errors)
- JSON validation report
- Exit code 1 if any invoices invalid

#### 3. Full Run (Extract + Validate)

Run complete pipeline in one command:

```bash
python -m invoice_qc.cli full-run \
  --pdf-dir /app/sample_invoices \
  --report /app/output/validation_report.json \
  --save-extracted /app/output/extracted_invoices.json
```

**Output**: Both extracted data and validation report

### API Usage

#### Start the API Server

```bash
cd /app/backend
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

#### 1. Health Check

```bash
curl http://localhost:8001/api/health
```

**Response**:
```json
{
  "status": "ok",
  "service": "invoice-qc"
}
```

#### 2. Validate JSON Data

```bash
curl -X POST http://localhost:8001/api/validate-json \
  -H "Content-Type: application/json" \
  -d '{
    "invoices": [
      {
        "invoice_number": "INV-001",
        "invoice_date": "2024-01-10",
        "due_date": "2024-01-25",
        "seller_name": "ACME Corp",
        "buyer_name": "Example Inc",
        "currency": "USD",
        "net_total": 1000.00,
        "tax_amount": 180.00,
        "gross_total": 1180.00
      }
    ]
  }'
```

**Response**:
```json
{
  "summary": {
    "total_invoices": 1,
    "valid_invoices": 1,
    "invalid_invoices": 0,
    "error_counts": {},
    "warning_counts": {}
  },
  "results": [
    {
      "invoice_id": "INV-001",
      "is_valid": true,
      "errors": [],
      "warnings": []
    }
  ]
}
```

#### 3. Extract and Validate PDFs

```bash
curl -X POST http://localhost:8001/api/extract-and-validate \
  -F "files=@/app/sample_invoices/invoice1.pdf" \
  -F "files=@/app/sample_invoices/invoice2.pdf"
```

**Response**: Both extracted invoices and validation report

#### 4. Get Validation Rules

```bash
curl http://localhost:8001/api/validation-rules
```

**Response**: List of all validation rules with descriptions

### Frontend Usage

1. **Start the frontend** (see Frontend Setup above)
2. **Open browser** at `http://localhost:3000`
3. **Choose input mode**:
   - **Upload PDFs**: Drag & drop or browse for PDF files → Click "Extract & Validate"
   - **Paste JSON**: Switch to JSON tab → Paste invoice JSON array → Click "Validate JSON"
4. **View results**:
   - Summary dashboard shows totals and success rate
   - Invoice list with filtering (all/valid/invalid)
   - Click any invoice to expand details (errors, warnings, line items)

---

## Integration with Larger Systems

### How This Service Integrates

This invoice QC service is designed as a **microservice** that can plug into document processing pipelines:

#### **Upstream Integration**
- **Document Management Systems**: After invoices are uploaded to DMS, trigger API call to `/api/extract-and-validate`
- **Email Processing**: Email attachment processor extracts PDFs → sends to QC service
- **OCR Pipeline**: OCR service outputs structured JSON → validates via `/api/validate-json`

#### **Downstream Integration**
- **Accounting Systems**: Valid invoices auto-posted to accounting (SAP, QuickBooks, etc.)
- **Payment Gateway**: Validated invoices trigger payment workflow
- **Data Warehouse**: Validation results logged for analytics and auditing
- **Alert System**: Invalid invoices trigger notifications to AP team

#### **Workflow Example**

```
[Email Scanner] → [PDF Extract] → [Invoice QC Service] → Decision:
                                                            │
                                    Valid → [Accounting System] → [Payment]
                                                            │
                                    Invalid → [Alert AP Team] → [Manual Review]
```

### Deployment & Scalability

#### **Containerization** (Docker)

```dockerfile
# Example Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ .

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
```

Deploy with:
- **Docker Compose**: Multi-container setup (API + MongoDB + Frontend)
- **Kubernetes**: Scalable deployment with auto-scaling based on load
- **Cloud Services**: AWS ECS, Google Cloud Run, Azure Container Instances

#### **Queue Integration** (For High Volume)

For processing large batches:

```
[Upload Service] → [RabbitMQ/Redis Queue] → [Worker Nodes] → [Results DB]
                                                │
                                          [Invoice QC Service]
```

- Upload service adds PDFs to queue
- Worker nodes (multiple instances) consume queue
- Each worker calls QC service
- Results stored in database for retrieval

### API Authentication (Future Enhancement)

For production:
- Add JWT or API key authentication
- Rate limiting per client
- Role-based access control (admin vs read-only)

---

### Tools Used

1. **ChatGPT-4** (OpenAI)
   - Initial project structure and architecture design
   - Regex patterns for invoice field extraction
   - Pydantic model design
   - FastAPI endpoint scaffolding

2. **GitHub Copilot**
   - Code completion for repetitive patterns
   - React component structure
   - CSS styling suggestions

### Assumptions

1. **PDF Format**: Invoices are text-based PDFs (not scanned images requiring OCR)
2. **Language**: Invoice text is in English
3. **Structure**: Invoices follow common B2B format (seller/buyer sections, line items table)
4. **Currency**: Single currency per invoice
5. **Date Format**: Dates are in common formats (ISO, DD/MM/YYYY, MM/DD/YYYY)

### Edge Cases Not Fully Handled

- **Credit Notes**: Negative amounts treated as errors (should be separate document type)
- **Multi-Currency**: Invoices with multiple currencies
- **Partial Payments**: No tracking of payment status
- **Amended Invoices**: No versioning or amendment tracking

### Future Enhancements

- Add OCR support (Tesseract, AWS Textract, Google Vision API)
- Multi-language support
- Machine learning for field extraction (instead of regex)
- Historical duplicate checking against database
- Real-time validation webhooks
- Batch processing with progress tracking
- Export to accounting formats (QuickBooks IIF, SAP IDOC)

---

## Testing

To test the service with sample invoices:

1. **Add PDFs** to `/app/sample_invoices/`
2. **Run CLI**:
   ```bash
   python -m invoice_qc.cli full-run \
     --pdf-dir /app/sample_invoices \
     --report /app/output/report.json
   ```
```

Validate with:
```bash
python -m invoice_qc.cli validate \
  --input /app/output/test_invoice.json \
  --report /app/output/test_report.json
```

## GitHub Repository

**Repository**: [To be added - Private repo shared with deeplogicaitech and csvinay]

---

## Contact

**Author**: Kruthika D
**Email**: kruthika.deepaks@gmail.com
**Date**: December 2025

---

## License

This project was created as a take-home assignment for Software Engineer Intern position.
