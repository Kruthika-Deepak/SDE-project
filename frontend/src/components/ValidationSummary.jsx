import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, XCircle, AlertTriangle, FileText } from "lucide-react";

const ValidationSummary = ({ summary }) => {
  const validationRate = summary.total_invoices > 0
    ? ((summary.valid_invoices / summary.total_invoices) * 100).toFixed(1)
    : 0;

  return (
    <Card className="shadow-lg border-0 bg-white" data-testid="validation-summary">
      <CardHeader>
        <CardTitle className="text-xl">Validation Summary</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          {/* Total */}
          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600 mb-1">Total Invoices</p>
                <p className="text-3xl font-bold text-slate-900" data-testid="total-invoices">
                  {summary.total_invoices}
                </p>
              </div>
              <FileText className="w-8 h-8 text-slate-400" />
            </div>
          </div>

          {/* Valid */}
          <div className="p-4 rounded-lg bg-emerald-50 border border-emerald-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-emerald-700 mb-1">Valid</p>
                <p className="text-3xl font-bold text-emerald-900" data-testid="valid-invoices">
                  {summary.valid_invoices}
                </p>
              </div>
              <CheckCircle2 className="w-8 h-8 text-emerald-500" />
            </div>
          </div>

          {/* Invalid */}
          <div className="p-4 rounded-lg bg-red-50 border border-red-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-red-700 mb-1">Invalid</p>
                <p className="text-3xl font-bold text-red-900" data-testid="invalid-invoices">
                  {summary.invalid_invoices}
                </p>
              </div>
              <XCircle className="w-8 h-8 text-red-500" />
            </div>
          </div>

          {/* Success Rate */}
          <div className="p-4 rounded-lg bg-blue-50 border border-blue-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-blue-700 mb-1">Success Rate</p>
                <p className="text-3xl font-bold text-blue-900" data-testid="success-rate">
                  {validationRate}%
                </p>
              </div>
              <div className="w-8 h-8 rounded-full bg-blue-200 flex items-center justify-center text-blue-700 font-bold">
                ✓
              </div>
            </div>
          </div>
        </div>

        {/* Error Breakdown */}
        {Object.keys(summary.error_counts).length > 0 && (
          <div className="mt-6">
            <h4 className="font-semibold text-slate-900 mb-3 flex items-center gap-2">
              <XCircle className="w-5 h-5 text-red-500" />
              Top Errors
            </h4>
            <div className="space-y-2">
              {Object.entries(summary.error_counts)
                .sort(([, a], [, b]) => b - a)
                .slice(0, 5)
                .map(([error, count]) => (
                  <div
                    key={error}
                    className="flex items-center justify-between p-3 bg-red-50 rounded-lg border border-red-100"
                    data-testid="error-item"
                  >
                    <span className="text-sm text-slate-700 flex-1">{error}</span>
                    <Badge variant="destructive" data-testid="error-count">{count}x</Badge>
                  </div>
                ))}
            </div>
          </div>
        )}

        {/* Warning Breakdown */}
        {Object.keys(summary.warning_counts).length > 0 && (
          <div className="mt-6">
            <h4 className="font-semibold text-slate-900 mb-3 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-500" />
              Warnings
            </h4>
            <div className="space-y-2">
              {Object.entries(summary.warning_counts)
                .sort(([, a], [, b]) => b - a)
                .slice(0, 5)
                .map(([warning, count]) => (
                  <div
                    key={warning}
                    className="flex items-center justify-between p-3 bg-amber-50 rounded-lg border border-amber-100"
                    data-testid="warning-item"
                  >
                    <span className="text-sm text-slate-700 flex-1">{warning}</span>
                    <Badge variant="outline" className="bg-amber-100 text-amber-700" data-testid="warning-count">
                      {count}x
                    </Badge>
                  </div>
                ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default ValidationSummary;
