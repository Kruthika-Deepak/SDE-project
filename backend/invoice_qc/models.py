"""Data models for invoice extraction and validation"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import date


class LineItem(BaseModel):
    """Individual line item in an invoice"""
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    line_total: Optional[float] = None


class Invoice(BaseModel):
    """Complete invoice data structure"""
    # Identifiers
    invoice_number: Optional[str] = None
    external_reference: Optional[str] = None
    
    # Dates
    invoice_date: Optional[str] = None  # Will be validated as date
    due_date: Optional[str] = None
    
    # Seller information
    seller_name: Optional[str] = None
    seller_address: Optional[str] = None
    seller_tax_id: Optional[str] = None
    
    # Buyer information
    buyer_name: Optional[str] = None
    buyer_address: Optional[str] = None
    buyer_tax_id: Optional[str] = None
    
    # Financial details
    currency: Optional[str] = None
    net_total: Optional[float] = None
    tax_amount: Optional[float] = None
    gross_total: Optional[float] = None
    payment_terms: Optional[str] = None
    
    # Line items
    line_items: List[LineItem] = Field(default_factory=list)
    
    # Metadata
    source_file: Optional[str] = None


class ValidationError(BaseModel):
    """Individual validation error"""
    rule: str
    message: str
    field: Optional[str] = None


class InvoiceValidationResult(BaseModel):
    """Validation result for a single invoice"""
    invoice_id: str
    is_valid: bool
    errors: List[ValidationError] = Field(default_factory=list)
    warnings: List[ValidationError] = Field(default_factory=list)


class ValidationSummary(BaseModel):
    """Aggregated validation summary"""
    total_invoices: int
    valid_invoices: int
    invalid_invoices: int
    error_counts: Dict[str, int] = Field(default_factory=dict)
    warning_counts: Dict[str, int] = Field(default_factory=dict)


class ValidationReport(BaseModel):
    """Complete validation report"""
    summary: ValidationSummary
    results: List[InvoiceValidationResult]
