import { useState } from "react";
import { BarChart3, TrendingUp, TrendingDown, DollarSign, Target, Activity, Wallet, Percent, Car, Zap } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { RevenueVsExpensesChart } from "@/components/analytics/RevenueVsExpensesChart";
import { ProfitMarginChart } from "@/components/analytics/ProfitMarginChart";
import { VehicleROILeaderboard } from "@/components/analytics/VehicleROILeaderboard";
import { DepreciationTracker } from "@/components/analytics/DepreciationTracker";
import { ExpenseDonutChart } from "@/components/analytics/ExpenseDonutChart";
import { BookingMetricsCard } from "@/components/analytics/BookingMetricsCard";
import { RevenueForecastChart } from "@/components/analytics/RevenueForecastChart";
import { GoalTracker } from "@/components/analytics/GoalTracker";
import { CashFlowTimeline } from "@/components/analytics/CashFlowTimeline";
import { SeasonalDemandHeatmap } from "@/components/analytics/SeasonalDemandHeatmap";
import { MaintenanceForecast } from "@/components/analytics/MaintenanceForecast";
import { CostPerMileChart } from "@/components/analytics/CostPerMileChart";
import { IdleDaysCostCard } from "@/components/analytics/IdleDaysCostCard";
import { FleetGrowthSimulator } from "@/components/analytics/FleetGrowthSimulator";
import { PeakHoursChart } from "@/components/analytics/PeakHoursChart";
import { RatingImpactChart } from "@/components/analytics/RatingImpactChart";
import { Progress } from "@/components/ui/progress";

