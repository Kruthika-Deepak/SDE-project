"""PDF extraction module - converts PDF invoices to structured JSON"""
import pdfplumber
import re
from pathlib import Path
from typing import List, Optional, Dict, Any
from .models import Invoice, LineItem
import logging

logger = logging.getLogger(__name__)


class InvoiceExtractor:
    """Extract structured data from invoice PDFs"""
    
    # Common patterns for invoice fields
    INVOICE_NUMBER_PATTERNS = [
        r'Invoice\s*(?:Number|No\.?|#)\s*:?\s*([A-Z0-9-]+)',
        r'Invoice\s+([A-Z0-9-]+)',
        r'INV[-\s]*([0-9]+)',
    ]
    
    DATE_PATTERNS = [
        r'(?:Invoice\s+)?Date\s*:?\s*(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})',
        r'Date\s*:?\s*(\d{4}[-/.]\d{2}[-/.]\d{2})',
        r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',
    ]
    
    DUE_DATE_PATTERNS = [
        r'(?:Due\s+)?(?:Date|By)\s*:?\s*(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})',
        r'Payment\s+Due\s*:?\s*(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})',
        r'Due\s*:?\s*(\d{4}[-/.]\d{2}[-/.]\d{2})',
    ]
    
    AMOUNT_PATTERNS = [
        r'(?:Total|Amount|Sum)\s*:?\s*([A-Z]{3})?\s*([€$£¥])?\s*([0-9,]+\.?\d{0,2})',
        r'([€$£¥])\s*([0-9,]+\.?\d{0,2})',
    ]
    
    CURRENCY_PATTERNS = [
        r'\b(USD|EUR|GBP|INR|JPY|CNY|CAD|AUD)\b',
        r'([€$£¥])',
    ]
    
    TAX_ID_PATTERNS = [
        r'(?:VAT|Tax|GST)\s*(?:ID|No|Number)?\s*:?\s*([A-Z0-9]+)',
        r'Tax\s+ID\s*:?\s*([A-Z0-9-]+)',
    ]
    
    def __init__(self):
        self.currency_map = {
            '€': 'EUR',
            '$': 'USD',
            '£': 'GBP',
            '¥': 'JPY',
        }
    
    def extract_from_pdf(self, pdf_path: Path) -> Invoice:
        """Extract invoice data from a single PDF file"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Extract text from all pages
                full_text = ''
                tables = []
                
                for page in pdf.pages:
                    full_text += page.extract_text() or ''
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)
                
                # Extract structured data
                invoice_data = {
                    'source_file': pdf_path.name,
                    'invoice_number': self._extract_invoice_number(full_text),
                    'invoice_date': self._extract_invoice_date(full_text),
                    'due_date': self._extract_due_date(full_text),
                    'currency': self._extract_currency(full_text),
                }
                
                # Extract seller and buyer information
                seller_info, buyer_info = self._extract_parties(full_text)
                invoice_data.update(seller_info)
                invoice_data.update(buyer_info)
                
                # Extract financial totals
                financial_data = self._extract_financials(full_text)
                invoice_data.update(financial_data)
                
                # Extract line items from tables
                line_items = self._extract_line_items(tables, full_text)
                invoice_data['line_items'] = line_items
                
                return Invoice(**invoice_data)
                
        except Exception as e:
            logger.error(f"Error extracting {pdf_path}: {e}")
            return Invoice(source_file=pdf_path.name)
    
    def extract_from_directory(self, pdf_dir: Path) -> List[Invoice]:
        """Extract invoices from all PDFs in a directory"""
        invoices = []
        pdf_files = list(pdf_dir.glob('*.pdf'))
        
        logger.info(f"Found {len(pdf_files)} PDF files in {pdf_dir}")
        
        for pdf_file in pdf_files:
            logger.info(f"Extracting {pdf_file.name}...")
            invoice = self.extract_from_pdf(pdf_file)
            invoices.append(invoice)
        
        return invoices
    
    def _extract_invoice_number(self, text: str) -> Optional[str]:
        """Extract invoice number from text"""
        for pattern in self.INVOICE_NUMBER_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_invoice_date(self, text: str) -> Optional[str]:
        """Extract invoice date from text"""
        for pattern in self.DATE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._normalize_date(match.group(1))
        return None
    
    def _extract_due_date(self, text: str) -> Optional[str]:
        """Extract due date from text"""
        for pattern in self.DUE_DATE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._normalize_date(match.group(1))
        return None
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize date to YYYY-MM-DD format"""
        # Try to parse common formats
        from datetime import datetime
        
        date_formats = [
            '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d',
            '%d-%m-%Y', '%d.%m.%Y',
            '%d %B %Y', '%d %b %Y',
        ]
        
        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.strftime('%Y-%m-%d')
            except:
                continue
        
        return date_str
    
    def _extract_currency(self, text: str) -> Optional[str]:
        """Extract currency code from text"""
        # Look for currency codes
        for pattern in self.CURRENCY_PATTERNS:
            match = re.search(pattern, text)
            if match:
                currency = match.group(1)
                if currency in self.currency_map:
                    return self.currency_map[currency]
                return currency
        return None
    
    def _extract_parties(self, text: str) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Extract seller and buyer information"""
        seller_info = {}
        buyer_info = {}
        
        # Look for seller/buyer sections
        seller_section = re.search(
            r'(?:From|Seller|Vendor|Supplier)\s*:?\s*([^\n]+(?:\n(?!(?:To|Bill|Customer))[^\n]+)*)',
            text, re.IGNORECASE | re.MULTILINE
        )
        
        buyer_section = re.search(
            r'(?:To|Bill\s+To|Customer|Buyer)\s*:?\s*([^\n]+(?:\n(?!(?:Invoice|Date))[^\n]+)*)',
            text, re.IGNORECASE | re.MULTILINE
        )
        
        if seller_section:
            seller_text = seller_section.group(1)
            lines = [l.strip() for l in seller_text.split('\n') if l.strip()]
            seller_info['seller_name'] = lines[0] if lines else None
            seller_info['seller_address'] = ' '.join(lines[1:3]) if len(lines) > 1 else None
            
            # Extract tax ID
            tax_id = self._extract_tax_id(seller_text)
            if tax_id:
                seller_info['seller_tax_id'] = tax_id
        
        if buyer_section:
            buyer_text = buyer_section.group(1)
            lines = [l.strip() for l in buyer_text.split('\n') if l.strip()]
            buyer_info['buyer_name'] = lines[0] if lines else None
            buyer_info['buyer_address'] = ' '.join(lines[1:3]) if len(lines) > 1 else None
            
            # Extract tax ID
            tax_id = self._extract_tax_id(buyer_text)
            if tax_id:
                buyer_info['buyer_tax_id'] = tax_id
        
        return seller_info, buyer_info
    
    def _extract_tax_id(self, text: str) -> Optional[str]:
        """Extract tax ID from text"""
        for pattern in self.TAX_ID_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_financials(self, text: str) -> Dict[str, Any]:
        """Extract financial amounts from text"""
        financials = {}
        
        # Extract various totals
        subtotal_match = re.search(r'(?:Subtotal|Net\s+Total|Net)\s*:?\s*[€$£¥]?\s*([0-9,]+\.?\d{0,2})', text, re.IGNORECASE)
        if subtotal_match:
            financials['net_total'] = self._parse_amount(subtotal_match.group(1))
        
        tax_match = re.search(r'(?:Tax|VAT|GST)(?:\s+Amount)?\s*:?\s*[€$£¥]?\s*([0-9,]+\.?\d{0,2})', text, re.IGNORECASE)
        if tax_match:
            financials['tax_amount'] = self._parse_amount(tax_match.group(1))
        
        total_match = re.search(r'(?:Total|Grand\s+Total|Amount\s+Due)\s*:?\s*[€$£¥]?\s*([0-9,]+\.?\d{0,2})', text, re.IGNORECASE)
        if total_match:
            financials['gross_total'] = self._parse_amount(total_match.group(1))
        
        # Extract payment terms
        payment_terms = re.search(r'(?:Payment\s+Terms|Terms)\s*:?\s*([^\n]+)', text, re.IGNORECASE)
        if payment_terms:
            financials['payment_terms'] = payment_terms.group(1).strip()
        
        return financials
    
    def _parse_amount(self, amount_str: str) -> float:
        """Parse amount string to float"""
        # Remove commas and convert to float
        cleaned = amount_str.replace(',', '').strip()
        try:
            return float(cleaned)
        except:
            return 0.0
    
    def _extract_line_items(self, tables: List[List[List[str]]], text: str) -> List[LineItem]:
        """Extract line items from tables"""
        line_items = []
        
        if not tables:
            return line_items
        
        # Find the table that looks like line items
        for table in tables:
            if len(table) < 2:  # Need at least header + 1 row
                continue
            
            # Check if this looks like a line items table
            header = [str(cell).lower() if cell else '' for cell in table[0]]
            
            # Look for common column names
            has_description = any('description' in h or 'item' in h or 'product' in h for h in header)
            has_quantity = any('qty' in h or 'quantity' in h or 'amount' in h for h in header)
            has_price = any('price' in h or 'rate' in h or 'unit' in h for h in header)
            
            if has_description and (has_quantity or has_price):
                # Parse line items
                for row in table[1:]:
                    if not row or all(not cell for cell in row):
                        continue
                    
                    item = self._parse_line_item_row(row, header)
                    if item.description:  # Only add if we got at least a description
                        line_items.append(item)
        
        return line_items
    
    def _parse_line_item_row(self, row: List[str], header: List[str]) -> LineItem:
        """Parse a single line item row"""
        item = LineItem()
        
        for idx, cell in enumerate(row):
            if not cell or idx >= len(header):
                continue
            
            cell = str(cell).strip()
            col_name = header[idx]
            
            # Match column to field
            if 'description' in col_name or 'item' in col_name or 'product' in col_name:
                item.description = cell
            elif 'qty' in col_name or 'quantity' in col_name:
                try:
                    item.quantity = float(cell.replace(',', ''))
                except:
                    pass
            elif 'unit' in col_name and 'price' in col_name:
                try:
                    item.unit_price = self._parse_amount(cell)
                except:
                    pass
            elif 'total' in col_name or 'amount' in col_name:
                try:
                    item.line_total = self._parse_amount(cell)
                except:
                    pass
        
        return item
