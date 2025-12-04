"""Validation module - validates extracted invoices against rules"""
from typing import List
from .models import (
    Invoice, 
    InvoiceValidationResult, 
    ValidationSummary, 
    ValidationReport,
    ValidationError
)
from .rules import ALL_RULES, ValidationRule
import logging

logger = logging.getLogger(__name__)


class InvoiceValidator:
    """Validate invoices against quality control rules"""
    
    def __init__(self, rules: List[ValidationRule] = None):
        """Initialize validator with rules"""
        self.rules = rules or ALL_RULES
    
    def validate_invoice(self, invoice: Invoice, all_invoices: List[Invoice] = None) -> InvoiceValidationResult:
        """Validate a single invoice"""
        invoice_id = invoice.invoice_number or invoice.source_file or 'unknown'
        errors = []
        warnings = []
        
        # Apply all rules
        for rule in self.rules:
            rule_errors = rule.validate(invoice, all_invoices)
            
            # Separate errors and warnings based on severity
            for error in rule_errors:
                if rule.severity == 'warning':
                    warnings.append(error)
                else:
                    errors.append(error)
        
        is_valid = len(errors) == 0
        
        return InvoiceValidationResult(
            invoice_id=invoice_id,
            is_valid=is_valid,
            errors=errors,
            warnings=warnings
        )
    
    def validate_invoices(self, invoices: List[Invoice]) -> ValidationReport:
        """Validate multiple invoices and generate report"""
        logger.info(f"Validating {len(invoices)} invoices...")
        
        results = []
        
        # Validate each invoice
        for invoice in invoices:
            result = self.validate_invoice(invoice, invoices)
            results.append(result)
        
        # Generate summary
        summary = self._generate_summary(results)
        
        return ValidationReport(
            summary=summary,
            results=results
        )
    
    def _generate_summary(self, results: List[InvoiceValidationResult]) -> ValidationSummary:
        """Generate validation summary from results"""
        total = len(results)
        valid = sum(1 for r in results if r.is_valid)
        invalid = total - valid
        
        # Count error types
        error_counts = {}
        warning_counts = {}
        
        for result in results:
            for error in result.errors:
                key = f"{error.rule}: {error.message.split('.')[0]}"
                error_counts[key] = error_counts.get(key, 0) + 1
            
            for warning in result.warnings:
                key = f"{warning.rule}: {warning.message.split('.')[0]}"
                warning_counts[key] = warning_counts.get(key, 0) + 1
        
        return ValidationSummary(
            total_invoices=total,
            valid_invoices=valid,
            invalid_invoices=invalid,
            error_counts=error_counts,
            warning_counts=warning_counts
        )
