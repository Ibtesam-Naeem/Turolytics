import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { AlertCircle, TrendingDown } from "lucide-react";

const vehicles = [
  { name: "Tesla Model 3", idleDays: 2, potentialRevenue: 170, utilizationRate: 75 },
  { name: "BMW X5", idleDays: 5, potentialRevenue: 450, utilizationRate: 68 },
  { name: "Mercedes C-Class", idleDays: 8, potentialRevenue: 640, utilizationRate: 62 },
  { name: "Tesla Model Y", idleDays: 10, potentialRevenue: 800, utilizationRate: 58 },
  { name: "Audi A4", idleDays: 4, potentialRevenue: 320, utilizationRate: 71 },
];

export const IdleDaysCostCard = () => {
  const totalIdleDays = vehicles.reduce((sum, v) => sum + v.idleDays, 0);
  const totalOpportunityCost = vehicles.reduce((sum, v) => sum + v.potentialRevenue, 0);
  const avgUtilization = vehicles.reduce((sum, v) => sum + v.utilizationRate, 0) / vehicles.length;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertCircle className="h-5 w-5 text-warning" />
          Idle Days Analysis
        </CardTitle>
        <CardDescription>
          {totalIdleDays} idle days this month • ${totalOpportunityCost.toLocaleString()} opportunity cost
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Summary Card */}
          <div className="p-4 bg-warning/10 border border-warning/20 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <TrendingDown className="h-4 w-4 text-warning" />
              <p className="text-sm font-medium text-warning">Opportunity Cost Impact</p>
            </div>
            <p className="text-2xl font-bold text-foreground">${totalOpportunityCost.toLocaleString()}</p>
            <p className="text-xs text-muted-foreground mt-1">
              Revenue lost to idle vehicles this month
            </p>
          </div>

          {/* Vehicle Breakdown */}
          <div className="space-y-3">
            {vehicles.map((vehicle, idx) => (
              <div key={idx} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-foreground">{vehicle.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {vehicle.idleDays} idle days • ${vehicle.potentialRevenue} lost
                    </p>
                  </div>
                  <span className="text-sm font-bold text-foreground">
                    {vehicle.utilizationRate}%
                  </span>
                </div>
                <Progress value={vehicle.utilizationRate} className="h-2" />
              </div>
            ))}
          </div>

          {/* Recommendations */}
          <div className="mt-4 p-4 bg-muted/30 rounded-lg space-y-2">
            <p className="text-sm font-medium text-foreground">💡 Recommendations</p>
            <ul className="text-xs text-muted-foreground space-y-1">
              <li>• Adjust pricing for Tesla Model Y and Mercedes to boost bookings</li>
              <li>• Consider promotional discounts during low-demand periods</li>
              <li>• Review and optimize vehicle listings and photos</li>
            </ul>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};