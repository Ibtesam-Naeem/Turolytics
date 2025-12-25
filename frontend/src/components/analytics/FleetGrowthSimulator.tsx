import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Calculator, TrendingUp } from "lucide-react";

export const FleetGrowthSimulator = () => {
  const [vehicleCount, setVehicleCount] = useState([8]);
  const [avgDailyRate, setAvgDailyRate] = useState([85]);
  const [utilizationRate, setUtilizationRate] = useState([68]);

  // Calculations
  const monthlyRevenue = vehicleCount[0] * avgDailyRate[0] * (utilizationRate[0] / 100) * 30;
  const yearlyRevenue = monthlyRevenue * 12;
  const monthlyExpenses = vehicleCount[0] * 1200; // Avg $1200/vehicle/month
  const yearlyExpenses = monthlyExpenses * 12;
  const netProfit = yearlyRevenue - yearlyExpenses;
  const profitMargin = ((netProfit / yearlyRevenue) * 100).toFixed(1);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calculator className="h-5 w-5 text-chart-4" />
          Fleet Growth Simulator
        </CardTitle>
        <CardDescription>Adjust inputs to model different scenarios</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Input Controls */}
          <div className="space-y-6">
            <div>
              <div className="flex items-center justify-between mb-2">
                <Label className="text-sm font-medium">Fleet Size</Label>
                <span className="text-sm font-bold text-foreground">{vehicleCount[0]} vehicles</span>
              </div>
              <Slider
                value={vehicleCount}
                onValueChange={setVehicleCount}
                min={1}
                max={50}
                step={1}
                className="w-full"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <Label className="text-sm font-medium">Average Daily Rate</Label>
                <span className="text-sm font-bold text-foreground">${avgDailyRate[0]}</span>
              </div>
              <Slider
                value={avgDailyRate}
                onValueChange={setAvgDailyRate}
                min={50}
                max={200}
                step={5}
                className="w-full"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <Label className="text-sm font-medium">Utilization Rate</Label>
                <span className="text-sm font-bold text-foreground">{utilizationRate[0]}%</span>
              </div>
              <Slider
                value={utilizationRate}
                onValueChange={setUtilizationRate}
                min={30}
                max={95}
                step={1}
                className="w-full"
              />
            </div>
          </div>

          {/* Results */}
          <div className="space-y-3 pt-4 border-t border-border">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-chart-1/10 border border-chart-1/20 rounded-lg">
                <p className="text-xs text-muted-foreground mb-1">Monthly Revenue</p>
                <p className="text-xl font-bold text-foreground">${monthlyRevenue.toLocaleString(undefined, {maximumFractionDigits: 0})}</p>
              </div>
              <div className="p-3 bg-chart-5/10 border border-chart-5/20 rounded-lg">
                <p className="text-xs text-muted-foreground mb-1">Monthly Expenses</p>
                <p className="text-xl font-bold text-foreground">${monthlyExpenses.toLocaleString()}</p>
              </div>
            </div>

            <div className="p-4 bg-gradient-to-br from-chart-2/20 to-chart-2/5 border border-chart-2/20 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="h-4 w-4 text-chart-2" />
                <p className="text-sm font-medium text-foreground">Annual Projections</p>
              </div>
              <div className="grid grid-cols-2 gap-4 mt-3">
                <div>
                  <p className="text-xs text-muted-foreground">Yearly Revenue</p>
                  <p className="text-lg font-bold text-foreground">${yearlyRevenue.toLocaleString(undefined, {maximumFractionDigits: 0})}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Net Profit</p>
                  <p className={`text-lg font-bold ${netProfit > 0 ? 'text-success' : 'text-destructive'}`}>
                    ${netProfit.toLocaleString(undefined, {maximumFractionDigits: 0})}
                  </p>
                </div>
              </div>
              <div className="mt-3 pt-3 border-t border-border/50">
                <p className="text-xs text-muted-foreground">Profit Margin</p>
                <p className="text-2xl font-bold text-chart-2 mt-1">{profitMargin}%</p>
              </div>
            </div>
          </div>

          {/* Insights */}
          <div className="p-3 bg-muted/30 rounded-lg">
            <p className="text-xs font-medium text-foreground mb-2">💡 Scenario Insights</p>
            {netProfit > 100000 && (
              <p className="text-xs text-success">Strong profitability - excellent scenario!</p>
            )}
            {netProfit > 0 && netProfit <= 100000 && (
              <p className="text-xs text-chart-3">Profitable but with room for growth</p>
            )}
            {netProfit <= 0 && (
              <p className="text-xs text-destructive">Loss scenario - increase rates or utilization</p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};