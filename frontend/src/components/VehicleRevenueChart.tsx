import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";

const data = [
  { name: "Tesla Model 3", value: 5240, color: "hsl(var(--chart-1))" },
  { name: "BMW X5", value: 5700, color: "hsl(var(--chart-2))" },
  { name: "Mercedes C-Class", value: 4680, color: "hsl(var(--chart-3))" },
  { name: "Tesla Model Y", value: 4320, color: "hsl(var(--chart-4))" },
  { name: "Audi A4", value: 4640, color: "hsl(var(--chart-5))" },
];

const CustomLegend = () => {
  const total = data.reduce((sum, item) => sum + item.value, 0);
  
  return (
    <div className="grid grid-cols-1 gap-3 mt-6">
      {data.map((entry, index) => {
        const percentage = ((entry.value / total) * 100).toFixed(1);
        return (
          <div
            key={index}
            className="flex items-center justify-between p-3 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors"
          >
            <div className="flex items-center gap-3">
              <div
                className="w-3 h-3 rounded-full shadow-sm"
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-sm font-medium text-foreground">
                {entry.name}
              </span>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-xs text-muted-foreground font-medium">
                {percentage}%
              </span>
              <span className="text-sm font-bold text-foreground">
                ${entry.value.toLocaleString()}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export const VehicleRevenueChart = () => {
  const total = data.reduce((sum, item) => sum + item.value, 0);
  
  return (
    <Card className="rounded-2xl shadow-lg border-border/50 overflow-hidden">
      <CardHeader className="bg-gradient-to-br from-primary/5 via-chart-2/5 to-transparent border-b border-border/50">
        <CardTitle className="text-lg font-bold">Revenue by Vehicle</CardTitle>
      </CardHeader>
      <CardContent className="pt-8">
        <div className="relative">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={80}
                outerRadius={120}
                paddingAngle={2}
                dataKey="value"
                strokeWidth={0}
              >
                {data.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={entry.color}
                    className="hover:opacity-80 transition-opacity cursor-pointer"
                  />
                ))}
              </Pie>
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
            </PieChart>
          </ResponsiveContainer>
          
          {/* Center total */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="text-center">
              <div className="text-3xl font-bold text-foreground">
                ${(total / 1000).toFixed(1)}k
              </div>
              <div className="text-xs text-muted-foreground font-medium mt-1">
                Total Revenue
              </div>
            </div>
          </div>
        </div>
        
        <CustomLegend />
      </CardContent>
    </Card>
  );
};
