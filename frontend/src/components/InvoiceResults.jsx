import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { CheckCircle2, XCircle, AlertTriangle, ChevronDown, ChevronUp } from "lucide-react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";

const InvoiceResults = ({ results, invoices }) => {
  const [filter, setFilter] = useState("all");
  const [expandedInvoices, setExpandedInvoices] = useState(new Set());

  const filteredResults = results.filter(result => {
    if (filter === "valid") return result.is_valid;
    if (filter === "invalid") return !result.is_valid;
    return true;
  });

  const toggleExpand = (invoiceId) => {
    const newExpanded = new Set(expandedInvoices);
    if (newExpanded.has(invoiceId)) {
      newExpanded.delete(invoiceId);
    } else {
      newExpanded.add(invoiceId);
    }
    setExpandedInvoices(newExpanded);
  };

  const getInvoiceData = (invoiceId) => {
    return invoices?.find(
      inv => (inv.invoice_number || inv.source_file || 'unknown') === invoiceId
    );
  };

  return (
    <Card className="shadow-lg border-0 bg-white" data-testid="invoice-results">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-xl">Invoice Details</CardTitle>
          <Select value={filter} onValueChange={setFilter}>
            <SelectTrigger className="w-48" data-testid="filter-select">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Invoices</SelectItem>
              <SelectItem value="valid">Valid Only</SelectItem>
              <SelectItem value="invalid">Invalid Only</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {filteredResults.length === 0 ? (
            <p className="text-center text-slate-500 py-8">No invoices match the current filter</p>
          ) : (
            filteredResults.map((result, idx) => {
              const isExpanded = expandedInvoices.has(result.invoice_id);
              const invoiceData = getInvoiceData(result.invoice_id);

              return (
                <Collapsible
                  key={idx}
                  open={isExpanded}
                  onOpenChange={() => toggleExpand(result.invoice_id)}
                >
                  <div
                    className={`border rounded-lg overflow-hidden ${
                      result.is_valid
                        ? 'border-emerald-200 bg-emerald-50'
                        : 'border-red-200 bg-red-50'
                    }`}
                    data-testid={`invoice-card-${idx}`}
                  >
                    <CollapsibleTrigger asChild>
                      <button className="w-full p-4 flex items-center justify-between hover:bg-white/50 transition-colors">
                        <div className="flex items-center gap-3">
                          {result.is_valid ? (
                            <CheckCircle2 className="w-5 h-5 text-emerald-600" data-testid="valid-icon" />
                          ) : (
                            <XCircle className="w-5 h-5 text-red-600" data-testid="invalid-icon" />
                          )}
                          <div className="text-left">
                            <p className="font-semibold text-slate-900" data-testid="invoice-id">
                              {result.invoice_id}
                            </p>
                            {invoiceData && (
                              <p className="text-xs text-slate-600">
                                {invoiceData.seller_name} → {invoiceData.buyer_name}
                              </p>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <Badge
                            variant={result.is_valid ? "success" : "destructive"}
                            className={result.is_valid ? "bg-emerald-600" : ""}
                            data-testid="status-badge"
                          >
                            {result.is_valid ? "Valid" : "Invalid"}
                          </Badge>
                          {result.errors.length > 0 && (
                            <Badge variant="outline" className="bg-red-100 text-red-700" data-testid="error-badge">
                              {result.errors.length} errors
                            </Badge>
                          )}
                          {result.warnings.length > 0 && (
                            <Badge variant="outline" className="bg-amber-100 text-amber-700" data-testid="warning-badge">
                              {result.warnings.length} warnings
                            </Badge>
                          )}
                          {isExpanded ? (
                            <ChevronUp className="w-5 h-5 text-slate-400" />
                          ) : (
                            <ChevronDown className="w-5 h-5 text-slate-400" />
                          )}
                        </div>
                      </button>
                    </CollapsibleTrigger>

                    <CollapsibleContent>
                      <div className="p-4 bg-white border-t space-y-4">
                        {/* Invoice Data */}
                        {invoiceData && (
                          <div>
                            <h4 className="font-semibold text-slate-900 mb-2">Invoice Information</h4>
                            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                              <div>
                                <span className="text-slate-600">Date:</span>
                                <span className="ml-2 font-medium text-slate-900">
                                  {invoiceData.invoice_date || 'N/A'}
                                </span>
                              </div>
                              <div>
                                <span className="text-slate-600">Due Date:</span>
                                <span className="ml-2 font-medium text-slate-900">
                                  {invoiceData.due_date || 'N/A'}
                                </span>
                              </div>
                              <div>
                                <span className="text-slate-600">Currency:</span>
                                <span className="ml-2 font-medium text-slate-900">
                                  {invoiceData.currency || 'N/A'}
                                </span>
                              </div>
                              <div>
                                <span className="text-slate-600">Net Total:</span>
                                <span className="ml-2 font-medium text-slate-900">
                                  {invoiceData.net_total?.toFixed(2) || 'N/A'}
                                </span>
                              </div>
                              <div>
                                <span className="text-slate-600">Tax:</span>
                                <span className="ml-2 font-medium text-slate-900">
                                  {invoiceData.tax_amount?.toFixed(2) || 'N/A'}
                                </span>
                              </div>
                              <div>
                                <span className="text-slate-600">Gross Total:</span>
                                <span className="ml-2 font-medium text-slate-900">
                                  {invoiceData.gross_total?.toFixed(2) || 'N/A'}
                                </span>
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Errors */}
                        {result.errors.length > 0 && (
                          <div>
                            <h4 className="font-semibold text-red-900 mb-2 flex items-center gap-2">
                              <XCircle className="w-4 h-4" />
                              Errors ({result.errors.length})
                            </h4>
                            <div className="space-y-2">
                              {result.errors.map((error, errorIdx) => (
                                <div
                                  key={errorIdx}
                                  className="p-3 bg-red-50 rounded border border-red-200"
                                  data-testid={`error-detail-${errorIdx}`}
                                >
                                  <div className="flex items-start gap-2">
                                    <Badge variant="destructive" className="text-xs">
                                      {error.rule}
                                    </Badge>
                                    <p className="text-sm text-slate-700 flex-1">{error.message}</p>
                                  </div>
                                  {error.field && (
                                    <p className="text-xs text-slate-500 mt-1">Field: {error.field}</p>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Warnings */}
                        {result.warnings.length > 0 && (
                          <div>
                            <h4 className="font-semibold text-amber-900 mb-2 flex items-center gap-2">
                              <AlertTriangle className="w-4 h-4" />
                              Warnings ({result.warnings.length})
                            </h4>
                            <div className="space-y-2">
                              {result.warnings.map((warning, warnIdx) => (
                                <div
                                  key={warnIdx}
                                  className="p-3 bg-amber-50 rounded border border-amber-200"
                                  data-testid={`warning-detail-${warnIdx}`}
                                >
                                  <div className="flex items-start gap-2">
                                    <Badge variant="outline" className="text-xs bg-amber-100 text-amber-700">
                                      {warning.rule}
                                    </Badge>
                                    <p className="text-sm text-slate-700 flex-1">{warning.message}</p>
                                  </div>
                                  {warning.field && (
                                    <p className="text-xs text-slate-500 mt-1">Field: {warning.field}</p>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Line Items */}
                        {invoiceData?.line_items && invoiceData.line_items.length > 0 && (
                          <div>
                            <h4 className="font-semibold text-slate-900 mb-2">Line Items</h4>
                            <div className="overflow-x-auto">
                              <table className="w-full text-sm">
                                <thead className="bg-slate-100">
                                  <tr>
                                    <th className="p-2 text-left">Description</th>
                                    <th className="p-2 text-right">Qty</th>
                                    <th className="p-2 text-right">Unit Price</th>
                                    <th className="p-2 text-right">Total</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {invoiceData.line_items.map((item, itemIdx) => (
                                    <tr key={itemIdx} className="border-t">
                                      <td className="p-2">{item.description || 'N/A'}</td>
                                      <td className="p-2 text-right">{item.quantity || 'N/A'}</td>
                                      <td className="p-2 text-right">
                                        {item.unit_price?.toFixed(2) || 'N/A'}
                                      </td>
                                      <td className="p-2 text-right font-medium">
                                        {item.line_total?.toFixed(2) || 'N/A'}
                                      </td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        )}
                      </div>
                    </CollapsibleContent>
                  </div>
                </Collapsible>
              );
            })
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default InvoiceResults;
