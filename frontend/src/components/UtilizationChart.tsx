import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { Activity, Car, TrendingUp, TrendingDown, Loader2 } from "lucide-react";
import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { vehiclesService, MonthlyUtilization } from "@/services/vehicles-service";

export const UtilizationChart = () => {
  const [selectedMonth, setSelectedMonth] = useState<MonthlyUtilization | null>(null);
  const [data, setData] = useState<MonthlyUtilization[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const loadUtilizationData = async () => {
      try {
        setLoading(true);
        const response = await vehiclesService.getMonthlyUtilization();
        setData(response.months);
      } catch (error) {
        console.error('Failed to load utilization data:', error);
        setData([]);
      } finally {
        setLoading(false);
      }
    };
    loadUtilizationData();
  }, []);
  
  const avgUtilization = data.length > 0 
    ? (data.reduce((acc, curr) => acc + curr.utilization, 0) / data.length).toFixed(0)
    : "0";
  
  const getBarColor = (value: number) => {
    if (value >= 90) return "hsl(var(--success))";
    if (value >= 75) return "hsl(var(--chart-2))";
    return "hsl(var(--chart-3))";
  };

  const getUtilizationColor = (value: number) => {
    if (value >= 90) return "text-success";
    if (value >= 75) return "text-chart-2";
    return "text-chart-3";
  };

  const handleBarClick = (data: MonthlyUtilization) => {
    setSelectedMonth(data);
  };
  
  if (loading) {
    return (
      <Card className="rounded-2xl shadow-lg border-border/50 overflow-hidden">
        <CardContent className="pt-6 flex items-center justify-center h-[400px]">
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
            <p className="text-muted-foreground">Loading utilization data...</p>
          </div>
        </CardContent>
      </Card>
    );
  }
  
  if (data.length === 0) {
    return (
      <Card className="rounded-2xl shadow-lg border-border/50 overflow-hidden">
        <CardHeader className="bg-gradient-to-br from-success/10 via-chart-2/5 to-transparent border-b border-border/50">
          <CardTitle className="text-lg font-bold flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-success animate-pulse" />
            Vehicle Utilization
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-6 flex items-center justify-center h-[400px]">
          <div className="flex flex-col items-center gap-2 text-center">
            <Activity className="w-12 h-12 text-muted-foreground opacity-50" />
            <p className="text-muted-foreground">No utilization data available</p>
            <p className="text-sm text-muted-foreground">Connect your Turo account and scrape trip data to see utilization.</p>
          </div>
        </CardContent>
      </Card>
    );
  }
  
  return (
    <>
      <Card className="rounded-2xl shadow-lg border-border/50 overflow-hidden animate-fade-in hover-scale group">
        <CardHeader className="bg-gradient-to-br from-success/10 via-chart-2/5 to-transparent border-b border-border/50">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg font-bold flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-success animate-pulse" />
              Vehicle Utilization
            </CardTitle>
            <div className="flex items-center gap-1.5 text-xs font-semibold text-foreground bg-muted/50 px-2.5 py-1 rounded-full">
              <Activity className="h-3 w-3" />
              {avgUtilization}% avg
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-6">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data}>
              <defs>
                <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="hsl(var(--success))" stopOpacity={1} />
                  <stop offset="100%" stopColor="hsl(var(--success))" stopOpacity={0.6} />
                </linearGradient>
              </defs>
              <CartesianGrid 
                strokeDasharray="3 3" 
                stroke="hsl(var(--border))" 
                opacity={0.3}
                vertical={false}
              />
              <XAxis 
                dataKey="month" 
                stroke="hsl(var(--muted-foreground))"
                fontSize={12}
                tickLine={false}
                axisLine={false}
              />
              <YAxis 
                stroke="hsl(var(--muted-foreground))"
                fontSize={12}
                tickFormatter={(value) => `${value}%`}
                tickLine={false}
                axisLine={false}
                domain={[0, 100]}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "12px",
                  boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
                }}
                formatter={(value: number) => [`${value}%`, "Utilization"]}
                labelStyle={{ color: "hsl(var(--foreground))", fontWeight: "600" }}
                cursor={{ fill: "hsl(var(--muted))", opacity: 0.1 }}
              />
              <Bar
                dataKey="utilization"
                radius={[12, 12, 0, 0]}
                maxBarSize={60}
                onClick={(data) => handleBarClick(data)}
                className="cursor-pointer"
              >
                {data.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={getBarColor(entry.utilization)}
                    className="hover:opacity-80 transition-opacity cursor-pointer"
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <p className="text-xs text-muted-foreground text-center mt-2">Click on a bar to view vehicle breakdown</p>
        </CardContent>
      </Card>

      {/* Month Detail Modal */}
      <Dialog open={!!selectedMonth} onOpenChange={() => setSelectedMonth(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-primary" />
              {selectedMonth?.month} Utilization Details
            </DialogTitle>
          </DialogHeader>
          
          {selectedMonth && (
            <div className="space-y-4">
              {/* Overall Stats */}
              <div className="bg-muted/30 rounded-lg p-4 text-center">
                <p className="text-sm text-muted-foreground mb-1">Fleet Utilization</p>
                <p className={`text-4xl font-bold ${getUtilizationColor(selectedMonth.utilization)}`}>
                  {selectedMonth.utilization}%
                </p>
                <div className="flex items-center justify-center gap-1 mt-1">
                  {selectedMonth.utilization >= 85 ? (
                    <>
                      <TrendingUp className="h-4 w-4 text-success" />
                      <span className="text-xs text-success font-medium">Above target</span>
                    </>
                  ) : (
                    <>
                      <TrendingDown className="h-4 w-4 text-warning" />
                      <span className="text-xs text-warning font-medium">Below target</span>
                    </>
                  )}
                </div>
              </div>

              {/* Per-Vehicle Breakdown */}
              <div className="space-y-3">
                <h4 className="font-semibold text-sm">Vehicle Breakdown</h4>
                {selectedMonth.vehicles.map((v, index) => (
                  <div key={index} className="bg-card border border-border rounded-lg p-3 space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Car className="h-4 w-4 text-primary" />
                        <span className="font-medium">{v.vehicle}</span>
                      </div>
                      <Badge variant={v.utilization >= 90 ? "default" : v.utilization >= 75 ? "secondary" : "outline"}>
                        {v.utilization}%
                      </Badge>
                    </div>
                    <Progress value={v.utilization} className="h-2" />
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>{v.trips} trips</span>
                      <span>{v.daysRented}/{v.totalDays} days rented</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
};
