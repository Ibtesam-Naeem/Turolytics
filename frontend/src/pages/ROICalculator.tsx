import { useState, useEffect, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  Tooltip, 
  TooltipContent, 
  TooltipProvider, 
  TooltipTrigger 
} from "@/components/ui/tooltip";
import { toast } from "sonner";
import { useRegionalSettings } from "@/contexts/RegionalSettingsContext";
import { formatCurrency } from "@/lib/regional-utils";
import { roiService, ROICalculation } from "@/services/roi-service";
import { 
  Calculator, 
  DollarSign, 
  Car, 
  TrendingUp, 
  Clock, 
  Percent, 
  PiggyBank,
  BarChart3,
  CalendarDays,
  Target,
  Info,
  Bookmark,
  Trash2,
  Search,
  Loader2,
  AlertCircle,
  X,
  CheckCircle2,
  Pencil,
  XCircle
} from "lucide-react";

// Using ROICalculation from service, but with camelCase fields and savedAt for display
interface SavedCalculation {
  id: number;
  vehicleName: string;
  vehiclePrice: number;
  dailyRate: number;
  bookingDays: number;
  monthlyExpenses: number;
  insuranceMonthly: number;
  annualDepreciation: number;
  roi: number;
  annualProfit: number;
  savedAt: string;
}

interface ValidationErrors {
  vehiclePrice?: string;
  dailyRate?: string;
  bookingDays?: string;
  monthlyExpenses?: string;
  insuranceMonthly?: string;
  annualDepreciation?: string;
}

