import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const data = [
  { month: "Jan", margin: 26 },
  { month: "Feb", margin: 27 },
  { month: "Mar", margin: 31 },
  { month: "Apr", margin: 27 },
  { month: "May", margin: 30 },
  { month: "Jun", margin: 33 },
  { month: "Jul", margin: 37 },
  { month: "Aug", margin: 35 },
  { month: "Sep", margin: 33 },
  { month: "Oct", margin: 33 },
  { month: "Nov", margin: 31 },
  { month: "Dec", margin: 35 },
];

export const ProfitMarginChart = () => {
  const avgMargin = (data.reduce((sum, item) => sum + item.margin, 0) / data.length).toFixed(1);
  const trend = data[data.length - 1].margin > data[0].margin ? "up" : "down";

  return (
    <Card>
      <CardHeader>
        <CardTitle>Profit Margin Trend</CardTitle>
        <CardDescription>
          Average: {avgMargin}% • Trend: {trend === "up" ? "📈 Improving" : "📉 Declining"}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={data}>
            <defs>
              <linearGradient id="marginGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(var(--chart-2))" stopOpacity={0.8} />
                <stop offset="95%" stopColor="hsl(var(--chart-2))" stopOpacity={0.1} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis 
              dataKey="month" 
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
            />
            <YAxis 
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
              tickFormatter={(value) => `${value}%`}
            />
            <Tooltip 
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "8px",
              }}
              formatter={(value: number) => [`${value}%`, "Profit Margin"]}
            />
            <Area 
              type="monotone" 
              dataKey="margin" 
              stroke="hsl(var(--chart-2))" 
              strokeWidth={2}
              fill="url(#marginGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};