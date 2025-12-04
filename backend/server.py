from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import json
import tempfile
import shutil

# Import invoice QC modules
from invoice_qc.models import Invoice, ValidationReport, InvoiceValidationResult
from invoice_qc.extractor import InvoiceExtractor
from invoice_qc.validator import InvoiceValidator


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Invoice Quality Control Service")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str


class ValidateJSONRequest(BaseModel):
    """Request body for JSON validation"""
    invoices: List[Invoice]


class ExtractAndValidateResponse(BaseModel):
    """Response for extract-and-validate endpoint"""
    extracted_invoices: List[Invoice]
    validation_report: ValidationReport


# Original routes
@api_router.get("/")
async def root():
    return {"message": "Invoice Quality Control Service API", "version": "1.0.0"}


@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "invoice-qc"}


@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    # Convert to dict and serialize datetime to ISO string for MongoDB
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj


@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    # Exclude MongoDB's _id field from the query results
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    # Convert ISO string timestamps back to datetime objects
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks


# Invoice QC endpoints
@api_router.post("/validate-json", response_model=ValidationReport)
async def validate_json(request: ValidateJSONRequest):
    """
    Validate a list of invoice JSON objects.
    
    This endpoint accepts already-extracted invoice data and validates it
    against the quality control rules.
    """
    try:
        validator = InvoiceValidator()
        report = validator.validate_invoices(request.invoices)
        return report
    except Exception as e:
        logging.error(f"Validation error: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@api_router.post("/extract-and-validate", response_model=ExtractAndValidateResponse)
async def extract_and_validate_pdfs(files: List[UploadFile] = File(...)):
    """
    Upload PDF files, extract invoice data, and validate.
    
    This endpoint handles the full pipeline:
    1. Accept PDF file uploads
    2. Extract structured data from PDFs
    3. Validate extracted data
    4. Return both extracted data and validation results
    """
    # Create temporary directory for PDFs
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Save uploaded files
        pdf_paths = []
        for file in files:
            if not file.filename.endswith('.pdf'):
                raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF")
            
            file_path = temp_dir / file.filename
            with open(file_path, 'wb') as f:
                content = await file.read()
                f.write(content)
            pdf_paths.append(file_path)
        
        # Extract invoices
        extractor = InvoiceExtractor()
        invoices = []
        for pdf_path in pdf_paths:
            invoice = extractor.extract_from_pdf(pdf_path)
            invoices.append(invoice)
        
        # Validate invoices
        validator = InvoiceValidator()
        report = validator.validate_invoices(invoices)
        
        return ExtractAndValidateResponse(
            extracted_invoices=invoices,
            validation_report=report
        )
        
    except Exception as e:
        logging.error(f"Extract and validate error: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    
    finally:
        # Cleanup temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)


@api_router.get("/validation-rules")
async def get_validation_rules():
    """
    Get information about all validation rules.
    
    Returns the list of rules with their descriptions.
    """
    from invoice_qc.rules import ALL_RULES
    
    rules_info = [
        {
            "name": rule.name,
            "description": rule.description,
            "severity": rule.severity
        }
        for rule in ALL_RULES
    ]
    
    return {"rules": rules_info}


# Store validation results in MongoDB
@api_router.post("/save-validation")
async def save_validation_result(report: ValidationReport):
    """
    Save a validation report to the database.
    
    Useful for tracking validation history and analytics.
    """
    doc = report.model_dump()
    doc['timestamp'] = datetime.now(timezone.utc).isoformat()
    doc['id'] = str(uuid.uuid4())
    
    await db.validation_reports.insert_one(doc)
    
    return {"id": doc['id'], "message": "Validation report saved"}


@api_router.get("/validation-history")
async def get_validation_history(limit: int = 10):
    """
    Get recent validation reports from the database.
    """
    reports = await db.validation_reports.find(
        {}, 
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    return {"reports": reports}


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
