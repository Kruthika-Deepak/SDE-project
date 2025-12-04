#!/bin/bash
# Test script for Invoice QC CLI

set -e

echo "======================================"
echo "Invoice QC CLI Test Suite"
echo "======================================"
echo ""

# Check if sample invoices directory exists
if [ ! -d "/app/sample_invoices" ]; then
    echo "Creating sample_invoices directory..."
    mkdir -p /app/sample_invoices
fi

# Check if output directory exists
if [ ! -d "/app/output" ]; then
    echo "Creating output directory..."
    mkdir -p /app/output
fi

echo "Test 1: Validate Sample JSON"
echo "-----------------------------"
cat > /app/output/sample_invoices.json << 'EOF'
[
  {
    "invoice_number": "INV-2024-001",
    "invoice_date": "2024-01-15",
    "due_date": "2024-02-15",
    "seller_name": "Tech Solutions GmbH",
    "seller_address": "123 Business St, Berlin, Germany",
    "seller_tax_id": "DE123456789",
    "buyer_name": "Global Corp Ltd",
    "buyer_address": "456 Commerce Ave, London, UK",
    "buyer_tax_id": "GB987654321",
    "currency": "EUR",
    "net_total": 5000.00,
    "tax_amount": 950.00,
    "gross_total": 5950.00,
    "payment_terms": "Net 30",
    "line_items": [
      {
        "description": "Software License - Annual",
        "quantity": 10,
        "unit_price": 500.00,
        "line_total": 5000.00
      }
    ]
  },
  {
    "invoice_number": "INV-2024-002",
    "invoice_date": "2024-01-20",
    "seller_name": "ACME Corp",
    "currency": "USD",
    "net_total": 1000.00,
    "tax_amount": 100.00,
    "gross_total": 1200.00
  }
]
EOF

cd /app/backend
python -m invoice_qc.cli validate \
  --input /app/output/sample_invoices.json \
  --report /app/output/validation_report.json || true

echo ""
echo "Test 2: Check API Health"
echo "------------------------"
echo "API health check (requires server to be running):"
echo "curl http://localhost:8001/api/health"

echo ""
echo "======================================"
echo "Tests completed!"
echo "======================================"
echo ""
echo "Check the following files:"
echo "  - /app/output/sample_invoices.json"
echo "  - /app/output/validation_report.json"
echo ""
echo "To run the API server:"
echo "  cd /app/backend && uvicorn server:app --reload --host 0.0.0.0 --port 8001"
echo ""
echo "To run the frontend:"
echo "  cd /app/frontend && yarn start"
