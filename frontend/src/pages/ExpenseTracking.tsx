import { Receipt, DollarSign, TrendingDown, PieChart, Search, Download, FileSpreadsheet, FileText, Calendar, Upload, X, Loader2, Car } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { useState, useEffect } from "react";
import { vehiclesService, Vehicle } from "@/services/vehicles-service";
import { documentService } from "@/services/document-service";
import { useToast } from "@/hooks/use-toast";
import { useRegionalSettings } from "@/contexts/RegionalSettingsContext";
import { formatCurrency } from "@/lib/regional-utils";

interface Expense {
  id?: string;
  description: string;
  category: string;
  amount: number;
  date: string;
  vehicle: string;
  vehicleId?: number;
  documentId?: string;
}

const expenseCategories = [
  "Maintenance",
  "Insurance",
  "Fuel",
  "Cleaning",
  "Registration",
  "Repairs",
  "Other"
];

const ExpenseTracking = () => {
  const { currency } = useRegionalSettings();
  const { toast } = useToast();
  const [searchQuery, setSearchQuery] = useState("");
  const [dateRange, setDateRange] = useState("this-month");
  const [expenses, setExpenses] = useState<Expense[]>([
    { id: "1", description: "Oil Change - BMW X5", category: "Maintenance", amount: 180, date: "Today", vehicle: "BMW X5" },
    { id: "2", description: "Monthly Insurance Premium", category: "Insurance", amount: 2800, date: "Yesterday", vehicle: "All Vehicles" },
    { id: "3", description: "Brake Pad Replacement - Audi A4", category: "Maintenance", amount: 420, date: "Nov 18", vehicle: "Audi A4" },
    { id: "4", description: "Professional Detailing", category: "Cleaning", amount: 150, date: "Nov 17", vehicle: "Tesla Model 3" },
    { id: "5", description: "Supercharger - Tesla Model Y", category: "Fuel", amount: 45, date: "Nov 15", vehicle: "Tesla Model Y" },
  ]);
  
  // Add Expense Dialog State
  const [addExpenseOpen, setAddExpenseOpen] = useState(false);
  const [expenseTitle, setExpenseTitle] = useState("");
  const [expenseCategory, setExpenseCategory] = useState("");
  const [expenseVehicleId, setExpenseVehicleId] = useState<number | "all">("all");
  const [expenseAmount, setExpenseAmount] = useState("");
  const [expenseDate, setExpenseDate] = useState(new Date().toISOString().split('T')[0]);
  const [expenseFile, setExpenseFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [loadingVehicles, setLoadingVehicles] = useState(false);

  // Fetch vehicles on mount
  useEffect(() => {
    const loadVehicles = async () => {
      try {
        setLoadingVehicles(true);
        const response = await vehiclesService.getVehicles({ limit: 100 });
        setVehicles(response.vehicles || []);
      } catch (error) {
        console.error('Failed to load vehicles:', error);
        toast({
          title: "Error",
          description: "Failed to load vehicles. You can still add expenses without linking to a vehicle.",
          variant: "destructive",
        });
      } finally {
        setLoadingVehicles(false);
      }
    };
    loadVehicles();
  }, [toast]);

  const filteredExpenses = expenses.filter(expense => 
    expense.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
    expense.vehicle.toLowerCase().includes(searchQuery.toLowerCase()) ||
    expense.category.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleAddExpense = async () => {
    // Validation
    if (!expenseTitle.trim()) {
      toast({
        title: "Title required",
        description: "Please enter a title for the expense.",
        variant: "destructive",
      });
      return;
    }

    if (!expenseCategory) {
      toast({
        title: "Category required",
        description: "Please select a category for the expense.",
        variant: "destructive",
      });
      return;
    }

    if (!expenseAmount || parseFloat(expenseAmount) <= 0) {
      toast({
        title: "Amount required",
        description: "Please enter a valid amount greater than 0.",
        variant: "destructive",
      });
      return;
    }

    try {
      setUploading(true);
      let documentId: string | undefined;

      // Upload document if provided
      if (expenseFile) {
        try {
          const uploadedDoc = await documentService.uploadDocument({
            file: expenseFile,
            category: "other",
            vehicle_id: expenseVehicleId !== "all" ? expenseVehicleId : undefined,
            description: `Expense receipt: ${expenseTitle}`,
          });
          documentId = uploadedDoc.id.toString();
        } catch (error) {
          console.error('Failed to upload document:', error);
          toast({
            title: "Document upload failed",
            description: "The expense will be added without the document attachment.",
            variant: "destructive",
          });
        }
      }

      // Determine vehicle name
      let vehicleName = "All Vehicles";
      if (expenseVehicleId !== "all") {
        const vehicle = vehicles.find(v => v.id === expenseVehicleId);
        vehicleName = vehicle ? vehicle.name : "Unknown Vehicle";
      }

      // Format date
      const dateObj = new Date(expenseDate);
      const today = new Date();
      const yesterday = new Date(today);
      yesterday.setDate(yesterday.getDate() - 1);
      
      let formattedDate = "";
      if (dateObj.toDateString() === today.toDateString()) {
        formattedDate = "Today";
      } else if (dateObj.toDateString() === yesterday.toDateString()) {
        formattedDate = "Yesterday";
      } else {
        formattedDate = dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      }

      // Create new expense
      const newExpense: Expense = {
        id: Date.now().toString(),
        description: expenseTitle,
        category: expenseCategory,
        amount: parseFloat(expenseAmount),
        date: formattedDate,
        vehicle: vehicleName,
        vehicleId: expenseVehicleId !== "all" ? expenseVehicleId : undefined,
        documentId,
      };

      // Add to expenses list
      setExpenses([newExpense, ...expenses]);

      toast({
        title: "Expense added",
        description: "Your expense has been successfully added.",
      });

      // Reset form
      setExpenseTitle("");
      setExpenseCategory("");
      setExpenseVehicleId("all");
      setExpenseAmount("");
      setExpenseDate(new Date().toISOString().split('T')[0]);
      setExpenseFile(null);
      setAddExpenseOpen(false);
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to add expense.",
        variant: "destructive",
      });
    } finally {
      setUploading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        toast({
          title: "File too large",
          description: "Please select a file smaller than 10MB.",
          variant: "destructive",
        });
        return;
      }
      setExpenseFile(file);
    }
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="mx-auto max-w-[2000px] space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Expense Tracking</h1>
            <p className="text-sm text-muted-foreground">Monitor and manage fleet expenses</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button variant="outline" size="sm" className="gap-2">
              <FileSpreadsheet className="h-4 w-4" />
              CSV
            </Button>
            <Button variant="outline" size="sm" className="gap-2">
              <FileText className="h-4 w-4" />
              PDF
            </Button>
            <Button className="gap-2" onClick={() => setAddExpenseOpen(true)}>
              <Receipt className="h-4 w-4" />
              Add Expense
            </Button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search expenses..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
          <Select value={dateRange} onValueChange={setDateRange}>
            <SelectTrigger className="w-[180px]">
              <Calendar className="h-4 w-4 mr-2" />
              <SelectValue placeholder="Date range" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="today">Today</SelectItem>
              <SelectItem value="this-week">This Week</SelectItem>
              <SelectItem value="this-month">This Month</SelectItem>
              <SelectItem value="last-month">Last Month</SelectItem>
              <SelectItem value="this-year">This Year</SelectItem>
              <SelectItem value="all-time">All Time</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Expense Overview */}
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader>
              <CardTitle>Total Expenses</CardTitle>
              <CardDescription>This month</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-foreground">{formatCurrency(8450, currency)}</p>
              <p className="text-sm text-success flex items-center gap-1 mt-1">
                <TrendingDown className="h-4 w-4" />
                -5.3% from last month
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Maintenance</CardTitle>
              <CardDescription>Service costs</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-foreground">{formatCurrency(3240, currency)}</p>
              <p className="text-sm text-muted-foreground mt-1">38% of total</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Insurance</CardTitle>
              <CardDescription>Monthly premiums</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-foreground">{formatCurrency(2800, currency)}</p>
              <p className="text-sm text-muted-foreground mt-1">33% of total</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Other</CardTitle>
              <CardDescription>Misc expenses</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-foreground">{formatCurrency(2410, currency)}</p>
              <p className="text-sm text-muted-foreground mt-1">29% of total</p>
            </CardContent>
          </Card>
        </div>

        {/* Expense Categories */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PieChart className="h-5 w-5" />
              Expense Breakdown
            </CardTitle>
            <CardDescription>Spending by category</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                { category: "Maintenance & Repairs", amount: 3240, percentage: 38, color: "bg-blue-500" },
                { category: "Insurance Premiums", amount: 2800, percentage: 33, color: "bg-green-500" },
                { category: "Fuel & Charging", amount: 1450, percentage: 17, color: "bg-yellow-500" },
                { category: "Cleaning & Detailing", amount: 680, percentage: 8, color: "bg-purple-500" },
                { category: "Registration & Fees", amount: 280, percentage: 4, color: "bg-red-500" },
              ].map((item, idx) => (
                <div key={idx}>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3">
                      <div className={`w-3 h-3 rounded-full ${item.color}`} />
                      <span className="text-sm font-medium text-foreground">{item.category}</span>
                    </div>
                    <div className="text-right">
                      <span className="font-bold text-foreground">{formatCurrency(item.amount, currency)}</span>
                      <span className="text-sm text-muted-foreground ml-2">({item.percentage}%)</span>
                    </div>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${item.color}`} 
                      style={{ width: `${item.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Recent Expenses */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Expenses</CardTitle>
            <CardDescription>
              {filteredExpenses.length} transaction{filteredExpenses.length !== 1 ? 's' : ''} found
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {filteredExpenses.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <Receipt className="h-12 w-12 text-muted-foreground/50 mb-3" />
                  <p className="text-muted-foreground">No expenses found matching your search</p>
                </div>
              ) : (
                filteredExpenses.map((expense, idx) => (
                  <div key={idx} className="flex items-center justify-between p-4 border border-border rounded-lg hover:bg-muted/50 transition-colors">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <p className="font-medium text-foreground">{expense.description}</p>
                        <Badge variant="secondary">{expense.category}</Badge>
                      </div>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <span>{expense.vehicle}</span>
                        <span>•</span>
                        <span>{expense.date}</span>
                      </div>
                    </div>
                    <p className="font-bold text-destructive">-{formatCurrency(expense.amount, currency)}</p>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Add Expense Dialog */}
      <Dialog open={addExpenseOpen} onOpenChange={setAddExpenseOpen}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>Add New Expense</DialogTitle>
            <DialogDescription>
              Record a new expense for your fleet. All fields except documentation are required.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {/* Title */}
            <div className="space-y-2">
              <Label htmlFor="expense-title">
                Title <span className="text-destructive">*</span>
              </Label>
              <Input
                id="expense-title"
                placeholder="e.g., Oil Change - BMW X5"
                value={expenseTitle}
                onChange={(e) => setExpenseTitle(e.target.value)}
              />
            </div>

            {/* Category */}
            <div className="space-y-2">
              <Label htmlFor="expense-category">
                Category <span className="text-destructive">*</span>
              </Label>
              <Select value={expenseCategory} onValueChange={setExpenseCategory}>
                <SelectTrigger id="expense-category">
                  <SelectValue placeholder="Select a category" />
                </SelectTrigger>
                <SelectContent>
                  {expenseCategories.map((cat) => (
                    <SelectItem key={cat} value={cat}>
                      {cat}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Vehicle */}
            <div className="space-y-2">
              <Label htmlFor="expense-vehicle">
                Link to Vehicle <span className="text-destructive">*</span>
              </Label>
              <Select 
                value={expenseVehicleId === "all" ? "all" : expenseVehicleId.toString()} 
                onValueChange={(value) => setExpenseVehicleId(value === "all" ? "all" : parseInt(value))}
                disabled={loadingVehicles}
              >
                <SelectTrigger id="expense-vehicle">
                  <SelectValue placeholder={loadingVehicles ? "Loading vehicles..." : "Select a vehicle"} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Vehicles</SelectItem>
                  {vehicles.map((vehicle) => (
                    <SelectItem key={vehicle.id} value={vehicle.id.toString()}>
                      <div className="flex items-center gap-2">
                        <Car className="h-4 w-4" />
                        <span>{vehicle.name}</span>
                        {vehicle.year && <span className="text-muted-foreground">({vehicle.year})</span>}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Amount and Date */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="expense-amount">
                  Amount <span className="text-destructive">*</span>
                </Label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                    {currency === "cad" ? "CA$" : "$"}
                  </span>
                  <Input
                    id="expense-amount"
                    type="number"
                    step="0.01"
                    min="0"
                    placeholder="0.00"
                    value={expenseAmount}
                    onChange={(e) => setExpenseAmount(e.target.value)}
                    className="pl-8"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="expense-date">
                  Date <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="expense-date"
                  type="date"
                  value={expenseDate}
                  onChange={(e) => setExpenseDate(e.target.value)}
                />
              </div>
            </div>

            {/* File Upload */}
            <div className="space-y-2">
              <Label htmlFor="expense-file">
                Documentation (Optional)
              </Label>
              <div className="flex items-center gap-2">
                <Input
                  id="expense-file"
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
                  onChange={handleFileChange}
                  className="cursor-pointer"
                />
                {expenseFile && (
                  <div className="flex items-center gap-2 px-3 py-1.5 bg-muted rounded-md">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm text-foreground truncate max-w-[150px]">
                      {expenseFile.name}
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 w-6 p-0"
                      onClick={() => setExpenseFile(null)}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </div>
                )}
              </div>
              <p className="text-xs text-muted-foreground">
                Supported formats: PDF, JPG, PNG, DOC, DOCX (max 10MB)
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setAddExpenseOpen(false);
                setExpenseTitle("");
                setExpenseCategory("");
                setExpenseVehicleId("all");
                setExpenseAmount("");
                setExpenseDate(new Date().toISOString().split('T')[0]);
                setExpenseFile(null);
              }}
              disabled={uploading}
            >
              Cancel
            </Button>
            <Button onClick={handleAddExpense} disabled={uploading}>
              {uploading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Adding...
                </>
              ) : (
                <>
                  <Receipt className="mr-2 h-4 w-4" />
                  Add Expense
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ExpenseTracking;