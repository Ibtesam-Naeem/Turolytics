import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const data = [
  { vehicle: "Tesla M3", costPerMile: 0.18, type: "EV" },
  { vehicle: "Tesla MY", costPerMile: 0.21, type: "EV" },
  { vehicle: "BMW X5", costPerMile: 0.45, type: "Gas" },
  { vehicle: "Mercedes C", costPerMile: 0.38, type: "Gas" },
  { vehicle: "Audi A4", costPerMile: 0.42, type: "Gas" },
];

export const CostPerMileChart = () => {
  const avgCost = (data.reduce((sum, item) => sum + item.costPerMile, 0) / data.length).toFixed(2);
  const evAvg = (data.filter(d => d.type === "EV").reduce((sum, item) => sum + item.costPerMile, 0) / 2).toFixed(2);
  const gasAvg = (data.filter(d => d.type === "Gas").reduce((sum, item) => sum + item.costPerMile, 0) / 3).toFixed(2);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Cost Per Mile Analysis</CardTitle>
        <CardDescription>
          Avg: ${avgCost}/mi • EV: ${evAvg}/mi • Gas: ${gasAvg}/mi
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis
              dataKey="vehicle"
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
            />
            <YAxis
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
              tickFormatter={(value) => `$${value}`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "8px",
              }}
              formatter={(value: number, name: string, props: any) => [
                `$${value}/mile (${props.payload.type})`,
                "Cost"
              ]}
            />
            <Bar dataKey="costPerMile" radius={[4, 4, 0, 0]}>
              {data.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.type === "EV" ? "hsl(var(--chart-2))" : "hsl(var(--chart-5))"}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>

        {/* Savings Info */}
        <div className="mt-4 p-4 bg-success/10 border border-success/20 rounded-lg">
          <p className="text-sm font-medium text-success">💡 EV Savings Potential</p>
          <p className="text-xs text-muted-foreground mt-1">
            EVs cost ${(parseFloat(gasAvg) - parseFloat(evAvg)).toFixed(2)}/mile less than gas vehicles
          </p>
        </div>
      </CardContent>
    </Card>
  );
};