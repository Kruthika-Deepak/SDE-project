import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";

const JSONInput = ({ onValidate, loading }) => {
  const [jsonText, setJsonText] = useState("");

  const handleValidate = () => {
    if (!jsonText.trim()) {
      toast.error("Please enter JSON data");
      return;
    }

    try {
      const data = JSON.parse(jsonText);
      
      // Check if it's an array
      if (!Array.isArray(data)) {
        toast.error("JSON must be an array of invoice objects");
        return;
      }

      onValidate(data);
    } catch (error) {
      toast.error("Invalid JSON format: " + error.message);
    }
  };

  const handleClear = () => {
    setJsonText("");
  };

  const sampleJSON = `[
  {
    "invoice_number": "INV-001",
    "invoice_date": "2024-01-10",
    "due_date": "2024-01-25",
    "seller_name": "ACME Corp",
    "buyer_name": "Example Inc",
    "currency": "USD",
    "net_total": 1000.00,
    "tax_amount": 180.00,
    "gross_total": 1180.00
  }
]`;

  return (
    <div className="space-y-4">
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="text-sm font-medium text-slate-700">Invoice JSON Data</label>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setJsonText(sampleJSON)}
            data-testid="load-sample-btn"
          >
            Load Sample
          </Button>
        </div>
        <Textarea
          value={jsonText}
          onChange={(e) => setJsonText(e.target.value)}
          placeholder="Paste your invoice JSON array here..."
          className="min-h-[300px] font-mono text-sm"
          data-testid="json-textarea"
        />
        <p className="text-xs text-slate-500 mt-2">
          Format: Array of invoice objects with fields like invoice_number, invoice_date, seller_name, buyer_name, currency, totals, etc.
        </p>
      </div>

      <div className="flex gap-3">
        <Button
          onClick={handleValidate}
          disabled={loading || !jsonText.trim()}
          className="flex-1 h-12 text-base"
          data-testid="validate-json-btn"
        >
          {loading ? "Validating..." : "Validate JSON"}
        </Button>
        {jsonText && (
          <Button
            onClick={handleClear}
            variant="outline"
            className="h-12"
            data-testid="clear-json-btn"
          >
            Clear
          </Button>
        )}
      </div>
    </div>
  );
};

export default JSONInput;
