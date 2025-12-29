import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";
import { useRegionalSettings } from "@/contexts/RegionalSettingsContext";
import { formatCurrency } from "@/lib/regional-utils";
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
  Trash2
} from "lucide-react";

interface SavedCalculation {
  id: string;
  vehicleName: string;
  vehiclePrice: number;
  dailyRate: number;
  bookingDays: number;
  monthlyExpenses: number;
  insuranceMonthly: number;
  depreciationYears: number;
  roi: number;
  annualProfit: number;
  savedAt: string;
}

const ROICalculator = () => {
  const { currency } = useRegionalSettings();
  const [vehicleName, setVehicleName] = useState("");
  const [vehiclePrice, setVehiclePrice] = useState(35000);
  const [dailyRate, setDailyRate] = useState(85);
  const [bookingDays, setBookingDays] = useState(20);
  const [monthlyExpenses, setMonthlyExpenses] = useState(500);
  const [insuranceMonthly, setInsuranceMonthly] = useState(200);
  const [depreciationYears, setDepreciationYears] = useState(5);
  const [savedCalculations, setSavedCalculations] = useState<SavedCalculation[]>([]);

  // Load saved calculations from localStorage
  useEffect(() => {
    const saved = localStorage.getItem("roi-calculations");
    if (saved) {
      setSavedCalculations(JSON.parse(saved));
    }
  }, []);

  // Calculations
  const monthlyRevenue = dailyRate * bookingDays;
  const annualRevenue = monthlyRevenue * 12;
  const totalMonthlyExpenses = monthlyExpenses + insuranceMonthly;
  const monthlyProfit = monthlyRevenue - totalMonthlyExpenses;
  const annualProfit = monthlyProfit * 12;
  const annualDepreciation = vehiclePrice / depreciationYears;
  const netAnnualProfit = annualProfit - annualDepreciation;
  const roi = ((netAnnualProfit / vehiclePrice) * 100);
  const paybackMonths = vehiclePrice / monthlyProfit;
  const utilizationRate = (bookingDays / 30) * 100;
  const profitMargin = (monthlyProfit / monthlyRevenue) * 100;

  // formatCurrency will be imported from regional-utils

  const saveCalculation = () => {
    if (!vehicleName.trim()) {
      toast.error("Please enter a vehicle name");
      return;
    }
    
    const newCalculation: SavedCalculation = {
      id: Date.now().toString(),
      vehicleName: vehicleName.trim(),
      vehiclePrice,
      dailyRate,
      bookingDays,
      monthlyExpenses,
      insuranceMonthly,
      depreciationYears,
      roi,
      annualProfit,
      savedAt: new Date().toLocaleDateString()
    };
    
    const updated = [newCalculation, ...savedCalculations];
    setSavedCalculations(updated);
    localStorage.setItem("roi-calculations", JSON.stringify(updated));
    setVehicleName("");
    toast.success(`Saved calculation for ${newCalculation.vehicleName}`);
  };

  const deleteCalculation = (id: string) => {
    const updated = savedCalculations.filter(c => c.id !== id);
    setSavedCalculations(updated);
    localStorage.setItem("roi-calculations", JSON.stringify(updated));
    toast.success("Calculation deleted");
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="mx-auto max-w-[2000px] space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-primary/10">
              <Calculator className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-foreground">ROI Calculator</h1>
              <p className="text-muted-foreground">Calculate your fleet's return on investment</p>
            </div>
          </div>
        </div>

        {/* KPI Summary */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Card className="bg-gradient-to-br from-primary/10 to-primary/5 border-primary/20">
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground font-medium">Annual ROI</p>
                  <p className={`text-3xl font-bold mt-1 ${roi >= 0 ? 'text-success' : 'text-destructive'}`}>
                    {roi.toFixed(1)}%
                  </p>
                </div>
                <div className="p-3 rounded-full bg-primary/20">
                  <TrendingUp className="h-5 w-5 text-primary" />
                </div>
              </div>
              <p className="text-xs text-muted-foreground mt-2">After depreciation</p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-success/10 to-success/5 border-success/20">
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground font-medium">Annual Profit</p>
                  <p className="text-3xl font-bold mt-1 text-success">{formatCurrency(annualProfit, currency)}</p>
                </div>
                <div className="p-3 rounded-full bg-success/20">
                  <DollarSign className="h-5 w-5 text-success" />
                </div>
              </div>
              <p className="text-xs text-muted-foreground mt-2">Before depreciation</p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-warning/10 to-warning/5 border-warning/20">
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground font-medium">Payback Period</p>
                  <p className="text-3xl font-bold mt-1 text-warning">{paybackMonths.toFixed(1)}</p>
                </div>
                <div className="p-3 rounded-full bg-warning/20">
                  <Clock className="h-5 w-5 text-warning" />
                </div>
              </div>
              <p className="text-xs text-muted-foreground mt-2">Months to break even</p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-chart-4/10 to-chart-4/5 border-chart-4/20">
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground font-medium">Utilization</p>
                  <p className="text-3xl font-bold mt-1" style={{ color: 'hsl(var(--chart-4))' }}>{utilizationRate.toFixed(0)}%</p>
                </div>
                <div className="p-3 rounded-full" style={{ backgroundColor: 'hsla(var(--chart-4), 0.2)' }}>
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
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Car className="h-5 w-5 text-primary" />
                  Vehicle Investment
                </CardTitle>
                <CardDescription>Enter your vehicle purchase details</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-3">
                  <Label htmlFor="vehicleName">Vehicle Name</Label>
                  <div className="relative">
                    <Car className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="vehicleName"
                      type="text"
                      placeholder="e.g., 2024 Tesla Model 3"
                      value={vehicleName}
                      onChange={(e) => setVehicleName(e.target.value)}
                      className="pl-9"
                    />
                  </div>
                  <p className="text-xs text-muted-foreground">Give this calculation a name to save it</p>
                </div>

                <div className="grid gap-6 sm:grid-cols-2">
                  <div className="space-y-3">
                    <Label htmlFor="vehiclePrice">Vehicle Purchase Price</Label>
                    <div className="relative">
                      <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input
                        id="vehiclePrice"
                        type="number"
                        value={vehiclePrice}
                        onChange={(e) => setVehiclePrice(Number(e.target.value))}
                        className="pl-9"
                      />
                    </div>
                  </div>

                  <div className="space-y-3">
                    <Label>Depreciation Period: {depreciationYears} years</Label>
                    <Slider
                      value={[depreciationYears]}
                      onValueChange={(v) => setDepreciationYears(v[0])}
                      min={3}
                      max={10}
                      step={1}
                      className="mt-2"
                    />
                    <p className="text-xs text-muted-foreground">
                      Annual depreciation: {formatCurrency(annualDepreciation, currency)}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5 text-primary" />
                  Revenue Projections
                </CardTitle>
                <CardDescription>Estimate your rental income</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid gap-6 sm:grid-cols-2">
                  <div className="space-y-3">
                    <Label htmlFor="dailyRate">Daily Rental Rate</Label>
                    <div className="relative">
                      <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input
                        id="dailyRate"
                        type="number"
                        value={dailyRate}
                        onChange={(e) => setDailyRate(Number(e.target.value))}
                        className="pl-9"
                      />
                    </div>
                  </div>

                  <div className="space-y-3">
                    <Label>Booking Days per Month: {bookingDays}</Label>
                    <Slider
                      value={[bookingDays]}
                      onValueChange={(v) => setBookingDays(v[0])}
                      min={5}
                      max={30}
                      step={1}
                      className="mt-2"
                    />
                    <p className="text-xs text-muted-foreground">{utilizationRate.toFixed(0)}% utilization rate</p>
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-muted/50 border border-border">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Projected Monthly Revenue</span>
                    <span className="text-lg font-bold text-foreground">{formatCurrency(monthlyRevenue, currency)}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <PiggyBank className="h-5 w-5 text-primary" />
                  Operating Expenses
                </CardTitle>
                <CardDescription>Enter your monthly costs</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid gap-6 sm:grid-cols-2">
                  <div className="space-y-3">
                    <Label htmlFor="monthlyExpenses">Monthly Maintenance & Misc</Label>
                    <div className="relative">
                      <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input
                        id="monthlyExpenses"
                        type="number"
                        value={monthlyExpenses}
                        onChange={(e) => setMonthlyExpenses(Number(e.target.value))}
                        className="pl-9"
                      />
                    </div>
                    <p className="text-xs text-muted-foreground">Cleaning, fuel, repairs, etc.</p>
                  </div>

                  <div className="space-y-3">
                    <Label htmlFor="insurance">Monthly Insurance</Label>
                    <div className="relative">
                      <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input
                        id="insurance"
                        type="number"
                        value={insuranceMonthly}
                        onChange={(e) => setInsuranceMonthly(Number(e.target.value))}
                        className="pl-9"
                      />
                    </div>
                    <p className="text-xs text-muted-foreground">Commercial auto insurance</p>
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/20">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Total Monthly Expenses</span>
                    <span className="text-lg font-bold text-destructive">{formatCurrency(totalMonthlyExpenses, currency)}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Results Section */}
          <div className="space-y-6">
            <Card className="sticky top-6">
              <CardHeader className="bg-gradient-to-r from-primary/10 to-transparent rounded-t-lg">
                <CardTitle className="flex items-center gap-2">
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
                    <div className="flex justify-between py-2 border-b border-border">
                      <span className="text-muted-foreground">Revenue</span>
                      <span className="font-semibold text-success">{formatCurrency(monthlyRevenue, currency)}</span>
                    </div>
                    <div className="flex justify-between py-2 border-b border-border">
                      <span className="text-muted-foreground">Expenses</span>
                      <span className="font-semibold text-destructive">-{formatCurrency(totalMonthlyExpenses, currency)}</span>
                    </div>
                    <div className="flex justify-between py-2 bg-muted/50 rounded-lg px-3 -mx-3">
                      <span className="font-semibold">Net Profit</span>
                      <span className={`font-bold ${monthlyProfit >= 0 ? 'text-success' : 'text-destructive'}`}>
                        {formatCurrency(monthlyProfit, currency)}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Annual Breakdown */}
                <div className="space-y-3 pt-4">
                  <h4 className="font-semibold text-sm text-muted-foreground uppercase tracking-wide">Annual</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between py-2 border-b border-border">
                      <span className="text-muted-foreground">Gross Profit</span>
                      <span className="font-semibold">{formatCurrency(annualProfit, currency)}</span>
                    </div>
                    <div className="flex justify-between py-2 border-b border-border">
                      <span className="text-muted-foreground">Depreciation</span>
                      <span className="font-semibold text-destructive">-{formatCurrency(annualDepreciation, currency)}</span>
                    </div>
                    <div className="flex justify-between py-2 bg-muted/50 rounded-lg px-3 -mx-3">
                      <span className="font-semibold">Net Profit</span>
                      <span className={`font-bold ${netAnnualProfit >= 0 ? 'text-success' : 'text-destructive'}`}>
                        {formatCurrency(netAnnualProfit, currency)}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Key Metrics */}
                <div className="space-y-3 pt-4">
                  <h4 className="font-semibold text-sm text-muted-foreground uppercase tracking-wide">Key Metrics</h4>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 rounded-lg bg-muted/50 text-center">
                      <p className="text-2xl font-bold text-primary">{roi.toFixed(1)}%</p>
                      <p className="text-xs text-muted-foreground">Annual ROI</p>
                    </div>
                    <div className="p-3 rounded-lg bg-muted/50 text-center">
                      <p className="text-2xl font-bold text-primary">{profitMargin.toFixed(0)}%</p>
                      <p className="text-xs text-muted-foreground">Profit Margin</p>
                    </div>
                  </div>
                </div>

                {/* Insight */}
                <div className="p-4 rounded-lg bg-primary/5 border border-primary/20 mt-4">
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
                          : "Low ROI. Consider a different vehicle or market."}
                      </p>
                    </div>
                  </div>
                </div>

                <Button className="w-full mt-4 gap-2" onClick={saveCalculation}>
                  <Bookmark className="h-4 w-4" />
                  Save Calculation
                </Button>
              </CardContent>
            </Card>

            {/* Saved Calculations */}
            {savedCalculations.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Bookmark className="h-4 w-4 text-primary" />
                    Saved Calculations
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <ScrollArea className="h-[300px]">
                    <div className="space-y-2 p-4 pt-0">
                      {savedCalculations.map((calc) => (
                        <div
                          key={calc.id}
                          className="p-3 rounded-lg bg-muted/50 border border-border hover:bg-muted transition-colors"
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div className="min-w-0 flex-1">
                              <p className="font-medium text-sm truncate">{calc.vehicleName}</p>
                              <p className="text-xs text-muted-foreground">{calc.savedAt}</p>
                            </div>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7 shrink-0 text-muted-foreground hover:text-destructive"
                              onClick={() => deleteCalculation(calc.id)}
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </Button>
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
                      ))}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ROICalculator;
