import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown, Trophy } from "lucide-react";

const vehicles = [
  { name: "Tesla Model 3", roi: 42, totalProfit: 12400, depreciation: -8200, status: "positive" },
  { name: "BMW X5", roi: 38, totalProfit: 15200, depreciation: -12000, status: "positive" },
  { name: "Mercedes C-Class", roi: 35, totalProfit: 10800, depreciation: -9500, status: "positive" },
  { name: "Tesla Model Y", roi: 32, totalProfit: 11200, depreciation: -10200, status: "positive" },
  { name: "Audi A4", roi: 28, totalProfit: 9600, depreciation: -11000, status: "warning" },
];

export const VehicleROILeaderboard = () => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Trophy className="h-5 w-5 text-warning" />
          Vehicle ROI Leaderboard
        </CardTitle>
        <CardDescription>Ranked by return on investment</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {vehicles.map((vehicle, idx) => (
            <div 
              key={idx} 
              className="flex items-center justify-between p-4 border border-border rounded-lg hover:bg-muted/50 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted font-bold text-foreground">
                  {idx + 1}
                </div>
                <div>
                  <p className="font-medium text-foreground">{vehicle.name}</p>
                  <p className="text-sm text-muted-foreground">
                    Profit: ${vehicle.totalProfit.toLocaleString()} • Depreciation: ${Math.abs(vehicle.depreciation).toLocaleString()}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <div className="flex items-center gap-2">
                  <Badge variant={vehicle.status === "positive" ? "default" : "secondary"}>
                    {vehicle.roi}% ROI
                  </Badge>
                  {vehicle.roi > 30 ? (
                    <TrendingUp className="h-4 w-4 text-success" />
                  ) : (
                    <TrendingDown className="h-4 w-4 text-warning" />
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};