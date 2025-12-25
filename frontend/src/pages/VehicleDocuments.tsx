import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText, Download, Calendar, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

interface Document {
  id: string;
  vehicleName: string;
  documentType: string;
  fileName: string;
  uploadDate: string;
  expiryDate?: string;
  status: "valid" | "expiring-soon" | "expired";
}

const documents: Document[] = [
  {
    id: "1",
    vehicleName: "Tesla Model 3",
    documentType: "Registration",
    fileName: "registration_tesla_2024.pdf",
    uploadDate: "Jan 15, 2024",
    expiryDate: "Jan 15, 2025",
    status: "valid",
  },
  {
    id: "2",
    vehicleName: "Tesla Model 3",
    documentType: "Insurance",
    fileName: "insurance_tesla.pdf",
    uploadDate: "Dec 1, 2023",
    expiryDate: "Dec 1, 2024",
    status: "expiring-soon",
  },
  {
    id: "3",
    vehicleName: "BMW X5",
    documentType: "Registration",
    fileName: "registration_bmw_2023.pdf",
    uploadDate: "Mar 10, 2023",
    expiryDate: "Mar 10, 2024",
    status: "expired",
  },
  {
    id: "4",
    vehicleName: "BMW X5",
    documentType: "Insurance",
    fileName: "insurance_bmw.pdf",
    uploadDate: "Feb 20, 2024",
    expiryDate: "Feb 20, 2025",
    status: "valid",
  },
  {
    id: "5",
    vehicleName: "Mercedes C-Class",
    documentType: "Registration",
    fileName: "registration_mercedes_2024.pdf",
    uploadDate: "Jan 5, 2024",
    expiryDate: "Jan 5, 2025",
    status: "valid",
  },
  {
    id: "6",
    vehicleName: "Mercedes C-Class",
    documentType: "Inspection Report",
    fileName: "inspection_mercedes_oct.pdf",
    uploadDate: "Oct 15, 2024",
    status: "valid",
  },
  {
    id: "7",
    vehicleName: "Audi A4",
    documentType: "Insurance",
    fileName: "insurance_audi.pdf",
    uploadDate: "Nov 1, 2024",
    expiryDate: "Nov 30, 2024",
    status: "expiring-soon",
  },
];

const VehicleDocuments = () => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case "valid":
        return "default";
      case "expiring-soon":
        return "secondary";
      case "expired":
        return "destructive";
      default:
        return "default";
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "valid":
        return "Valid";
      case "expiring-soon":
        return "Expiring Soon";
      case "expired":
        return "Expired";
      default:
        return status;
    }
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Vehicle Documents</h1>
            <p className="text-sm text-muted-foreground">Manage vehicle documentation and certifications</p>
          </div>
          <Button>
            <FileText className="h-4 w-4 mr-2" />
            Upload Document
          </Button>
        </div>

        <Card className="rounded-xl shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg">All Documents</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between p-4 rounded-lg border border-border hover:bg-accent/50 transition-colors"
                >
                  <div className="flex items-start gap-4 flex-1">
                    <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                      <FileText className="h-5 w-5 text-primary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <p className="font-semibold text-foreground">{doc.vehicleName}</p>
                        <Badge variant={getStatusColor(doc.status)}>
                          {getStatusText(doc.status)}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mb-1">{doc.documentType}</p>
                      <p className="text-xs text-muted-foreground">{doc.fileName}</p>
                      <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          Uploaded: {doc.uploadDate}
                        </span>
                        {doc.expiryDate && (
                          <span className="flex items-center gap-1">
                            <AlertCircle className="h-3 w-3" />
                            Expires: {doc.expiryDate}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <Button variant="ghost" size="icon">
                    <Download className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default VehicleDocuments;
