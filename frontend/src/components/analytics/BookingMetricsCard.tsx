import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp, Calendar, DollarSign, Clock } from "lucide-react";

export const BookingMetricsCard = () => {
  const metrics = [
    {
      label: "Booking Conversion",
      value: "68%",
      trend: "+5.2%",
      icon: TrendingUp,
      color: "text-chart-2"
    },
    {
      label: "Average Daily Rate",
      value: "$85",
      trend: "+$8",
      icon: DollarSign,
      color: "text-chart-1"
    },
    {
      label: "Avg Trip Length",
      value: "4.2 days",
      trend: "+0.3 days",
      icon: Calendar,
      color: "text-chart-3"
    },
    {
      label: "Booking Lead Time",
      value: "12 days",
      trend: "-2 days",
      icon: Clock,
      color: "text-chart-4"
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Turo Booking Metrics</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 sm:grid-cols-2">
          {metrics.map((metric, idx) => (
            <div key={idx} className="flex items-start gap-3 p-4 border border-border rounded-lg">
              <div className={`mt-1 ${metric.color}`}>
                <metric.icon className="h-5 w-5" />
              </div>
              <div className="flex-1">
                <p className="text-sm text-muted-foreground">{metric.label}</p>
                <p className="text-2xl font-bold text-foreground mt-1">{metric.value}</p>
                <p className="text-sm text-success mt-1">{metric.trend} from last month</p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};