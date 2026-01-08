import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from "recharts";
import { TrendingUp, Loader2 } from "lucide-react";
import { useState, useEffect } from "react";
import { dashboardService, MonthlyRevenue } from "@/services/dashboard-service";

export const RevenueChart = () => {
  const [data, setData] = useState<MonthlyRevenue[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const loadRevenueData = async () => {
      try {
        setLoading(true);
        const response = await dashboardService.getMonthlyRevenue();
        setData(response.months);
      } catch (error) {
        console.error('Failed to load revenue data:', error);
        setData([]);
      } finally {
        setLoading(false);
      }
    };
    loadRevenueData();
  }, []);
  
  const hasData = data.length > 0;
  const calculateGrowth = () => {
    if (!hasData || data.length < 2) return null;
    const firstRevenue = data[0].revenue;
    const lastRevenue = data[data.length - 1].revenue;
    if (firstRevenue === 0 || !isFinite(firstRevenue) || !isFinite(lastRevenue)) return null;
    const growthValue = ((lastRevenue - firstRevenue) / firstRevenue * 100);
    if (!isFinite(growthValue) || isNaN(growthValue)) return null;
    return growthValue.toFixed(1);
  };
  const growth = calculateGrowth();
  
  return (
    <Card className="rounded-2xl shadow-lg border-border/50 overflow-hidden animate-fade-in hover-scale group">
      <CardHeader className="bg-gradient-to-br from-primary/10 via-primary/5 to-transparent border-b border-border/50">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-bold flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-primary animate-pulse" />
            Revenue Trend
          </CardTitle>
          {hasData && growth !== null ? (
            <div className="flex items-center gap-1.5 text-xs font-semibold text-success bg-success/10 px-2.5 py-1 rounded-full">
              <TrendingUp className="h-3 w-3" />
              +{growth}%
            </div>
          ) : hasData ? (
            <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground bg-muted/10 px-2.5 py-1 rounded-full">
              -
            </div>
          ) : null}
        </div>
      </CardHeader>
      <CardContent className="pt-6">
        {loading ? (
          <div className="flex flex-col items-center justify-center h-[300px] text-center">
            <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
            <p className="text-sm text-muted-foreground">Loading revenue data...</p>
          </div>
        ) : hasData ? (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={data}>
            <defs>
              <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
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
              tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "12px",
                boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
              }}
              formatter={(value: number) => [`$${value.toLocaleString()}`, "Revenue"]}
              labelStyle={{ color: "hsl(var(--foreground))", fontWeight: "600" }}
            />
            <Area
              type="monotone"
              dataKey="revenue"
              stroke="hsl(var(--primary))"
              strokeWidth={3}
              fill="url(#revenueGradient)"
              dot={{ 
                fill: "hsl(var(--primary))", 
                r: 5,
                strokeWidth: 2,
                stroke: "hsl(var(--card))"
              }}
              activeDot={{ 
                r: 7,
                strokeWidth: 2,
                stroke: "hsl(var(--card))"
              }}
            />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex flex-col items-center justify-center h-[300px] text-center">
            <TrendingUp className="h-12 w-12 text-muted-foreground mb-4 opacity-50" />
            <p className="text-lg font-semibold text-foreground mb-2">No Revenue Data</p>
            <p className="text-sm text-muted-foreground max-w-sm">
              Revenue trends will appear here once you start completing trips. Connect your Turo account to begin tracking.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