const ROICalculator = () => {
  const { currency } = useRegionalSettings();
  const [vehicleName, setVehicleName] = useState("");
  const [vehiclePrice, setVehiclePrice] = useState(35000);
  const [dailyRate, setDailyRate] = useState(85);
  const [bookingDays, setBookingDays] = useState(20);
  const [monthlyExpenses, setMonthlyExpenses] = useState(500);
  const [insuranceMonthly, setInsuranceMonthly] = useState(200);
  const [annualDepreciation, setAnnualDepreciation] = useState(7000);
  const [savedCalculations, setSavedCalculations] = useState<SavedCalculation[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);

  // Load saved calculations from API
  useEffect(() => {
    const loadCalculations = async () => {
      try {
        setLoading(true);
        const response = await roiService.getCalculations();
        // Convert API format to component format
        const converted = response.calculations.map(calc => ({
          ...calc,
          vehicleName: calc.vehicle_name,
          vehiclePrice: calc.vehicle_price,
          dailyRate: calc.daily_rate,
          bookingDays: calc.booking_days,
          monthlyExpenses: calc.monthly_expenses,
          insuranceMonthly: calc.insurance_monthly,
          annualDepreciation: calc.annual_depreciation,
          savedAt: new Date(calc.created_at).toLocaleDateString()
        }));
        setSavedCalculations(converted);
      } catch (error) {
        console.error("Failed to load saved calculations:", error);
        toast.error("Failed to load saved calculations");
      } finally {
        setLoading(false);
      }
    };
    loadCalculations();
  }, []);

  // Validation
  const validateInput = (field: keyof ValidationErrors, value: number): string | undefined => {
    if (isNaN(value) || value < 0) {
      return "Must be a positive number";
    }
    
    switch (field) {
      case "vehiclePrice":
        if (value < 1000) return "Vehicle price should be at least $1,000";
        if (value > 1000000) return "Vehicle price seems unusually high";
        break;
      case "dailyRate":
        if (value < 10) return "Daily rate should be at least $10";
        if (value > 10000) return "Daily rate seems unusually high";
        break;
      case "bookingDays":
        if (value < 0) return "Booking days cannot be negative";
        if (value > 30) return "Booking days cannot exceed 30";
        break;
      case "monthlyExpenses":
        if (value < 0) return "Expenses cannot be negative";
        if (value > 100000) return "Monthly expenses seem unusually high";
        break;
      case "insuranceMonthly":
        if (value < 0) return "Insurance cannot be negative";
        if (value > 50000) return "Monthly insurance seems unusually high";
        break;
      case "annualDepreciation":
        if (value < 0) return "Depreciation cannot be negative";
        if (value > vehiclePrice) return "Annual depreciation cannot exceed vehicle price";
        break;
    }
    return undefined;
  };

  const handleInputChange = (
    field: keyof ValidationErrors,
    value: number,
    setter: (value: number) => void
  ) => {
    const error = validateInput(field, value);
    setValidationErrors(prev => ({
      ...prev,
      [field]: error
    }));
    setter(value);
    
    // If vehicle price changes, re-validate annual depreciation
    if (field === "vehiclePrice") {
      const depError = validateInput("annualDepreciation", annualDepreciation);
      setValidationErrors(prev => ({
        ...prev,
        annualDepreciation: depError
      }));
    }
  };

  // Calculations
  const monthlyRevenue = dailyRate * bookingDays;
  const annualRevenue = monthlyRevenue * 12;
  const totalMonthlyExpenses = monthlyExpenses + insuranceMonthly;
  const monthlyProfit = monthlyRevenue - totalMonthlyExpenses;
  const annualProfit = monthlyProfit * 12;
  const netAnnualProfit = annualProfit - annualDepreciation;
  // ROI = (Net Annual Profit / Initial Investment) × 100
  const roi = vehiclePrice > 0 ? ((netAnnualProfit / vehiclePrice) * 100) : 0;
  const paybackMonths = monthlyProfit > 0 ? vehiclePrice / monthlyProfit : Infinity;
  const utilizationRate = (bookingDays / 30) * 100;
  const profitMargin = monthlyRevenue > 0 ? (monthlyProfit / monthlyRevenue) * 100 : 0;

  // Filter saved calculations
  const filteredCalculations = useMemo(() => {
    if (!searchQuery.trim()) return savedCalculations;
    const query = searchQuery.toLowerCase();
    return savedCalculations.filter(calc => 
      calc.vehicleName.toLowerCase().includes(query)
    );
  }, [savedCalculations, searchQuery]);

  const hasValidationErrors = Object.values(validationErrors).some(error => error !== undefined);

  const saveCalculation = async () => {
    // Validate all fields
    const errors: ValidationErrors = {};
    errors.vehiclePrice = validateInput("vehiclePrice", vehiclePrice);
    errors.dailyRate = validateInput("dailyRate", dailyRate);
    errors.bookingDays = validateInput("bookingDays", bookingDays);
    errors.monthlyExpenses = validateInput("monthlyExpenses", monthlyExpenses);
    errors.insuranceMonthly = validateInput("insuranceMonthly", insuranceMonthly);
    errors.annualDepreciation = validateInput("annualDepreciation", annualDepreciation);

    setValidationErrors(errors);

    if (Object.values(errors).some(error => error !== undefined)) {
      toast.error("Please fix validation errors before saving");
      return;
    }

    if (!vehicleName.trim()) {
      toast.error("Please enter a vehicle name");
      return;
    }
    
    // Check for duplicate names (excluding the one being edited)
    const trimmedName = vehicleName.trim();
    const duplicate = savedCalculations.find(
      calc => calc.vehicleName.toLowerCase() === trimmedName.toLowerCase() && calc.id !== editingId
    );
    
    if (duplicate) {
      toast.error(`A calculation with the name "${trimmedName}" already exists. Please use a different name.`);
      return;
    }
    
    try {
      setSaving(true);
      
      if (editingId) {
        // Update existing calculation
        const saved = await roiService.updateCalculation(editingId, {
          vehicle_name: trimmedName,
          vehicle_price: vehiclePrice,
          daily_rate: dailyRate,
          booking_days: bookingDays,
          monthly_expenses: monthlyExpenses,
          insurance_monthly: insuranceMonthly,
          annual_depreciation: annualDepreciation,
          roi,
          annual_profit: annualProfit,
        });
        
        // Convert API format to component format
        const updatedCalculation: SavedCalculation = {
          ...saved,
          vehicleName: saved.vehicle_name,
          vehiclePrice: saved.vehicle_price,
          dailyRate: saved.daily_rate,
          bookingDays: saved.booking_days,
          monthlyExpenses: saved.monthly_expenses,
          insuranceMonthly: saved.insurance_monthly,
          annualDepreciation: saved.annual_depreciation,
          savedAt: new Date(saved.created_at).toLocaleDateString()
        };
        
        setSavedCalculations(savedCalculations.map(calc => 
          calc.id === editingId ? updatedCalculation : calc
        ));
        setEditingId(null);
        toast.success(`Updated calculation for ${updatedCalculation.vehicleName}`);
      } else {
        // Create new calculation
        const saved = await roiService.saveCalculation({
          vehicle_name: trimmedName,
          vehicle_price: vehiclePrice,
          daily_rate: dailyRate,
          booking_days: bookingDays,
          monthly_expenses: monthlyExpenses,
          insurance_monthly: insuranceMonthly,
          annual_depreciation: annualDepreciation,
          roi,
          annual_profit: annualProfit,
        });
        
        // Convert API format to component format
        const newCalculation: SavedCalculation = {
          ...saved,
          vehicleName: saved.vehicle_name,
          vehiclePrice: saved.vehicle_price,
          dailyRate: saved.daily_rate,
          bookingDays: saved.booking_days,
          monthlyExpenses: saved.monthly_expenses,
          insuranceMonthly: saved.insurance_monthly,
          annualDepreciation: saved.annual_depreciation,
          savedAt: new Date(saved.created_at).toLocaleDateString()
        };
        
        setSavedCalculations([newCalculation, ...savedCalculations]);
        toast.success(`Saved calculation for ${newCalculation.vehicleName}`);
      }
      
      setVehicleName("");
      setSearchQuery("");
    } catch (error) {
      console.error("Failed to save calculation:", error);
      toast.error("Failed to save calculation. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  const loadCalculation = (calc: SavedCalculation) => {
    setVehicleName(calc.vehicleName);
    setVehiclePrice(calc.vehiclePrice);
    setDailyRate(calc.dailyRate);
    setBookingDays(calc.bookingDays);
    setMonthlyExpenses(calc.monthlyExpenses);
    setInsuranceMonthly(calc.insuranceMonthly);
    setAnnualDepreciation(calc.annualDepreciation);
    setEditingId(null); // Clear edit mode when loading
    setValidationErrors({});
    toast.success(`Loaded calculation for ${calc.vehicleName}`);
  };

  const editCalculation = (calc: SavedCalculation) => {
    setVehicleName(calc.vehicleName);
    setVehiclePrice(calc.vehiclePrice);
    setDailyRate(calc.dailyRate);
    setBookingDays(calc.bookingDays);
    setMonthlyExpenses(calc.monthlyExpenses);
    setInsuranceMonthly(calc.insuranceMonthly);
    setAnnualDepreciation(calc.annualDepreciation);
    setEditingId(calc.id);
    setValidationErrors({});
    // Scroll to top of form
    window.scrollTo({ top: 0, behavior: 'smooth' });
    toast.info(`Editing calculation: ${calc.vehicleName}`);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setVehicleName("");
    setVehiclePrice(35000);
    setDailyRate(85);
    setBookingDays(20);
    setMonthlyExpenses(500);
    setInsuranceMonthly(200);
    setAnnualDepreciation(7000);
    setValidationErrors({});
  };

  const deleteCalculation = async (id: number) => {
    try {
      await roiService.deleteCalculation(id);
      setSavedCalculations(savedCalculations.filter(c => c.id !== id));
      toast.success("Calculation deleted");
    } catch (error) {
      console.error("Failed to delete calculation:", error);
      toast.error("Failed to delete calculation. Please try again.");
    }
  };

  return (
    <TooltipProvider delayDuration={300}>
      <div className="min-h-screen bg-background p-6">
        <div className="mx-auto max-w-[2000px] space-y-6">
          {/* Header */}
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-xl bg-primary/10 transition-all duration-200 hover:bg-primary/15">
                <Calculator className="h-6 w-6 text-primary" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-foreground tracking-tight">ROI Calculator</h1>
                <p className="text-muted-foreground mt-1">Calculate your fleet's return on investment</p>
              </div>
            </div>
          </div>

          {/* KPI Summary */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card className="bg-gradient-to-br from-primary/10 to-primary/5 border-primary/20 transition-all duration-200 hover:shadow-md">
              <CardContent className="p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground font-medium">Annual ROI</p>
                    <p className={`text-3xl font-bold mt-1 transition-colors ${roi >= 0 ? 'text-success' : 'text-destructive'}`}>
                      {roi.toFixed(1)}%
                    </p>
                  </div>
                  <div className="p-3 rounded-full bg-primary/20 transition-transform duration-200 hover:scale-110">
                    <TrendingUp className="h-5 w-5 text-primary" />
                  </div>
                </div>
                <p className="text-xs text-muted-foreground mt-2">After depreciation</p>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-success/10 to-success/5 border-success/20 transition-all duration-200 hover:shadow-md">
              <CardContent className="p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground font-medium">Annual Profit</p>
                    <p className="text-3xl font-bold mt-1 text-success">{formatCurrency(annualProfit, currency)}</p>
                  </div>
                  <div className="p-3 rounded-full bg-success/20 transition-transform duration-200 hover:scale-110">
                    <DollarSign className="h-5 w-5 text-success" />
                  </div>
                </div>
                <p className="text-xs text-muted-foreground mt-2">Before depreciation</p>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-warning/10 to-warning/5 border-warning/20 transition-all duration-200 hover:shadow-md">
              <CardContent className="p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground font-medium">Payback Period</p>
                    <p className="text-3xl font-bold mt-1 text-warning">
                      {paybackMonths === Infinity ? "∞" : paybackMonths.toFixed(1)}
                    </p>
                  </div>
                  <div className="p-3 rounded-full bg-warning/20 transition-transform duration-200 hover:scale-110">
                    <Clock className="h-5 w-5 text-warning" />
                  </div>
                </div>
                <p className="text-xs text-muted-foreground mt-2">Months to break even</p>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-chart-4/10 to-chart-4/5 border-chart-4/20 transition-all duration-200 hover:shadow-md">
              <CardContent className="p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground font-medium">Utilization</p>
                    <p className="text-3xl font-bold mt-1" style={{ color: 'hsl(var(--chart-4))' }}>
                      {utilizationRate.toFixed(0)}%
                    </p>
                  </div>
                  <div className="p-3 rounded-full transition-transform duration-200 hover:scale-110" style={{ backgroundColor: 'hsla(var(--chart-4), 0.2)' }}>
                    <CalendarDays className="h-5 w-5" style={{ color: 'hsl(var(--chart-4))' }} />
                  </div>
                </div>
                <p className="text-xs text-muted-foreground mt-2">{bookingDays} days/month booked</p>
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-6 lg:grid-cols-3">
            {/* Input Section */}
            <div className="lg:col-span-2 space-y-6">
              <Card className="transition-all duration-200 hover:shadow-sm">
                <CardHeader className="pb-4">
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <Car className="h-5 w-5 text-primary" />
                    Vehicle Investment
                  </CardTitle>
                  <CardDescription>Enter your vehicle purchase details</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <Label htmlFor="vehicleName" className="text-sm font-medium">Vehicle Name</Label>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Info className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
                        </TooltipTrigger>
                        <TooltipContent className="max-w-xs">
                          <p>Give this calculation a descriptive name to easily identify it later when saved.</p>
                        </TooltipContent>
                      </Tooltip>
                    </div>
                    <div className="relative">
                      <Car className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input
                        id="vehicleName"
                        type="text"
                        placeholder="e.g., 2024 Tesla Model 3"
                        value={vehicleName}
                        onChange={(e) => setVehicleName(e.target.value)}
                        className="pl-9 transition-all duration-200"
                      />
                    </div>
                    {editingId && (
                      <p className="text-xs text-primary font-medium">Editing existing calculation</p>
                    )}
                    <p className="text-xs text-muted-foreground">
                      {editingId ? "Update the name if needed" : "Give this calculation a name to save it"}
                    </p>
                  </div>

                  <div className="grid gap-6 sm:grid-cols-2">
                    <div className="space-y-3">
                      <div className="flex items-center gap-2">
                        <Label htmlFor="vehiclePrice" className="text-sm font-medium">Vehicle Purchase Price</Label>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Info className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
                          </TooltipTrigger>
                          <TooltipContent className="max-w-xs">
                            <p>The total purchase price of the vehicle, including taxes and fees.</p>
                          </TooltipContent>
                        </Tooltip>
                      </div>
                      <div className="relative">
                        <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                          id="vehiclePrice"
                          type="number"
                          min="0"
                          step="100"
                          value={vehiclePrice}
                          onChange={(e) => handleInputChange("vehiclePrice", Number(e.target.value), setVehiclePrice)}
                          className={`pl-9 transition-all duration-200 ${
                            validationErrors.vehiclePrice ? 'border-destructive focus-visible:ring-destructive' : ''
                          }`}
                        />
                      </div>
                      {validationErrors.vehiclePrice && (
                        <p className="text-xs text-destructive flex items-center gap-1">
                          <AlertCircle className="h-3 w-3" />
                          {validationErrors.vehiclePrice}
                        </p>
                      )}
                      <p className="text-xs text-muted-foreground">
                        {formatCurrency(vehiclePrice, currency)}
                      </p>
                    </div>

                    <div className="space-y-3">
                      <div className="flex items-center gap-2">
                        <Label htmlFor="annualDepreciation" className="text-sm font-medium">Annual Depreciation</Label>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Info className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
                          </TooltipTrigger>
                          <TooltipContent className="max-w-xs">
                            <p>The annual amount the vehicle depreciates in value. This accounts for wear, age, and market value decline.</p>
                          </TooltipContent>
                        </Tooltip>
                      </div>
                      <div className="relative">
                        <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                          id="annualDepreciation"
                          type="number"
                          min="0"
                          step="100"
                          value={annualDepreciation}
                          onChange={(e) => handleInputChange("annualDepreciation", Number(e.target.value), setAnnualDepreciation)}
                          className={`pl-9 transition-all duration-200 ${
                            validationErrors.annualDepreciation ? 'border-destructive focus-visible:ring-destructive' : ''
                          }`}
                        />
                      </div>
                      {validationErrors.annualDepreciation && (
                        <p className="text-xs text-destructive flex items-center gap-1">
                          <AlertCircle className="h-3 w-3" />
                          {validationErrors.annualDepreciation}
                        </p>
                      )}
                      <p className="text-xs text-muted-foreground">
                        {formatCurrency(annualDepreciation, currency)} per year
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="transition-all duration-200 hover:shadow-sm">
                <CardHeader className="pb-4">
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <BarChart3 className="h-5 w-5 text-primary" />
                    Revenue Projections
                  </CardTitle>
                  <CardDescription>Estimate your rental income</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid gap-6 sm:grid-cols-2">
                    <div className="space-y-3">
                      <div className="flex items-center gap-2">
                        <Label htmlFor="dailyRate" className="text-sm font-medium">Daily Rental Rate</Label>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Info className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
                          </TooltipTrigger>
                          <TooltipContent className="max-w-xs">
                            <p>The average daily rate you charge for renting this vehicle on Turo.</p>
                          </TooltipContent>
                        </Tooltip>
                      </div>
                      <div className="relative">
                        <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                          id="dailyRate"
                          type="number"
                          min="0"
                          step="1"
                          value={dailyRate}
                          onChange={(e) => handleInputChange("dailyRate", Number(e.target.value), setDailyRate)}
                          className={`pl-9 transition-all duration-200 ${
                            validationErrors.dailyRate ? 'border-destructive focus-visible:ring-destructive' : ''
                          }`}
                        />
                      </div>
                      {validationErrors.dailyRate && (
                        <p className="text-xs text-destructive flex items-center gap-1">
                          <AlertCircle className="h-3 w-3" />
                          {validationErrors.dailyRate}
                        </p>
                      )}
                      <p className="text-xs text-muted-foreground">
                        {formatCurrency(dailyRate, currency)} per day
                      </p>
                    </div>

                    <div className="space-y-3">
                      <div className="flex items-center gap-2">
                        <Label className="text-sm font-medium">Booking Days per Month: {bookingDays}</Label>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Info className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
                          </TooltipTrigger>
                          <TooltipContent className="max-w-xs">
                            <p>Average number of days per month the vehicle is booked. This affects your utilization rate and revenue.</p>
                          </TooltipContent>
                        </Tooltip>
                      </div>
                      <Slider
                        value={[bookingDays]}
                        onValueChange={(v) => {
                          const error = validateInput("bookingDays", v[0]);
                          setValidationErrors(prev => ({
                            ...prev,
                            bookingDays: error
                          }));
                          setBookingDays(v[0]);
                        }}
                        min={0}
                        max={30}
                        step={1}
                        className="mt-2"
                      />
                      {validationErrors.bookingDays && (
                        <p className="text-xs text-destructive flex items-center gap-1">
                          <AlertCircle className="h-3 w-3" />
                          {validationErrors.bookingDays}
                        </p>
                      )}
                      <p className="text-xs text-muted-foreground">
                        {utilizationRate.toFixed(1)}% utilization rate
                      </p>
                    </div>
                  </div>

                  <div className="p-4 rounded-lg bg-muted/50 border border-border transition-all duration-200 hover:bg-muted/70">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground font-medium">Projected Monthly Revenue</span>
                      <span className="text-lg font-bold text-foreground">{formatCurrency(monthlyRevenue, currency)}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="transition-all duration-200 hover:shadow-sm">
                <CardHeader className="pb-4">
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <PiggyBank className="h-5 w-5 text-primary" />
                    Operating Expenses
                  </CardTitle>
                  <CardDescription>Enter your monthly costs</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid gap-6 sm:grid-cols-2">
                    <div className="space-y-3">
                      <div className="flex items-center gap-2">
                        <Label htmlFor="monthlyExpenses" className="text-sm font-medium">Monthly Maintenance & Misc</Label>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Info className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
                          </TooltipTrigger>
                          <TooltipContent className="max-w-xs">
                            <p>Monthly costs including cleaning, fuel, repairs, parking, storage, and other miscellaneous expenses.</p>
                          </TooltipContent>
                        </Tooltip>
                      </div>
                      <div className="relative">
                        <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                          id="monthlyExpenses"
                          type="number"
                          min="0"
                          step="10"
                          value={monthlyExpenses}
                          onChange={(e) => handleInputChange("monthlyExpenses", Number(e.target.value), setMonthlyExpenses)}
                          className={`pl-9 transition-all duration-200 ${
                            validationErrors.monthlyExpenses ? 'border-destructive focus-visible:ring-destructive' : ''
                          }`}
                        />
                      </div>
                      {validationErrors.monthlyExpenses && (
                        <p className="text-xs text-destructive flex items-center gap-1">
                          <AlertCircle className="h-3 w-3" />
                          {validationErrors.monthlyExpenses}
                        </p>
                      )}
                      <p className="text-xs text-muted-foreground">Cleaning, fuel, repairs, etc.</p>
                    </div>

                    <div className="space-y-3">
                      <div className="flex items-center gap-2">
                        <Label htmlFor="insurance" className="text-sm font-medium">Monthly Insurance</Label>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Info className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
                          </TooltipTrigger>
                          <TooltipContent className="max-w-xs">
                            <p>Monthly commercial auto insurance premium for this vehicle.</p>
                          </TooltipContent>
                        </Tooltip>
                      </div>
                      <div className="relative">
                        <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                          id="insurance"
                          type="number"
                          min="0"
                          step="10"
                          value={insuranceMonthly}
                          onChange={(e) => handleInputChange("insuranceMonthly", Number(e.target.value), setInsuranceMonthly)}
                          className={`pl-9 transition-all duration-200 ${
                            validationErrors.insuranceMonthly ? 'border-destructive focus-visible:ring-destructive' : ''
                          }`}
                        />
                      </div>
                      {validationErrors.insuranceMonthly && (
                        <p className="text-xs text-destructive flex items-center gap-1">
                          <AlertCircle className="h-3 w-3" />
                          {validationErrors.insuranceMonthly}
                        </p>
                      )}
                      <p className="text-xs text-muted-foreground">Commercial auto insurance</p>
                    </div>
                  </div>

                  <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/20 transition-all duration-200">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground font-medium">Total Monthly Expenses</span>
                      <span className="text-lg font-bold text-destructive">{formatCurrency(totalMonthlyExpenses, currency)}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Results Section */}
            <div className="space-y-6">
              <Card className="sticky top-6 transition-all duration-200 hover:shadow-md">
                <CardHeader className="bg-gradient-to-r from-primary/10 to-transparent rounded-t-lg pb-4">
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <Target className="h-5 w-5 text-primary" />
                    Financial Summary
                  </CardTitle>
                  <CardDescription>Your projected returns</CardDescription>
                </CardHeader>
                <CardContent className="space-y-5 pt-6">
                  {/* Monthly Breakdown */}
                  <div className="space-y-3">
                    <h4 className="font-semibold text-sm text-muted-foreground uppercase tracking-wide">Monthly</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between py-2 border-b border-border transition-colors">
                        <span className="text-muted-foreground">Revenue</span>
                        <span className="font-semibold text-success">{formatCurrency(monthlyRevenue, currency)}</span>
                      </div>
                      <div className="flex justify-between py-2 border-b border-border transition-colors">
                        <span className="text-muted-foreground">Expenses</span>
                        <span className="font-semibold text-destructive">-{formatCurrency(totalMonthlyExpenses, currency)}</span>
                      </div>
                      <div className="flex justify-between py-2 bg-muted/50 rounded-lg px-3 -mx-3 transition-colors">
                        <span className="font-semibold">Net Profit</span>
                        <span className={`font-bold transition-colors ${monthlyProfit >= 0 ? 'text-success' : 'text-destructive'}`}>
                          {formatCurrency(monthlyProfit, currency)}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Annual Breakdown */}
                  <div className="space-y-3 pt-4">
                    <h4 className="font-semibold text-sm text-muted-foreground uppercase tracking-wide">Annual</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between py-2 border-b border-border transition-colors">
                        <span className="text-muted-foreground">Gross Profit</span>
                        <span className="font-semibold">{formatCurrency(annualProfit, currency)}</span>
                      </div>
                      <div className="flex justify-between py-2 border-b border-border transition-colors">
                        <span className="text-muted-foreground">Depreciation</span>
                        <span className="font-semibold text-destructive">-{formatCurrency(annualDepreciation, currency)}</span>
                      </div>
                      <div className="flex justify-between py-2 bg-muted/50 rounded-lg px-3 -mx-3 transition-colors">
                        <span className="font-semibold">Net Profit</span>
                        <span className={`font-bold transition-colors ${netAnnualProfit >= 0 ? 'text-success' : 'text-destructive'}`}>
                          {formatCurrency(netAnnualProfit, currency)}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Key Metrics */}
                  <div className="space-y-3 pt-4">
                    <h4 className="font-semibold text-sm text-muted-foreground uppercase tracking-wide">Key Metrics</h4>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="p-3 rounded-lg bg-muted/50 text-center transition-all duration-200 hover:bg-muted/70">
                        <p className={`text-2xl font-bold ${roi >= 0 ? 'text-primary' : 'text-destructive'}`}>{roi.toFixed(1)}%</p>
                        <p className="text-xs text-muted-foreground">Annual ROI</p>
                      </div>
                      <div className="p-3 rounded-lg bg-muted/50 text-center transition-all duration-200 hover:bg-muted/70">
                        <p className="text-2xl font-bold text-primary">{profitMargin.toFixed(1)}%</p>
                        <p className="text-xs text-muted-foreground">Profit Margin</p>
                      </div>
                    </div>
                  </div>

                  {/* Insight */}
                  <div className="p-4 rounded-lg bg-primary/5 border border-primary/20 mt-4 transition-all duration-200">
                    <div className="flex gap-3">
                      <Info className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                      <div>
                        <p className="text-sm font-medium text-foreground">Investment Insight</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          {roi >= 15 
                            ? "Excellent ROI! This vehicle is a strong investment."
                            : roi >= 10
                            ? "Good ROI. Consider optimizing pricing or utilization."
                            : roi >= 5
                            ? "Moderate ROI. Look for ways to reduce expenses."
                            : monthlyProfit <= 0
                            ? "Negative profit. Review your expenses and pricing strategy."
                            : "Low ROI. Consider a different vehicle or market."}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-2 mt-4">
                    {editingId && (
                      <Button 
                        variant="outline"
                        className="flex-1 gap-2 transition-all duration-200" 
                        onClick={cancelEdit}
                        disabled={saving}
                      >
                        <XCircle className="h-4 w-4" />
                        Cancel
                      </Button>
                    )}
                    <Button 
                      className={`${editingId ? 'flex-1' : 'w-full'} gap-2 transition-all duration-200`}
                      onClick={saveCalculation}
                      disabled={hasValidationErrors || saving}
                    >
                      {saving ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin" />
                          {editingId ? 'Updating...' : 'Saving...'}
                        </>
                      ) : hasValidationErrors ? (
                        <>
                          <AlertCircle className="h-4 w-4" />
                          Fix Errors to Save
                        </>
                      ) : (
                        <>
                          <Bookmark className="h-4 w-4" />
                          {editingId ? 'Update Calculation' : 'Save Calculation'}
                        </>
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>

            {/* Saved Calculations */}
            {loading ? (
              <Card className="transition-all duration-200">
                <CardContent className="p-6">
                  <div className="flex items-center justify-center gap-2 text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span className="text-sm">Loading calculations...</span>
                  </div>
                </CardContent>
              </Card>
            ) : savedCalculations.length > 0 && (
              <Card className="transition-all duration-200 hover:shadow-sm">
                <CardHeader className="pb-4">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Bookmark className="h-4 w-4 text-primary" />
                    Saved Calculations
                    <Badge variant="secondary" className="ml-auto">
                      {savedCalculations.length}
                    </Badge>
                  </CardTitle>
                    <div className="relative mt-3">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input
                        placeholder="Search saved calculations..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-9 pr-8"
                      />
                      {searchQuery && (
                        <Button
                          variant="ghost"
                          size="icon"
                          className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7"
                          onClick={() => setSearchQuery("")}
                        >
                          <X className="h-3.5 w-3.5" />
                        </Button>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent className="p-0">
                    <ScrollArea className="h-[300px]">
                      <div className="space-y-2 p-4 pt-0">
                        {filteredCalculations.length === 0 ? (
                          <div className="flex flex-col items-center justify-center py-8 text-center">
                            <Search className="h-8 w-8 text-muted-foreground mb-2 opacity-50" />
                            <p className="text-sm text-muted-foreground">No calculations found</p>
                            <p className="text-xs text-muted-foreground mt-1">Try a different search term</p>
                          </div>
                        ) : (
                          filteredCalculations.map((calc) => (
                            <div
                              key={calc.id}
                              className="p-3 rounded-lg bg-muted/50 border border-border hover:bg-muted transition-all duration-200 hover:border-primary/30 group"
                            >
                              <div className="flex items-start justify-between gap-2">
                                <div className="min-w-0 flex-1">
                                  <p className="font-medium text-sm truncate">{calc.vehicleName}</p>
                                  <p className="text-xs text-muted-foreground">{calc.savedAt}</p>
                                </div>
                                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-7 w-7 text-muted-foreground hover:text-primary"
                                    onClick={() => editCalculation(calc)}
                                    title="Edit calculation"
                                  >
                                    <Pencil className="h-3.5 w-3.5" />
                                  </Button>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-7 w-7 text-muted-foreground hover:text-primary"
                                    onClick={() => loadCalculation(calc)}
                                    title="Load calculation"
                                  >
                                    <CheckCircle2 className="h-3.5 w-3.5" />
                                  </Button>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-7 w-7 text-muted-foreground hover:text-destructive"
                                    onClick={() => deleteCalculation(calc.id)}
                                    title="Delete calculation"
                                  >
                                    <Trash2 className="h-3.5 w-3.5" />
                                  </Button>
                                </div>
                              </div>
                              <div className="flex items-center gap-4 mt-2 text-xs">
                                <div>
                                  <span className="text-muted-foreground">ROI: </span>
                                  <span className={`font-semibold ${calc.roi >= 0 ? 'text-success' : 'text-destructive'}`}>
                                    {calc.roi.toFixed(1)}%
                                  </span>
                                </div>
                                <div>
                                  <span className="text-muted-foreground">Profit: </span>
                                  <span className="font-semibold">{formatCurrency(calc.annualProfit, currency)}/yr</span>
                                </div>
                              </div>
                              <p className="text-xs text-muted-foreground mt-1">
                                {formatCurrency(calc.vehiclePrice, currency)} • {formatCurrency(calc.dailyRate, currency)}/day • {calc.bookingDays} days/mo
                              </p>
                            </div>
                          ))
                        )}
                      </div>
                    </ScrollArea>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </div>
      </div>
    </TooltipProvider>
  );
};

export default ROICalculator;
