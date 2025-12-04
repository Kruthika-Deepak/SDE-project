"""Validation rules for invoice quality control"""
from typing import List, Optional
from datetime import datetime
from .models import Invoice, ValidationError
import re


class ValidationRule:
    """Base class for validation rules"""
    
    def __init__(self, name: str, description: str, severity: str = 'error'):
        self.name = name
        self.description = description
        self.severity = severity  # 'error' or 'warning'
    
    def validate(self, invoice: Invoice, all_invoices: List[Invoice] = None) -> List[ValidationError]:
        """Validate invoice and return list of errors"""
        raise NotImplementedError


class RequiredFieldRule(ValidationRule):
    """Rule: Required fields must not be empty"""
    
    def __init__(self):
        super().__init__(
            'required_fields',
            'Core invoice fields must be present and non-empty'
        )
        self.required_fields = [
            'invoice_number',
            'invoice_date',
            'seller_name',
            'buyer_name',
            'currency',
            'gross_total',
        ]
    
    def validate(self, invoice: Invoice, all_invoices: List[Invoice] = None) -> List[ValidationError]:
        errors = []
        
        for field in self.required_fields:
            value = getattr(invoice, field, None)
            if value is None or (isinstance(value, str) and not value.strip()):
                errors.append(ValidationError(
                    rule=self.name,
                    message=f"Required field '{field}' is missing or empty",
                    field=field
                ))
        
        return errors


class DateFormatRule(ValidationRule):
    """Rule: Dates must be in valid format and within reasonable range"""
    
    def __init__(self):
        super().__init__(
            'date_format',
            'Dates must be parseable and within reasonable range (1900-2100)'
        )
    
    def validate(self, invoice: Invoice, all_invoices: List[Invoice] = None) -> List[ValidationError]:
        errors = []
        
        # Check invoice_date
        if invoice.invoice_date:
            if not self._is_valid_date(invoice.invoice_date):
                errors.append(ValidationError(
                    rule=self.name,
                    message=f"Invalid invoice_date format: {invoice.invoice_date}",
                    field='invoice_date'
                ))
        
        # Check due_date
        if invoice.due_date:
            if not self._is_valid_date(invoice.due_date):
                errors.append(ValidationError(
                    rule=self.name,
                    message=f"Invalid due_date format: {invoice.due_date}",
                    field='due_date'
                ))
        
        return errors
    
    def _is_valid_date(self, date_str: str) -> bool:
        """Check if date string is valid"""
        try:
            dt = datetime.fromisoformat(date_str)
            # Check reasonable range
            return 1900 <= dt.year <= 2100
        except:
            return False


class CurrencyValidationRule(ValidationRule):
    """Rule: Currency must be from a known set"""
    
    VALID_CURRENCIES = {'EUR', 'USD', 'GBP', 'INR', 'JPY', 'CNY', 'CAD', 'AUD', 'CHF', 'SEK'}
    
    def __init__(self):
        super().__init__(
            'currency_validation',
            'Currency must be a recognized ISO code'
        )
    
    def validate(self, invoice: Invoice, all_invoices: List[Invoice] = None) -> List[ValidationError]:
        errors = []
        
        if invoice.currency and invoice.currency not in self.VALID_CURRENCIES:
            errors.append(ValidationError(
                rule=self.name,
                message=f"Unknown currency code: {invoice.currency}. Valid: {', '.join(sorted(self.VALID_CURRENCIES))}",
                field='currency'
            ))
        
        return errors


class DueDateRule(ValidationRule):
    """Rule: Due date must be on or after invoice date"""
    
    def __init__(self):
        super().__init__(
            'due_date_logic',
            'Due date must be on or after invoice date'
        )
    
    def validate(self, invoice: Invoice, all_invoices: List[Invoice] = None) -> List[ValidationError]:
        errors = []
        
        if invoice.invoice_date and invoice.due_date:
            try:
                invoice_dt = datetime.fromisoformat(invoice.invoice_date)
                due_dt = datetime.fromisoformat(invoice.due_date)
                
                if due_dt < invoice_dt:
                    errors.append(ValidationError(
                        rule=self.name,
                        message=f"Due date ({invoice.due_date}) is before invoice date ({invoice.invoice_date})",
                        field='due_date'
                    ))
            except:
                pass  # Date format errors caught by DateFormatRule
        
        return errors


