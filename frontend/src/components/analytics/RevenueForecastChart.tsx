import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const data = [
  { month: "Jan", actual: 24580, forecast: null },
  { month: "Feb", actual: 26300, forecast: null },
  { month: "Mar", actual: 28900, forecast: null },
  { month: "Apr", actual: 27600, forecast: null },
  { month: "May", actual: 30200, forecast: null },
  { month: "Jun", actual: 32100, forecast: null },
  { month: "Jul", actual: 35400, forecast: null },
  { month: "Aug", actual: 33800, forecast: null },
  { month: "Sep", actual: 31200, forecast: null },
  { month: "Oct", actual: 29800, forecast: null },
  { month: "Nov", actual: 28400, forecast: null },
  { month: "Dec", actual: 31600, forecast: null },
  { month: "Jan '25", actual: null, forecast: 33200 },
  { month: "Feb '25", actual: null, forecast: 35400 },
  { month: "Mar '25", actual: null, forecast: 37800 },
  { month: "Apr '25", actual: null, forecast: 36200 },
  { month: "May '25", actual: null, forecast: 39100 },
  { month: "Jun '25", actual: null, forecast: 41500 },
];

export const RevenueForecastChart = () => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Revenue Forecast</CardTitle>
        <CardDescription>12-month historical + 6-month projection</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={data}>
            <defs>
              <linearGradient id="actualGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(var(--chart-1))" stopOpacity={0.8} />
                <stop offset="95%" stopColor="hsl(var(--chart-1))" stopOpacity={0.1} />
              </linearGradient>
              <linearGradient id="forecastGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(var(--chart-4))" stopOpacity={0.5} />
                <stop offset="95%" stopColor="hsl(var(--chart-4))" stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis 
              dataKey="month" 
              stroke="hsl(var(--muted-foreground))"
              fontSize={10}
              angle={-45}
              textAnchor="end"
              height={60}
            />
            <YAxis 
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
              tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
            />
            <Tooltip 
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "8px",
              }}
              formatter={(value: number, name: string) => [
                `$${value?.toLocaleString() || 0}`, 
                name === "actual" ? "Actual" : "Forecast"
              ]}
            />
            <Area 
              type="monotone" 
              dataKey="actual" 
              stroke="hsl(var(--chart-1))" 
              strokeWidth={2}
              fill="url(#actualGradient)"
              name="actual"
            />
            <Area 
              type="monotone" 
              dataKey="forecast" 
              stroke="hsl(var(--chart-4))" 
              strokeWidth={2}
              strokeDasharray="5 5"
              fill="url(#forecastGradient)"
              name="forecast"
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};