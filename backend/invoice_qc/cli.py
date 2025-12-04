"""CLI interface for invoice QC service"""
import typer
import json
from pathlib import Path
from typing import Optional
from .extractor import InvoiceExtractor
from .validator import InvoiceValidator
from .models import Invoice
import sys

app = typer.Typer(
    help="Invoice Quality Control Service - Extract and validate invoice data from PDFs"
)


@app.command()
def extract(
    pdf_dir: Path = typer.Option(..., "--pdf-dir", help="Directory containing PDF invoices"),
    output: Path = typer.Option(..., "--output", help="Output JSON file for extracted data"),
):
    """Extract invoice data from PDFs"""
    if not pdf_dir.exists():
        typer.secho(f"Error: Directory {pdf_dir} does not exist", fg=typer.colors.RED)
        raise typer.Exit(1)
    
    typer.secho(f"\n⚙️  Extracting invoices from {pdf_dir}...", fg=typer.colors.CYAN)
    
    extractor = InvoiceExtractor()
    invoices = extractor.extract_from_directory(pdf_dir)
    
    # Convert to JSON
    invoices_data = [inv.model_dump() for inv in invoices]
    
    # Save to file
    with open(output, 'w') as f:
        json.dump(invoices_data, f, indent=2)
    
    typer.secho(f"\n✅ Extracted {len(invoices)} invoices", fg=typer.colors.GREEN)
    typer.secho(f"✅ Saved to {output}", fg=typer.colors.GREEN)


@app.command()
def validate(
    input: Path = typer.Option(..., "--input", help="Input JSON file with extracted invoices"),
    report: Path = typer.Option(..., "--report", help="Output JSON file for validation report"),
):
    """Validate extracted invoice data"""
    if not input.exists():
        typer.secho(f"Error: File {input} does not exist", fg=typer.colors.RED)
        raise typer.Exit(1)
    
    typer.secho(f"\n⚙️  Validating invoices from {input}...", fg=typer.colors.CYAN)
    
    # Load invoices
    with open(input, 'r') as f:
        invoices_data = json.load(f)
    
    invoices = [Invoice(**inv_data) for inv_data in invoices_data]
    
    # Validate
    validator = InvoiceValidator()
    validation_report = validator.validate_invoices(invoices)
    
    # Save report
    with open(report, 'w') as f:
        json.dump(validation_report.model_dump(), f, indent=2)
    
    # Print summary
    _print_summary(validation_report)
    
    typer.secho(f"\n✅ Validation report saved to {report}", fg=typer.colors.GREEN)
    
    # Exit with error code if there are invalid invoices
    if validation_report.summary.invalid_invoices > 0:
        raise typer.Exit(1)


@app.command(name="full-run")
def full_run(
    pdf_dir: Path = typer.Option(..., "--pdf-dir", help="Directory containing PDF invoices"),
    report: Path = typer.Option(..., "--report", help="Output JSON file for validation report"),
    save_extracted: Optional[Path] = typer.Option(None, "--save-extracted", help="Optionally save extracted data"),
):
    """Extract and validate invoices in one step"""
    if not pdf_dir.exists():
        typer.secho(f"Error: Directory {pdf_dir} does not exist", fg=typer.colors.RED)
        raise typer.Exit(1)
    
    typer.secho(f"\n⚙️  Running full invoice QC pipeline...", fg=typer.colors.CYAN)
    
    # Extract
    typer.secho(f"\n[1/2] Extracting invoices from {pdf_dir}...", fg=typer.colors.BLUE)
    extractor = InvoiceExtractor()
    invoices = extractor.extract_from_directory(pdf_dir)
    typer.secho(f"  ✓ Extracted {len(invoices)} invoices", fg=typer.colors.GREEN)
    
    # Save extracted data if requested
    if save_extracted:
        invoices_data = [inv.model_dump() for inv in invoices]
        with open(save_extracted, 'w') as f:
            json.dump(invoices_data, f, indent=2)
        typer.secho(f"  ✓ Saved extracted data to {save_extracted}", fg=typer.colors.GREEN)
    
    # Validate
    typer.secho(f"\n[2/2] Validating invoices...", fg=typer.colors.BLUE)
    validator = InvoiceValidator()
    validation_report = validator.validate_invoices(invoices)
    
    # Save report
    with open(report, 'w') as f:
        json.dump(validation_report.model_dump(), f, indent=2)
    
    # Print summary
    _print_summary(validation_report)
    
    typer.secho(f"\n✅ Validation report saved to {report}", fg=typer.colors.GREEN)
    
    # Exit with error code if there are invalid invoices
    if validation_report.summary.invalid_invoices > 0:
        raise typer.Exit(1)


def _print_summary(report):
    """Print validation summary to console"""
    summary = report.summary
    
    typer.secho("\n" + "="*60, fg=typer.colors.CYAN)
    typer.secho(" VALIDATION SUMMARY", fg=typer.colors.CYAN, bold=True)
    typer.secho("="*60, fg=typer.colors.CYAN)
    
    typer.secho(f"\nTotal Invoices:   {summary.total_invoices}", bold=True)
    typer.secho(f"Valid Invoices:   {summary.valid_invoices}", fg=typer.colors.GREEN, bold=True)
    
    if summary.invalid_invoices > 0:
        typer.secho(f"Invalid Invoices: {summary.invalid_invoices}", fg=typer.colors.RED, bold=True)
    else:
        typer.secho(f"Invalid Invoices: 0", fg=typer.colors.GREEN, bold=True)
    
    # Print error breakdown
    if summary.error_counts:
        typer.secho("\nTop Errors:", fg=typer.colors.YELLOW, bold=True)
        sorted_errors = sorted(summary.error_counts.items(), key=lambda x: x[1], reverse=True)
        for error, count in sorted_errors[:5]:
            typer.secho(f"  [{count}x] {error}", fg=typer.colors.YELLOW)
    
    # Print warning breakdown
    if summary.warning_counts:
        typer.secho("\nWarnings:", fg=typer.colors.MAGENTA, bold=True)
        sorted_warnings = sorted(summary.warning_counts.items(), key=lambda x: x[1], reverse=True)
        for warning, count in sorted_warnings[:5]:
            typer.secho(f"  [{count}x] {warning}", fg=typer.colors.MAGENTA)
    
    typer.secho("\n" + "="*60 + "\n", fg=typer.colors.CYAN)


if __name__ == "__main__":
    app()
