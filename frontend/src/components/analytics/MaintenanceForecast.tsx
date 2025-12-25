import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Wrench, AlertTriangle, Clock } from "lucide-react";

const forecasts = [
  {
    vehicle: "Tesla Model 3",
    service: "Tire Rotation",
    cost: 120,
    dueIn: "2 weeks",
    priority: "medium",
    basedOn: "Mileage"
  },
  {
    vehicle: "BMW X5",
    service: "Oil Change",
    cost: 180,
    dueIn: "1 month",
    priority: "low",
    basedOn: "Time"
  },
  {
    vehicle: "Mercedes C-Class",
    service: "Brake Inspection",
    cost: 250,
    dueIn: "3 days",
    priority: "high",
    basedOn: "Mileage"
  },
  {
    vehicle: "Tesla Model Y",
    service: "Battery Check",
    cost: 0,
    dueIn: "1 week",
    priority: "medium",
    basedOn: "Time"
  },
  {
    vehicle: "Audi A4",
    service: "Fluid Top-up",
    cost: 85,
    dueIn: "5 days",
    priority: "high",
    basedOn: "Inspection"
  },
];

export const MaintenanceForecast = () => {
  const totalUpcoming = forecasts.reduce((sum, item) => sum + item.cost, 0);
  const urgentCount = forecasts.filter(f => f.priority === "high").length;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Wrench className="h-5 w-5 text-chart-3" />
          Maintenance Forecast
        </CardTitle>
        <CardDescription>
          Predicted costs: ${totalUpcoming} • {urgentCount} urgent items
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {forecasts.map((forecast, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between p-4 border border-border rounded-lg hover:bg-muted/30 transition-colors"
            >
              <div className="flex items-start gap-3 flex-1">
                {forecast.priority === "high" && (
                  <AlertTriangle className="h-5 w-5 text-destructive mt-0.5" />
                )}
                {forecast.priority === "medium" && (
                  <Clock className="h-5 w-5 text-warning mt-0.5" />
                )}
                {forecast.priority === "low" && (
                  <Wrench className="h-5 w-5 text-muted-foreground mt-0.5" />
                )}
                <div className="flex-1">
                  <p className="font-medium text-foreground">{forecast.vehicle}</p>
                  <p className="text-sm text-muted-foreground">{forecast.service}</p>
                  <div className="flex gap-2 mt-1">
                    <Badge variant="outline" className="text-xs">
                      {forecast.basedOn}
                    </Badge>
                    <Badge
                      variant={
                        forecast.priority === "high"
                          ? "destructive"
                          : forecast.priority === "medium"
                          ? "secondary"
                          : "outline"
                      }
                      className="text-xs"
                    >
                      {forecast.priority}
                    </Badge>
                  </div>
                </div>
              </div>
              <div className="text-right">
                <p className="font-bold text-foreground">
                  {forecast.cost === 0 ? "Free" : `$${forecast.cost}`}
                </p>
                <p className="text-xs text-muted-foreground">Due in {forecast.dueIn}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Summary */}
        <div className="mt-4 p-4 bg-muted/30 rounded-lg">
          <div className="flex items-center justify-between">
            <span className="text-sm text-foreground">Total Upcoming (30 days)</span>
            <span className="text-lg font-bold text-foreground">${totalUpcoming}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};