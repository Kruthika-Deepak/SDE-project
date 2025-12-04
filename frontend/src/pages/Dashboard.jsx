import { useState } from "react";
import { Upload, FileJson, CheckCircle2, AlertCircle, Info } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import axios from "axios";
import InvoiceResults from "@/components/InvoiceResults";
import ValidationSummary from "@/components/ValidationSummary";
import JSONInput from "@/components/JSONInput";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Dashboard = () => {
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [validationReport, setValidationReport] = useState(null);
  const [extractedInvoices, setExtractedInvoices] = useState(null);

  const handleFileUpload = (e) => {
    const files = Array.from(e.target.files);
    const pdfFiles = files.filter(file => file.name.toLowerCase().endsWith('.pdf'));
    
    if (pdfFiles.length !== files.length) {
      toast.error("Only PDF files are allowed");
    }
    
    setUploadedFiles(pdfFiles);
  };

  const handleExtractAndValidate = async () => {
    if (uploadedFiles.length === 0) {
      toast.error("Please upload at least one PDF file");
      return;
    }

    setLoading(true);
    const formData = new FormData();
    
    uploadedFiles.forEach(file => {
      formData.append('files', file);
    });

    try {
      const response = await axios.post(
        `${API}/extract-and-validate`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      setExtractedInvoices(response.data.extracted_invoices);
      setValidationReport(response.data.validation_report);
      
      const valid = response.data.validation_report.summary.valid_invoices;
      const total = response.data.validation_report.summary.total_invoices;
      
      if (valid === total) {
        toast.success(`All ${total} invoices validated successfully!`);
      } else {
        toast.warning(`${valid}/${total} invoices passed validation`);
      }
    } catch (error) {
      console.error('Error:', error);
      toast.error(error.response?.data?.detail || "Failed to process invoices");
    } finally {
      setLoading(false);
    }
  };

  const handleJSONValidation = async (invoicesData) => {
    setLoading(true);

    try {
      const response = await axios.post(
        `${API}/validate-json`,
        { invoices: invoicesData }
      );

      setValidationReport(response.data);
      setExtractedInvoices(invoicesData);
      
      const valid = response.data.summary.valid_invoices;
      const total = response.data.summary.total_invoices;
      
      if (valid === total) {
        toast.success(`All ${total} invoices validated successfully!`);
      } else {
        toast.warning(`${valid}/${total} invoices passed validation`);
      }
    } catch (error) {
      console.error('Error:', error);
      toast.error(error.response?.data?.detail || "Failed to validate JSON");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setUploadedFiles([]);
    setValidationReport(null);
    setExtractedInvoices(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-lg sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-600 to-cyan-500 flex items-center justify-center">
                <CheckCircle2 className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-900" data-testid="app-title">Invoice QC Console</h1>
                <p className="text-sm text-slate-600">Quality Control & Validation System</p>
              </div>
            </div>
            <Badge variant="outline" className="px-3 py-1">
              <Info className="w-3 h-3 mr-1" />
              v1.0.0
            </Badge>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <Card className="shadow-xl border-0 bg-white/90 backdrop-blur">
          <CardHeader>
            <CardTitle className="text-2xl" data-testid="card-title">Process Invoices</CardTitle>
            <CardDescription>
              Upload PDF invoices or paste JSON data for extraction and validation
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="upload" className="w-full">
              <TabsList className="grid w-full grid-cols-2 mb-6">
                <TabsTrigger value="upload" data-testid="upload-tab">
                  <Upload className="w-4 h-4 mr-2" />
                  Upload PDFs
                </TabsTrigger>
                <TabsTrigger value="json" data-testid="json-tab">
                  <FileJson className="w-4 h-4 mr-2" />
                  Paste JSON
                </TabsTrigger>
              </TabsList>

              {/* PDF Upload Tab */}
              <TabsContent value="upload" className="space-y-6">
                <div className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center hover:border-blue-400 transition-colors">
                  <input
                    type="file"
                    multiple
                    accept=".pdf"
                    onChange={handleFileUpload}
                    className="hidden"
                    id="file-upload"
                    data-testid="file-input"
                  />
                  <label
                    htmlFor="file-upload"
                    className="cursor-pointer flex flex-col items-center gap-3"
                  >
                    <div className="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center">
                      <Upload className="w-8 h-8 text-blue-600" />
                    </div>
                    <div>
                      <p className="text-lg font-medium text-slate-900">Drop PDF files here or click to browse</p>
                      <p className="text-sm text-slate-500 mt-1">Support for multiple invoice PDFs</p>
                    </div>
                  </label>
                </div>

                {uploadedFiles.length > 0 && (
                  <div className="space-y-2" data-testid="uploaded-files-list">
                    <h3 className="font-medium text-slate-900">Uploaded Files ({uploadedFiles.length})</h3>
                    <div className="space-y-2 max-h-40 overflow-y-auto">
                      {uploadedFiles.map((file, idx) => (
                        <div
                          key={idx}
                          className="flex items-center gap-2 p-3 bg-slate-50 rounded-lg"
                          data-testid={`uploaded-file-${idx}`}
                        >
                          <FileJson className="w-4 h-4 text-blue-600" />
                          <span className="text-sm text-slate-700 flex-1">{file.name}</span>
                          <span className="text-xs text-slate-500">
                            {(file.size / 1024).toFixed(1)} KB
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="flex gap-3">
                  <Button
                    onClick={handleExtractAndValidate}
                    disabled={loading || uploadedFiles.length === 0}
                    className="flex-1 h-12 text-base"
                    data-testid="extract-validate-btn"
                  >
                    {loading ? "Processing..." : "Extract & Validate"}
                  </Button>
                  {(uploadedFiles.length > 0 || validationReport) && (
                    <Button
                      onClick={handleReset}
                      variant="outline"
                      className="h-12"
                      data-testid="reset-btn"
                    >
                      Reset
                    </Button>
                  )}
                </div>
              </TabsContent>

              {/* JSON Input Tab */}
              <TabsContent value="json">
                <JSONInput onValidate={handleJSONValidation} loading={loading} />
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        {/* Results */}
        {validationReport && (
          <div className="mt-8 space-y-6" data-testid="validation-results">
            <ValidationSummary summary={validationReport.summary} />
            <InvoiceResults
              results={validationReport.results}
              invoices={extractedInvoices}
            />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t bg-white/80 backdrop-blur-lg mt-12">
        <div className="container mx-auto px-4 py-6 text-center text-sm text-slate-600">
          <p>Invoice Quality Control Service © 2025 | Built for Software Engineer Intern Assignment</p>
        </div>
      </footer>
    </div>
  );
};

export default Dashboard;
