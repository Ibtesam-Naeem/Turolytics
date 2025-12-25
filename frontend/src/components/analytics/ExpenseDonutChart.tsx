import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip, Legend } from "recharts";

const data = [
  { name: "Maintenance", value: 42000, color: "hsl(var(--chart-1))" },
  { name: "Fuel/Charging", value: 28000, color: "hsl(var(--chart-2))" },
  { name: "Insurance", value: 36000, color: "hsl(var(--chart-3))" },
  { name: "Cleaning", value: 18000, color: "hsl(var(--chart-4))" },
  { name: "Depreciation", value: 52000, color: "hsl(var(--chart-5))" },
  { name: "Other", value: 12000, color: "hsl(var(--muted))" },
];

export const ExpenseDonutChart = () => {
  const total = data.reduce((sum, item) => sum + item.value, 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Expense Breakdown</CardTitle>
        <CardDescription>Total Expenses: ${total.toLocaleString()}</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              paddingAngle={2}
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip 
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "8px",
              }}
              formatter={(value: number) => [
                `$${value.toLocaleString()} (${((value / total) * 100).toFixed(1)}%)`,
                ""
              ]}
            />
            <Legend 
              verticalAlign="bottom" 
              height={36}
              iconType="circle"
              formatter={(value, entry: any) => {
                const percentage = ((entry.payload.value / total) * 100).toFixed(0);
                return `${value} (${percentage}%)`;
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};