class TotalsMatchRule(ValidationRule):
    """Rule: net_total + tax_amount ≈ gross_total"""
    
    def __init__(self, tolerance: float = 0.02):
        super().__init__(
            'totals_match',
            'Net total + tax amount should equal gross total (within tolerance)'
        )
        self.tolerance = tolerance
    
    def validate(self, invoice: Invoice, all_invoices: List[Invoice] = None) -> List[ValidationError]:
        errors = []
        
        if invoice.net_total is not None and invoice.tax_amount is not None and invoice.gross_total is not None:
            calculated_total = invoice.net_total + invoice.tax_amount
            difference = abs(calculated_total - invoice.gross_total)
            
            if difference > self.tolerance:
                errors.append(ValidationError(
                    rule=self.name,
                    message=f"Totals mismatch: {invoice.net_total} + {invoice.tax_amount} = {calculated_total}, but gross_total is {invoice.gross_total} (diff: {difference:.2f})",
                    field='gross_total'
                ))
        
        return errors


class LineItemsTotalRule(ValidationRule):
    """Rule: Sum of line item totals should match net_total"""
    
    def __init__(self, tolerance: float = 0.02):
        super().__init__(
            'line_items_total',
            'Sum of line item totals should match net total',
            severity='warning'  # Warning because line items extraction can be imperfect
        )
        self.tolerance = tolerance
    
    def validate(self, invoice: Invoice, all_invoices: List[Invoice] = None) -> List[ValidationError]:
        errors = []
        
        if invoice.net_total is not None and invoice.line_items:
            # Calculate sum of line items
            line_items_sum = sum(
                item.line_total for item in invoice.line_items 
                if item.line_total is not None
            )
            
            if line_items_sum > 0:  # Only check if we have line item data
                difference = abs(line_items_sum - invoice.net_total)
                
                if difference > self.tolerance:
                    errors.append(ValidationError(
                        rule=self.name,
                        message=f"Line items sum ({line_items_sum:.2f}) doesn't match net_total ({invoice.net_total:.2f}), diff: {difference:.2f}",
                        field='line_items'
                    ))
        
        return errors


class NegativeAmountsRule(ValidationRule):
    """Rule: Financial amounts should not be negative"""
    
    def __init__(self):
        super().__init__(
            'no_negative_amounts',
            'Invoice amounts should not be negative'
        )
    
    def validate(self, invoice: Invoice, all_invoices: List[Invoice] = None) -> List[ValidationError]:
        errors = []
        
        amount_fields = ['net_total', 'tax_amount', 'gross_total']
        
        for field in amount_fields:
            value = getattr(invoice, field, None)
            if value is not None and value < 0:
                errors.append(ValidationError(
                    rule=self.name,
                    message=f"Field '{field}' has negative value: {value}",
                    field=field
                ))
        
        return errors


class DuplicateInvoiceRule(ValidationRule):
    """Rule: No duplicate invoices (same number + seller + date)"""
    
    def __init__(self):
        super().__init__(
            'no_duplicates',
            'Invoices should not have duplicate invoice numbers from same seller on same date'
        )
    
    def validate(self, invoice: Invoice, all_invoices: List[Invoice] = None) -> List[ValidationError]:
        errors = []
        
        if not all_invoices or not invoice.invoice_number:
            return errors
        
        # Find duplicates
        duplicates = [
            inv for inv in all_invoices
            if inv.invoice_number == invoice.invoice_number
            and inv.seller_name == invoice.seller_name
            and inv.invoice_date == invoice.invoice_date
            and inv.source_file != invoice.source_file  # Different file
        ]
        
        if duplicates:
            dup_files = [inv.source_file for inv in duplicates]
            errors.append(ValidationError(
                rule=self.name,
                message=f"Duplicate invoice detected. Same invoice_number ({invoice.invoice_number}) from {invoice.seller_name} on {invoice.invoice_date}. Duplicates in: {', '.join(dup_files)}",
                field='invoice_number'
            ))
        
        return errors


# All available rules
ALL_RULES = [
    RequiredFieldRule(),
    DateFormatRule(),
    CurrencyValidationRule(),
    DueDateRule(),
    TotalsMatchRule(),
    LineItemsTotalRule(),
    NegativeAmountsRule(),
    DuplicateInvoiceRule(),
]