const Analytics = () => {
  const [timeRange, setTimeRange] = useState("30d");

  return (
    <div className="min-h-screen bg-background p-4 sm:p-6 lg:p-8">
      <div className="mx-auto max-w-[2400px] space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Analytics Dashboard</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Comprehensive insights into your fleet performance
            </p>
          </div>
          <div className="flex gap-2 bg-muted/50 p-1 rounded-xl">
            {["7d", "30d", "90d", "YTD"].map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={`px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200 ${
                  timeRange === range
                    ? "bg-primary text-primary-foreground shadow-md"
                    : "text-muted-foreground hover:text-foreground hover:bg-background/50"
                }`}
              >
                {range}
              </button>
            ))}
          </div>
        </div>

        {/* Key Metrics - Top Row */}
        <div className="grid gap-4 grid-cols-2 lg:grid-cols-4 2xl:grid-cols-4">
          <Card className="relative overflow-hidden border-0 bg-gradient-to-br from-primary/10 via-card to-card">
            <div className="absolute top-0 right-0 w-24 h-24 bg-primary/5 rounded-full -translate-y-1/2 translate-x-1/2" />
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-muted-foreground">Net Profit</CardTitle>
                <div className="p-2 rounded-lg bg-primary/10">
                  <Wallet className="h-4 w-4 text-primary" />
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-foreground">$115,400</p>
              <div className="flex items-center gap-2 mt-2">
                <span className="flex items-center gap-1 text-sm font-medium text-success bg-success/10 px-2 py-0.5 rounded-full">
                  <TrendingUp className="h-3 w-3" />
                  +18.2%
                </span>
                <span className="text-xs text-muted-foreground">vs last period</span>
              </div>
            </CardContent>
          </Card>

          <Card className="relative overflow-hidden border-0 bg-gradient-to-br from-success/10 via-card to-card">
            <div className="absolute top-0 right-0 w-24 h-24 bg-success/5 rounded-full -translate-y-1/2 translate-x-1/2" />
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-muted-foreground">Gross Margin</CardTitle>
                <div className="p-2 rounded-lg bg-success/10">
                  <Percent className="h-4 w-4 text-success" />
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-foreground">31.4%</p>
              <div className="flex items-center gap-2 mt-2">
                <span className="flex items-center gap-1 text-sm font-medium text-success bg-success/10 px-2 py-0.5 rounded-full">
                  <TrendingUp className="h-3 w-3" />
                  +2.1%
                </span>
                <span className="text-xs text-muted-foreground">vs last period</span>
              </div>
            </CardContent>
          </Card>

          <Card className="relative overflow-hidden border-0 bg-gradient-to-br from-chart-3/10 via-card to-card">
            <div className="absolute top-0 right-0 w-24 h-24 bg-chart-3/5 rounded-full -translate-y-1/2 translate-x-1/2" />
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-muted-foreground">Fleet Utilization</CardTitle>
                <div className="p-2 rounded-lg bg-chart-3/10">
                  <Car className="h-4 w-4 text-chart-3" />
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-foreground">68%</p>
              <div className="flex items-center gap-2 mt-2">
                <span className="flex items-center gap-1 text-sm font-medium text-success bg-success/10 px-2 py-0.5 rounded-full">
                  <TrendingUp className="h-3 w-3" />
                  +5.2%
                </span>
                <span className="text-xs text-muted-foreground">vs last period</span>
              </div>
            </CardContent>
          </Card>

          <Card className="relative overflow-hidden border-0 bg-gradient-to-br from-chart-4/10 via-card to-card">
            <div className="absolute top-0 right-0 w-24 h-24 bg-chart-4/5 rounded-full -translate-y-1/2 translate-x-1/2" />
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-muted-foreground">Cash Flow</CardTitle>
                <div className="p-2 rounded-lg bg-chart-4/10">
                  <Zap className="h-4 w-4 text-chart-4" />
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-success">+$11.2k</p>
              <p className="text-sm text-muted-foreground mt-2">This month</p>
            </CardContent>
          </Card>
        </div>

        {/* Tabs for Different Analytics Sections */}
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="inline-flex h-12 items-center justify-start rounded-xl bg-muted/50 p-1 gap-1">
            <TabsTrigger value="overview" className="rounded-lg px-6 py-2.5 text-sm font-medium data-[state=active]:bg-background data-[state=active]:shadow-sm">Overview</TabsTrigger>
            <TabsTrigger value="financial" className="rounded-lg px-6 py-2.5 text-sm font-medium data-[state=active]:bg-background data-[state=active]:shadow-sm">Financial</TabsTrigger>
            <TabsTrigger value="vehicles" className="rounded-lg px-6 py-2.5 text-sm font-medium data-[state=active]:bg-background data-[state=active]:shadow-sm">Vehicles</TabsTrigger>
            <TabsTrigger value="turo" className="rounded-lg px-6 py-2.5 text-sm font-medium data-[state=active]:bg-background data-[state=active]:shadow-sm">Turo Metrics</TabsTrigger>
            <TabsTrigger value="goals" className="rounded-lg px-6 py-2.5 text-sm font-medium data-[state=active]:bg-background data-[state=active]:shadow-sm">Goals</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid gap-6 lg:grid-cols-2 2xl:grid-cols-3">
              <RevenueVsExpensesChart />
              <ProfitMarginChart />
              <div className="lg:col-span-2 2xl:col-span-1">
                <BookingMetricsCard />
              </div>
            </div>
            <div className="grid gap-6 lg:grid-cols-2 2xl:grid-cols-3">
              <CashFlowTimeline />
              <IdleDaysCostCard />
              <MaintenanceForecast />
            </div>
          </TabsContent>

          {/* Financial Tab */}
          <TabsContent value="financial" className="space-y-6">
            <div className="grid gap-6 lg:grid-cols-2 2xl:grid-cols-3">
              <div className="2xl:col-span-2">
                <RevenueVsExpensesChart />
              </div>
              <ExpenseDonutChart />
            </div>
            <div className="grid gap-6 lg:grid-cols-2 2xl:grid-cols-3">
              <CashFlowTimeline />
              <ProfitMarginChart />
              <div className="lg:col-span-2 2xl:col-span-1">
                <RevenueForecastChart />
              </div>
            </div>
          </TabsContent>

          {/* Vehicles Tab */}
          <TabsContent value="vehicles" className="space-y-6">
            <VehicleROILeaderboard />
            <div className="grid gap-6 lg:grid-cols-2 2xl:grid-cols-3">
              <DepreciationTracker />
              <CostPerMileChart />
              <IdleDaysCostCard />
            </div>
            
            {/* Vehicle Performance Grid */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5 text-primary" />
                  Vehicle Performance Summary
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 lg:grid-cols-2 2xl:grid-cols-3">
                  {[
                    { name: "Tesla Model 3", trips: 18, revenue: 5240, utilization: 75, roi: 42 },
                    { name: "BMW X5", trips: 15, revenue: 5700, utilization: 68, roi: 38 },
                    { name: "Mercedes C-Class", trips: 14, revenue: 4680, utilization: 62, roi: 35 },
                    { name: "Tesla Model Y", trips: 12, revenue: 4320, utilization: 58, roi: 32 },
                    { name: "Audi A4", trips: 16, revenue: 4640, utilization: 71, roi: 28 },
                    { name: "Porsche Cayenne", trips: 10, revenue: 6200, utilization: 52, roi: 45 },
                  ].map((vehicle, idx) => (
                    <div key={idx} className="p-4 border border-border rounded-xl hover:bg-muted/30 hover:border-primary/20 transition-all duration-200 group">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <p className="font-semibold text-foreground group-hover:text-primary transition-colors">{vehicle.name}</p>
                          <p className="text-sm text-muted-foreground">{vehicle.trips} trips this month</p>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-lg text-foreground">${vehicle.revenue.toLocaleString()}</p>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Utilization</span>
                          <span className="font-medium">{vehicle.utilization}%</span>
                        </div>
                        <Progress value={vehicle.utilization} className="h-1.5" />
                      </div>
                      <div className="flex items-center justify-between mt-3 pt-3 border-t border-border">
                        <span className="text-sm text-muted-foreground">ROI</span>
                        <span className="text-sm font-semibold text-success">{vehicle.roi}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Turo Metrics Tab */}
          <TabsContent value="turo" className="space-y-6">
            <BookingMetricsCard />
            <div className="grid gap-6 lg:grid-cols-2 2xl:grid-cols-3">
              <SeasonalDemandHeatmap />
              <RatingImpactChart />
              <div className="lg:col-span-2 2xl:col-span-1">
                <PeakHoursChart />
              </div>
            </div>
            <div className="grid gap-6 lg:grid-cols-2 2xl:grid-cols-3">
              <Card>
                <CardHeader>
                  <CardTitle>Trip Duration Analysis</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {[
                      { label: "Short (1-2 days)", value: 35, color: "bg-primary" },
                      { label: "Medium (3-5 days)", value: 45, color: "bg-success" },
                      { label: "Long (6+ days)", value: 20, color: "bg-chart-3" },
                    ].map((item, idx) => (
                      <div key={idx} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-foreground">{item.label}</span>
                          <span className="font-bold text-foreground">{item.value}%</span>
                        </div>
                        <div className="h-2 bg-muted rounded-full overflow-hidden">
                          <div className={`h-full ${item.color} rounded-full transition-all duration-500`} style={{ width: `${item.value}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Booking Insights</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="p-4 bg-gradient-to-br from-primary/5 to-transparent rounded-xl border border-primary/10">
                      <p className="text-sm text-muted-foreground">Peak Booking Day</p>
                      <p className="text-2xl font-bold text-foreground mt-1">Friday</p>
                    </div>
                    <div className="p-4 bg-gradient-to-br from-success/5 to-transparent rounded-xl border border-success/10">
                      <p className="text-sm text-muted-foreground">Most Popular Vehicle</p>
                      <p className="text-2xl font-bold text-foreground mt-1">Tesla Model 3</p>
                    </div>
                    <div className="p-4 bg-gradient-to-br from-chart-3/5 to-transparent rounded-xl border border-chart-3/10">
                      <p className="text-sm text-muted-foreground">Average Guest Rating</p>
                      <p className="text-2xl font-bold text-foreground mt-1">4.8 ★</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
              <Card className="lg:col-span-2 2xl:col-span-1">
                <CardHeader>
                  <CardTitle>Quick Stats</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-4 bg-muted/30 rounded-xl">
                      <p className="text-3xl font-bold text-primary">156</p>
                      <p className="text-sm text-muted-foreground mt-1">Total Bookings</p>
                    </div>
                    <div className="text-center p-4 bg-muted/30 rounded-xl">
                      <p className="text-3xl font-bold text-success">94%</p>
                      <p className="text-sm text-muted-foreground mt-1">Accept Rate</p>
                    </div>
                    <div className="text-center p-4 bg-muted/30 rounded-xl">
                      <p className="text-3xl font-bold text-chart-3">3.2</p>
                      <p className="text-sm text-muted-foreground mt-1">Avg Trip Days</p>
                    </div>
                    <div className="text-center p-4 bg-muted/30 rounded-xl">
                      <p className="text-3xl font-bold text-chart-4">$89</p>
                      <p className="text-sm text-muted-foreground mt-1">Avg Daily Rate</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Goals Tab */}
          <TabsContent value="goals" className="space-y-6">
            <div className="grid gap-6 lg:grid-cols-2 2xl:grid-cols-3">
              <GoalTracker />
              <Card>
                <CardHeader>
                  <CardTitle>YTD Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {[
                      { icon: DollarSign, label: "Total Revenue", value: "$367,200", color: "text-primary", bg: "bg-primary/10" },
                      { icon: Activity, label: "Total Trips", value: "892", color: "text-success", bg: "bg-success/10" },
                      { icon: Target, label: "Avg Utilization", value: "66.4%", color: "text-chart-3", bg: "bg-chart-3/10" },
                      { icon: TrendingUp, label: "Net Profit", value: "$115,400", color: "text-chart-4", bg: "bg-chart-4/10" },
                    ].map((item, idx) => (
                      <div key={idx} className="flex items-center justify-between p-3 rounded-xl hover:bg-muted/30 transition-colors">
                        <div className="flex items-center gap-3">
                          <div className={`p-2 rounded-lg ${item.bg}`}>
                            <item.icon className={`h-4 w-4 ${item.color}`} />
                          </div>
                          <span className="text-foreground">{item.label}</span>
                        </div>
                        <span className="font-bold text-foreground">{item.value}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
              <div className="lg:col-span-2 2xl:col-span-1">
                <RevenueForecastChart />
              </div>
            </div>
            <FleetGrowthSimulator />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Analytics;
