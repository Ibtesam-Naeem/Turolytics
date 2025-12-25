import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Clock } from "lucide-react";

const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const hours = ["12am", "6am", "12pm", "6pm"];

// Activity data: 0-100 representing booking/checkout activity
const activityData = [
  [20, 45, 75, 85], // Mon
  [18, 42, 72, 80], // Tue
  [22, 48, 78, 88], // Wed
  [25, 52, 82, 92], // Thu
  [35, 68, 95, 98], // Fri
  [65, 85, 92, 88], // Sat
  [70, 90, 85, 75], // Sun
];

export const PeakHoursChart = () => {
  const getColor = (value: number) => {
    if (value >= 85) return "bg-chart-2";
    if (value >= 70) return "bg-chart-1";
    if (value >= 50) return "bg-chart-3";
    if (value >= 30) return "bg-warning";
    return "bg-muted";
  };

  const getIntensity = (value: number) => {
    if (value >= 85) return "opacity-100";
    if (value >= 70) return "opacity-80";
    if (value >= 50) return "opacity-60";
    if (value >= 30) return "opacity-40";
    return "opacity-25";
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="h-5 w-5 text-chart-1" />
          Peak Activity Hours
        </CardTitle>
        <CardDescription>Booking and checkout activity heatmap</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Legend */}
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <span>Low Activity</span>
            <div className="flex gap-1">
              {[25, 40, 60, 80, 100].map((val) => (
                <div
                  key={val}
                  className={`h-3 w-3 rounded ${getColor(val)} ${getIntensity(val)}`}
                />
              ))}
            </div>
            <span>High Activity</span>
          </div>

          {/* Heatmap Grid */}
          <div className="overflow-x-auto">
            <div className="min-w-[400px]">
              {/* Hour Headers */}
              <div className="flex gap-1 mb-2">
                <div className="w-12" />
                {hours.map((hour, idx) => (
                  <div key={idx} className="flex-1 text-xs text-center text-muted-foreground">
                    {hour}
                  </div>
                ))}
              </div>

              {/* Day Rows */}
              {days.map((day, dayIdx) => (
                <div key={dayIdx} className="flex gap-1 mb-1 items-center">
                  <div className="w-12 text-xs text-muted-foreground font-medium">{day}</div>
                  {activityData[dayIdx].map((value, hourIdx) => (
                    <div
                      key={hourIdx}
                      className={`flex-1 h-14 rounded-lg ${getColor(value)} ${getIntensity(value)} hover:ring-2 hover:ring-primary transition-all cursor-pointer flex items-center justify-center text-xs font-bold text-foreground group relative`}
                    >
                      <span className="opacity-0 group-hover:opacity-100">{value}%</span>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>

          {/* Peak Times Info */}
          <div className="grid grid-cols-2 gap-3 mt-4">
            <div className="p-3 bg-chart-2/10 border border-chart-2/20 rounded-lg">
              <p className="text-xs text-muted-foreground mb-1">Busiest Day</p>
              <p className="text-lg font-bold text-foreground">Friday</p>
              <p className="text-xs text-muted-foreground">6pm peak</p>
            </div>
            <div className="p-3 bg-chart-1/10 border border-chart-1/20 rounded-lg">
              <p className="text-xs text-muted-foreground mb-1">Quietest Time</p>
              <p className="text-lg font-bold text-foreground">Tue 6am</p>
              <p className="text-xs text-muted-foreground">18% activity</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};