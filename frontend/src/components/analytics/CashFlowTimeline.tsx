import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const data = [
  { month: "Jan", cashFlow: 6380 },
  { month: "Feb", cashFlow: 7200 },
  { month: "Mar", cashFlow: 9100 },
  { month: "Apr", cashFlow: 7400 },
  { month: "May", cashFlow: 9200 },
  { month: "Jun", cashFlow: 10600 },
  { month: "Jul", cashFlow: 13100 },
  { month: "Aug", cashFlow: 11900 },
  { month: "Sep", cashFlow: 10400 },
  { month: "Oct", cashFlow: 9700 },
  { month: "Nov", cashFlow: 8900 },
  { month: "Dec", cashFlow: 11200 },
];

export const CashFlowTimeline = () => {
  const totalCashFlow = data.reduce((sum, item) => sum + item.cashFlow, 0);
  const avgCashFlow = (totalCashFlow / data.length).toFixed(0);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Cash Flow Analysis</CardTitle>
        <CardDescription>
          Total: ${totalCashFlow.toLocaleString()} • Avg: ${avgCashFlow}/month
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
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
              formatter={(value: number) => [`$${value.toLocaleString()}`, "Net Cash Flow"]}
            />
            <Bar dataKey="cashFlow" radius={[4, 4, 0, 0]}>
              {data.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={entry.cashFlow > 9000 ? "hsl(var(--chart-2))" : "hsl(var(--chart-1))"} 
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};