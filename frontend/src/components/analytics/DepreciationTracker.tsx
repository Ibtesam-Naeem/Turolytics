import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const data = [
  { vehicle: "Tesla M3", purchase: 45000, current: 36800, earnings: 12400 },
  { vehicle: "BMW X5", purchase: 55000, current: 43000, earnings: 15200 },
  { vehicle: "Mercedes C", purchase: 42000, current: 32500, earnings: 10800 },
  { vehicle: "Tesla MY", purchase: 50000, current: 39800, earnings: 11200 },
  { vehicle: "Audi A4", purchase: 48000, current: 37000, earnings: 9600 },
];

export const DepreciationTracker = () => {
  const totalDepreciation = data.reduce((sum, v) => sum + (v.purchase - v.current), 0);
  const totalEarnings = data.reduce((sum, v) => sum + v.earnings, 0);
  const netPosition = totalEarnings - totalDepreciation;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Depreciation vs Earnings</CardTitle>
        <CardDescription>
          Total Depreciation: ${totalDepreciation.toLocaleString()} • Net Position: ${netPosition.toLocaleString()}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis 
              type="number"
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
              tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
            />
            <YAxis 
              type="category"
              dataKey="vehicle" 
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
              width={100}
            />
            <Tooltip 
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "8px",
              }}
              formatter={(value: number, name: string) => {
                const labels: Record<string, string> = {
                  purchase: "Purchase Price",
                  current: "Current Value",
                  earnings: "Total Earnings"
                };
                return [`$${value.toLocaleString()}`, labels[name] || name];
              }}
            />
            <Bar dataKey="purchase" fill="hsl(var(--muted))" radius={[0, 4, 4, 0]} name="Purchase" />
            <Bar dataKey="current" fill="hsl(var(--chart-3))" radius={[0, 4, 4, 0]} name="Current" />
            <Bar dataKey="earnings" fill="hsl(var(--chart-2))" radius={[0, 4, 4, 0]} name="Earnings" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};