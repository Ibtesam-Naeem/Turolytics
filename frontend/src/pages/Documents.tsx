import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { 
  FileText, 
  Download, 
  Trash2, 
  Shield, 
  Car, 
  Wrench, 
  Receipt, 
  Search,
  AlertTriangle,
  CheckCircle,
  Clock,
  Plus,
  Filter,
  MoreHorizontal,
  FolderOpen,
  Upload,
  Loader2,
  X,
  Folder
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import { documentService, DocumentCategory } from "@/services/document-service";
import { useToast } from "@/hooks/use-toast";

interface Document {
  id: string;
  name: string;
  vehicle: string;
  size: string;
  uploadDate: string;
  expiryDate?: string;
  status: "valid" | "expiring" | "expired";
}

const insuranceDocs: Document[] = [
  { id: "1", name: "Full Coverage Policy", vehicle: "2024 Tesla Model 3", size: "2.4 MB", uploadDate: "Nov 15, 2025", expiryDate: "Mar 15, 2026", status: "valid" },
  { id: "2", name: "Liability Insurance", vehicle: "2023 BMW X5", size: "1.8 MB", uploadDate: "Nov 10, 2025", expiryDate: "Dec 20, 2025", status: "expiring" },
  { id: "3", name: "Comprehensive Policy", vehicle: "2024 Mercedes-Benz GLE", size: "2.1 MB", uploadDate: "Oct 20, 2025", expiryDate: "Jan 20, 2026", status: "valid" },
  { id: "4", name: "Full Coverage Policy", vehicle: "2023 Audi Q7", size: "2.0 MB", uploadDate: "Sep 15, 2025", expiryDate: "Nov 10, 2025", status: "expired" },
  { id: "5", name: "Commercial Auto Insurance", vehicle: "2024 Porsche Cayenne", size: "2.3 MB", uploadDate: "Oct 5, 2025", expiryDate: "Apr 5, 2026", status: "valid" },
  { id: "6", name: "Fleet Insurance Policy", vehicle: "2024 Land Rover Defender", size: "3.1 MB", uploadDate: "Sep 1, 2025", expiryDate: "Mar 1, 2026", status: "valid" },
  { id: "7", name: "Comprehensive Coverage", vehicle: "2023 Honda Accord", size: "1.9 MB", uploadDate: "Nov 1, 2025", expiryDate: "May 1, 2026", status: "valid" },
  { id: "8", name: "Full Coverage Policy", vehicle: "2024 Chevrolet Tahoe", size: "2.2 MB", uploadDate: "Oct 15, 2025", expiryDate: "Dec 15, 2025", status: "expiring" },
  { id: "9", name: "Liability Insurance", vehicle: "2023 Subaru Outback", size: "1.7 MB", uploadDate: "Aug 20, 2025", expiryDate: "Feb 20, 2026", status: "valid" },
  { id: "10", name: "Commercial Policy", vehicle: "2024 Ford F-150", size: "2.5 MB", uploadDate: "Jul 10, 2025", expiryDate: "Jan 10, 2026", status: "valid" },
];

const registrationDocs: Document[] = [
  { id: "11", name: "Vehicle Registration", vehicle: "2024 Tesla Model 3", size: "856 KB", uploadDate: "Nov 1, 2025", expiryDate: "Nov 1, 2026", status: "valid" },
  { id: "12", name: "Vehicle Registration", vehicle: "2023 BMW X5", size: "912 KB", uploadDate: "Oct 15, 2025", expiryDate: "Oct 15, 2026", status: "valid" },
  { id: "13", name: "Vehicle Registration", vehicle: "2024 Mercedes-Benz GLE", size: "780 KB", uploadDate: "Aug 20, 2025", expiryDate: "Dec 1, 2025", status: "expiring" },
  { id: "14", name: "Vehicle Title", vehicle: "2023 Audi Q7", size: "1.2 MB", uploadDate: "Jul 10, 2025", status: "valid" },
  { id: "15", name: "Vehicle Registration", vehicle: "2024 Porsche Cayenne", size: "890 KB", uploadDate: "Sep 5, 2025", expiryDate: "Sep 5, 2026", status: "valid" },
  { id: "16", name: "Vehicle Registration", vehicle: "2024 Land Rover Defender", size: "945 KB", uploadDate: "Oct 1, 2025", expiryDate: "Oct 1, 2026", status: "valid" },
  { id: "17", name: "Vehicle Title", vehicle: "2023 Honda Accord", size: "1.1 MB", uploadDate: "Jun 15, 2025", status: "valid" },
  { id: "18", name: "Vehicle Registration", vehicle: "2024 Chevrolet Tahoe", size: "875 KB", uploadDate: "Nov 10, 2025", expiryDate: "Nov 10, 2026", status: "valid" },
  { id: "19", name: "Vehicle Registration", vehicle: "2023 Subaru Outback", size: "820 KB", uploadDate: "Aug 1, 2025", expiryDate: "Aug 1, 2026", status: "valid" },
  { id: "20", name: "Vehicle Registration", vehicle: "2024 Ford F-150", size: "910 KB", uploadDate: "Jul 20, 2025", expiryDate: "Jul 20, 2026", status: "valid" },
  { id: "21", name: "Vehicle Title", vehicle: "2024 Tesla Model Y", size: "1.3 MB", uploadDate: "Jan 15, 2024", status: "valid" },
  { id: "22", name: "Vehicle Registration", vehicle: "2024 Mercedes C-Class", size: "765 KB", uploadDate: "Sep 20, 2025", expiryDate: "Sep 20, 2026", status: "valid" },
];

const maintenanceDocs: Document[] = [
  { id: "23", name: "Oil Change Receipt", vehicle: "2024 Tesla Model 3", size: "456 KB", uploadDate: "Nov 20, 2025", status: "valid" },
  { id: "24", name: "Brake Service Invoice", vehicle: "2023 BMW X5", size: "1.1 MB", uploadDate: "Nov 18, 2025", status: "valid" },
  { id: "25", name: "Tire Rotation Receipt", vehicle: "2024 Mercedes-Benz GLE", size: "380 KB", uploadDate: "Nov 15, 2025", status: "valid" },
  { id: "26", name: "Annual Inspection", vehicle: "2023 Audi Q7", size: "2.3 MB", uploadDate: "Nov 10, 2025", status: "valid" },
  { id: "27", name: "Battery Replacement", vehicle: "2024 Tesla Model 3", size: "520 KB", uploadDate: "Oct 28, 2025", status: "valid" },
  { id: "28", name: "Transmission Service", vehicle: "2024 Porsche Cayenne", size: "1.4 MB", uploadDate: "Nov 5, 2025", status: "valid" },
  { id: "29", name: "AC System Repair", vehicle: "2024 Land Rover Defender", size: "980 KB", uploadDate: "Oct 25, 2025", status: "valid" },
  { id: "30", name: "Wheel Alignment", vehicle: "2023 Honda Accord", size: "420 KB", uploadDate: "Nov 12, 2025", status: "valid" },
  { id: "31", name: "Engine Diagnostic", vehicle: "2024 Chevrolet Tahoe", size: "1.2 MB", uploadDate: "Oct 30, 2025", status: "valid" },
  { id: "32", name: "Tire Replacement", vehicle: "2023 Subaru Outback", size: "1.6 MB", uploadDate: "Nov 8, 2025", status: "valid" },
  { id: "33", name: "Coolant Flush", vehicle: "2024 Ford F-150", size: "510 KB", uploadDate: "Oct 18, 2025", status: "valid" },
  { id: "34", name: "Spark Plug Replacement", vehicle: "2024 Mercedes C-Class", size: "640 KB", uploadDate: "Nov 3, 2025", status: "valid" },
  { id: "35", name: "Windshield Replacement", vehicle: "2024 Tesla Model Y", size: "2.1 MB", uploadDate: "Oct 12, 2025", status: "valid" },
  { id: "36", name: "Suspension Repair", vehicle: "2024 Porsche 911", size: "1.8 MB", uploadDate: "Sep 28, 2025", status: "valid" },
];

const receiptsDocs: Document[] = [
  { id: "37", name: "Gas Receipt - Shell", vehicle: "2023 BMW X5", size: "245 KB", uploadDate: "Nov 18, 2025", status: "valid" },
  { id: "38", name: "Gas Receipt - Chevron", vehicle: "2024 Mercedes-Benz GLE", size: "198 KB", uploadDate: "Nov 15, 2025", status: "valid" },
  { id: "39", name: "Gas Receipt - BP", vehicle: "2024 Porsche Cayenne", size: "267 KB", uploadDate: "Nov 12, 2025", status: "valid" },
  { id: "40", name: "Gas Receipt - Mobil", vehicle: "2024 Land Rover Defender", size: "223 KB", uploadDate: "Nov 10, 2025", status: "valid" },
  { id: "41", name: "Gas Receipt - Exxon", vehicle: "2023 Honda Accord", size: "189 KB", uploadDate: "Nov 8, 2025", status: "valid" },
  { id: "42", name: "Gas Receipt - Shell", vehicle: "2024 Chevrolet Tahoe", size: "256 KB", uploadDate: "Nov 5, 2025", status: "valid" },
  { id: "43", name: "Gas Receipt - Chevron", vehicle: "2023 Subaru Outback", size: "201 KB", uploadDate: "Nov 3, 2025", status: "valid" },
  { id: "44", name: "Gas Receipt - Costco", vehicle: "2024 Ford F-150", size: "178 KB", uploadDate: "Nov 1, 2025", status: "valid" },
  { id: "45", name: "Parking Ticket - LAX", vehicle: "2024 Tesla Model 3", size: "312 KB", uploadDate: "Oct 28, 2025", status: "valid" },
  { id: "46", name: "Parking Receipt - SFO", vehicle: "2023 BMW X5", size: "298 KB", uploadDate: "Oct 25, 2025", status: "valid" },
  { id: "47", name: "Toll Receipt - Golden Gate Bridge", vehicle: "2024 Mercedes-Benz GLE", size: "156 KB", uploadDate: "Oct 22, 2025", status: "valid" },
  { id: "48", name: "Toll Receipt - Bay Bridge", vehicle: "2024 Porsche Cayenne", size: "142 KB", uploadDate: "Oct 20, 2025", status: "valid" },
  { id: "49", name: "Parking Ticket - Downtown SF", vehicle: "2024 Land Rover Defender", size: "289 KB", uploadDate: "Oct 18, 2025", status: "valid" },
  { id: "50", name: "Gas Receipt - Shell", vehicle: "2023 Honda Accord", size: "234 KB", uploadDate: "Oct 15, 2025", status: "valid" },
  { id: "51", name: "Toll Receipt - I-405", vehicle: "2024 Chevrolet Tahoe", size: "167 KB", uploadDate: "Oct 12, 2025", status: "valid" },
  { id: "52", name: "Parking Receipt - Airport", vehicle: "2023 Subaru Outback", size: "301 KB", uploadDate: "Oct 10, 2025", status: "valid" },
  { id: "53", name: "Gas Receipt - 76", vehicle: "2024 Ford F-150", size: "212 KB", uploadDate: "Oct 8, 2025", status: "valid" },
  { id: "54", name: "Toll Receipt - SR-520", vehicle: "2024 Tesla Model Y", size: "148 KB", uploadDate: "Oct 5, 2025", status: "valid" },
  { id: "55", name: "Parking Ticket - Seattle", vehicle: "2024 Mercedes C-Class", size: "275 KB", uploadDate: "Oct 3, 2025", status: "valid" },
  { id: "56", name: "Gas Receipt - Arco", vehicle: "2024 Porsche 911", size: "198 KB", uploadDate: "Oct 1, 2025", status: "valid" },
];

// Combine all documents for "All" category
const allDocs = [...insuranceDocs, ...registrationDocs, ...maintenanceDocs, ...receiptsDocs];

const categories = [
  { id: "all", label: "All", icon: Folder, docs: allDocs },
  { id: "insurance", label: "Insurance", icon: Shield, docs: insuranceDocs },
  { id: "registration", label: "Registration", icon: Car, docs: registrationDocs },
  { id: "maintenance", label: "Maintenance", icon: Wrench, docs: maintenanceDocs },
  { id: "receipts", label: "Receipts", icon: Receipt, docs: receiptsDocs },
];

const getStatusIndicator = (status: Document["status"]) => {
  switch (status) {
    case "valid":
      return <CheckCircle className="h-4 w-4 text-success" />;
    case "expiring":
      return <Clock className="h-4 w-4 text-warning" />;
    case "expired":
      return <AlertTriangle className="h-4 w-4 text-destructive" />;
  }
};

const Documents = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchQuery, setSearchQuery] = useState("");
  const [activeCategory, setActiveCategory] = useState("all");
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadCategory, setUploadCategory] = useState<DocumentCategory>("other");
  const [uploadDescription, setUploadDescription] = useState("");
  const [uploadVehicleId, setUploadVehicleId] = useState<number | undefined>(undefined);
  const { toast } = useToast();

  // Get vehicle filter from URL params
  const vehicleFilter = searchParams.get("vehicle");

  // Set active category based on vehicle filter on mount
  useEffect(() => {
    if (vehicleFilter) {
      // If vehicle filter is present, show "All" category filtered by vehicle
      setActiveCategory("all");
    }
  }, [vehicleFilter]);

  // Calculate stats based on filtered documents if vehicle filter is active
  const docsForStats = vehicleFilter 
    ? allDocs.filter(doc => {
        const vehicleNameLower = vehicleFilter.toLowerCase();
        const docVehicleLower = doc.vehicle.toLowerCase();
        return docVehicleLower.includes(vehicleNameLower) || vehicleNameLower.includes(docVehicleLower.split(' ').slice(1).join(' '));
      })
    : allDocs;
  
  const expiringCount = docsForStats.filter(d => d.status === "expiring").length;
  const expiredCount = docsForStats.filter(d => d.status === "expired").length;
  const totalDocs = vehicleFilter ? docsForStats.length : allDocs.length;

  const currentCategory = categories.find(c => c.id === activeCategory);
  
  // Filter documents by category, search query, and vehicle filter
  const filteredDocs = (currentCategory?.docs || []).filter((doc) => {
    // First filter by vehicle if vehicle filter is present
    if (vehicleFilter) {
      // Match vehicle name - handle cases where vehicle name might be "Porsche 911" but doc has "2024 Porsche 911"
      const vehicleNameLower = vehicleFilter.toLowerCase();
      const docVehicleLower = doc.vehicle.toLowerCase();
      const vehicleMatches = docVehicleLower.includes(vehicleNameLower) || vehicleNameLower.includes(docVehicleLower.split(' ').slice(1).join(' '));
      if (!vehicleMatches) return false;
    }
    
    // Then filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      return (
        doc.name.toLowerCase().includes(query) ||
        doc.vehicle.toLowerCase().includes(query)
      );
    }
    
    return true;
  });

  const handleUploadDocument = async () => {
    if (!selectedFile) {
      toast({
        title: "No file selected",
        description: "Please select a file to upload.",
        variant: "destructive",
      });
      return;
    }

    try {
      setUploading(true);
      await documentService.uploadDocument({
        file: selectedFile,
        category: uploadCategory,
        vehicle_id: uploadVehicleId,
        description: uploadDescription || undefined,
      });

      toast({
        title: "Upload successful",
        description: "Your document has been uploaded successfully.",
      });

      setUploadDialogOpen(false);
      setSelectedFile(null);
      setUploadDescription("");
      setUploadCategory("other");
      setUploadVehicleId(undefined);
      
      // TODO: Refresh document list
    } catch (error) {
      toast({
        title: "Upload failed",
        description: error instanceof Error ? error.message : "Failed to upload document.",
        variant: "destructive",
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="flex h-screen">
        {/* Sidebar */}
        <div className="w-64 border-r border-border bg-card/50 flex flex-col">
          {/* Sidebar Header */}
          <div className="p-4 border-b border-border">
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1">
                <h1 className="text-lg font-semibold text-foreground">Documents</h1>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {vehicleFilter ? `Filtered: ${vehicleFilter}` : `${totalDocs} files`}
                </p>
              </div>
              {vehicleFilter && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6"
                  onClick={() => {
                    setSearchParams({});
                    setActiveCategory("all");
                  }}
                  title="Clear vehicle filter"
                >
                  <X className="h-3.5 w-3.5" />
                </Button>
              )}
            </div>
          </div>

          {/* Quick Stats */}
          <div className="p-3 border-b border-border">
            <div className="grid grid-cols-2 gap-2">
              <div className="p-2.5 rounded-lg bg-success/10 border border-success/20">
                <div className="flex items-center gap-1.5">
                  <CheckCircle className="h-3.5 w-3.5 text-success" />
                  <span className="text-xs font-medium text-success">Valid</span>
                </div>
                <p className="text-lg font-semibold text-foreground mt-1">
                  {totalDocs - expiringCount - expiredCount}
                </p>
              </div>
              <div className="p-2.5 rounded-lg bg-warning/10 border border-warning/20">
                <div className="flex items-center gap-1.5">
                  <Clock className="h-3.5 w-3.5 text-warning" />
                  <span className="text-xs font-medium text-warning">Expiring</span>
                </div>
                <p className="text-lg font-semibold text-foreground mt-1">{expiringCount}</p>
              </div>
            </div>
            {expiredCount > 0 && (
              <div className="mt-2 p-2.5 rounded-lg bg-destructive/10 border border-destructive/20">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <AlertTriangle className="h-3.5 w-3.5 text-destructive" />
                    <span className="text-xs font-medium text-destructive">{expiredCount} Expired</span>
                  </div>
                  <Button variant="ghost" size="sm" className="h-6 text-xs text-destructive hover:text-destructive">
                    View
                  </Button>
                </div>
              </div>
            )}
          </div>

          {/* Categories */}
          <div className="flex-1 p-3">
            <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider mb-2 px-2">
              Categories
            </p>
            <nav className="space-y-1">
              {categories.map((category) => {
                const Icon = category.icon;
                const isActive = activeCategory === category.id;
                return (
                  <button
                    key={category.id}
                    onClick={() => setActiveCategory(category.id)}
                    className={cn(
                      "w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors",
                      isActive 
                        ? "bg-primary text-primary-foreground" 
                        : "text-muted-foreground hover:bg-muted hover:text-foreground"
                    )}
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon className="h-4 w-4" />
                      <span>{category.label}</span>
                    </div>
                    <Badge 
                      variant="secondary" 
                      className={cn(
                        "h-5 min-w-[20px] px-1.5 text-xs",
                        isActive && "bg-primary-foreground/20 text-primary-foreground"
                      )}
                    >
                      {category.docs.length}
                    </Badge>
                  </button>
                );
              })}
            </nav>
          </div>

        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          {/* Toolbar */}
          <div className="h-14 border-b border-border flex items-center justify-between px-4 bg-card/30">
            <div className="flex items-center gap-3">
              {currentCategory && (
                <div className="flex items-center gap-2">
                  <currentCategory.icon className="h-5 w-5 text-primary" />
                  <h2 className="font-medium text-foreground">{currentCategory.label}</h2>
                </div>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Button 
                className="gap-2" 
                size="sm"
                onClick={() => setUploadDialogOpen(true)}
              >
                <Upload className="h-4 w-4" />
                Upload Document
              </Button>
              <div className="relative">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-8 h-9 w-56 bg-background"
                />
              </div>
              <Button variant="outline" size="sm" className="gap-1.5">
                <Filter className="h-3.5 w-3.5" />
                Filter
              </Button>
            </div>
          </div>

          {/* Document Grid */}
          <ScrollArea className="flex-1 p-4">
            {filteredDocs.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
                <FolderOpen className="h-12 w-12 mb-3 opacity-40" />
                <p className="font-medium">No documents found</p>
                <p className="text-sm mt-1">Try adjusting your search</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                {filteredDocs.map((doc) => (
                  <div
                    key={doc.id}
                    className="group relative p-4 bg-card border border-border rounded-xl hover:border-primary/50 hover:shadow-lg hover:shadow-primary/5 transition-all duration-200 cursor-pointer"
                  >
                    {/* Status Indicator */}
                    {doc.expiryDate && (
                      <div className="absolute top-3 right-3">
                        {getStatusIndicator(doc.status)}
                      </div>
                    )}

                    {/* File Icon */}
                    <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mb-3">
                      <FileText className="h-6 w-6 text-primary" />
                    </div>

                    {/* Document Info */}
                    <h3 className="font-medium text-foreground text-sm truncate pr-6">
                      {doc.name}
                    </h3>
                    <p className="text-xs text-muted-foreground mt-1 truncate">
                      {doc.vehicle}
                    </p>

                    {/* Meta */}
                    <div className="flex items-center gap-2 mt-3 text-xs text-muted-foreground">
                      <span>{doc.size}</span>
                      <span>•</span>
                      <span>{doc.uploadDate}</span>
                    </div>

                    {/* Expiry */}
                    {doc.expiryDate && (
                      <div className={cn(
                        "mt-3 text-xs font-medium",
                        doc.status === "valid" && "text-muted-foreground",
                        doc.status === "expiring" && "text-warning",
                        doc.status === "expired" && "text-destructive"
                      )}>
                        {doc.status === "expired" ? "Expired" : "Expires"} {doc.expiryDate}
                      </div>
                    )}

                    {/* Actions - Show on Hover */}
                    <div className="absolute bottom-3 right-3 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Button variant="ghost" size="icon" className="h-7 w-7">
                        <Download className="h-3.5 w-3.5" />
                      </Button>
                      <Button variant="ghost" size="icon" className="h-7 w-7">
                        <MoreHorizontal className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </div>
      </div>

      {/* Upload Document Dialog */}
      <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Upload Document</DialogTitle>
            <DialogDescription>
              Upload a document to store in your account. Supported formats: PDF, images, and common document types.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {/* File Input */}
            <div className="space-y-2">
              <Label htmlFor="file-upload">File</Label>
              <div className="flex items-center gap-2">
                <Input
                  id="file-upload"
                  type="file"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) {
                      setSelectedFile(file);
                    }
                  }}
                  className="cursor-pointer"
                />
                {selectedFile && (
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setSelectedFile(null)}
                    className="h-8 w-8"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
              {selectedFile && (
                <p className="text-sm text-muted-foreground">
                  Selected: {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
                </p>
              )}
            </div>

            {/* Category */}
            <div className="space-y-2">
              <Label htmlFor="category">Category</Label>
              <Select value={uploadCategory} onValueChange={(v) => setUploadCategory(v as DocumentCategory)}>
                <SelectTrigger id="category">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="insurance">Insurance</SelectItem>
                  <SelectItem value="registration">Registration</SelectItem>
                  <SelectItem value="maintenance">Maintenance</SelectItem>
                  <SelectItem value="repair">Repair</SelectItem>
                  <SelectItem value="inspection">Inspection</SelectItem>
                  <SelectItem value="gas_receipt">Gas Receipt</SelectItem>
                  <SelectItem value="parking_ticket">Parking Ticket</SelectItem>
                  <SelectItem value="toll_booth">Toll Booth</SelectItem>
                  <SelectItem value="business_expense">Business Expense</SelectItem>
                  <SelectItem value="other">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="description">Description (Optional)</Label>
              <Textarea
                id="description"
                placeholder="Add a description or notes about this document..."
                value={uploadDescription}
                onChange={(e) => setUploadDescription(e.target.value)}
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setUploadDialogOpen(false);
              setSelectedFile(null);
              setUploadDescription("");
              setUploadCategory("other");
            }}>
              Cancel
            </Button>
            <Button 
              onClick={handleUploadDocument} 
              disabled={!selectedFile || uploading}
            >
              {uploading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="mr-2 h-4 w-4" />
                  Upload
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Documents;
