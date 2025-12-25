import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, ComposedChart } from "recharts";

const data = [
  { month: "Jan", revenue: 24580, expenses: 18200 },
  { month: "Feb", revenue: 26300, expenses: 19100 },
  { month: "Mar", revenue: 28900, expenses: 19800 },
  { month: "Apr", revenue: 27600, expenses: 20200 },
  { month: "May", revenue: 30200, expenses: 21000 },
  { month: "Jun", revenue: 32100, expenses: 21500 },
  { month: "Jul", revenue: 35400, expenses: 22300 },
  { month: "Aug", revenue: 33800, expenses: 21900 },
  { month: "Sep", revenue: 31200, expenses: 20800 },
  { month: "Oct", revenue: 29800, expenses: 20100 },
  { month: "Nov", revenue: 28400, expenses: 19500 },
  { month: "Dec", revenue: 31600, expenses: 20400 },
];

export const RevenueVsExpensesChart = () => {
  const netProfit = data.reduce((sum, item) => sum + (item.revenue - item.expenses), 0);
  const avgMargin = ((netProfit / data.reduce((sum, item) => sum + item.revenue, 0)) * 100).toFixed(1);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Revenue vs Expenses</CardTitle>
        <CardDescription>
          Net Profit: ${netProfit.toLocaleString()} • Avg Margin: {avgMargin}%
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis 
              dataKey="month" 
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
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
              formatter={(value: number) => [`$${value.toLocaleString()}`, ""]}
            />
            <Legend />
            <Bar dataKey="revenue" fill="hsl(var(--chart-1))" radius={[4, 4, 0, 0]} name="Revenue" />
            <Line 
              type="monotone" 
              dataKey="expenses" 
              stroke="hsl(var(--chart-5))" 
              strokeWidth={3}
              name="Expenses"
              dot={{ fill: "hsl(var(--chart-5))", r: 4 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};