import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const weeks = ["Week 1", "Week 2", "Week 3", "Week 4"];

// Demand data: 0-100 representing booking density
const demandData = [
  [45, 52, 48, 50], // Jan
  [48, 55, 52, 58], // Feb
  [65, 72, 68, 75], // Mar
  [70, 75, 72, 78], // Apr
  [82, 88, 85, 90], // May
  [95, 98, 92, 96], // Jun
  [98, 95, 100, 97], // Jul
  [92, 90, 88, 85], // Aug
  [75, 72, 70, 68], // Sep
  [62, 65, 60, 58], // Oct
  [50, 48, 52, 55], // Nov
  [58, 62, 68, 72], // Dec
];

export const SeasonalDemandHeatmap = () => {
  const getColor = (value: number) => {
    if (value >= 90) return "bg-chart-2";
    if (value >= 75) return "bg-chart-1";
    if (value >= 60) return "bg-chart-3";
    if (value >= 45) return "bg-chart-4";
    return "bg-muted";
  };

  const getIntensity = (value: number) => {
    if (value >= 90) return "opacity-100";
    if (value >= 75) return "opacity-80";
    if (value >= 60) return "opacity-60";
    if (value >= 45) return "opacity-40";
    return "opacity-20";
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Seasonal Demand Heatmap</CardTitle>
        <CardDescription>Booking density by month and week</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {/* Legend */}
          <div className="flex items-center gap-4 mb-4 text-xs text-muted-foreground">
            <span>Low</span>
            <div className="flex gap-1">
              {[20, 40, 60, 80, 100].map((val) => (
                <div
                  key={val}
                  className={`h-3 w-3 rounded ${getColor(val)} ${getIntensity(val)}`}
                />
              ))}
            </div>
            <span>High</span>
          </div>

          {/* Heatmap Grid */}
          <div className="overflow-x-auto">
            <div className="min-w-[600px]">
              {/* Week Headers */}
              <div className="flex gap-1 mb-2">
                <div className="w-16" />
                {weeks.map((week, idx) => (
                  <div key={idx} className="flex-1 text-xs text-center text-muted-foreground">
                    {week}
                  </div>
                ))}
              </div>

              {/* Month Rows */}
              {months.map((month, monthIdx) => (
                <div key={monthIdx} className="flex gap-1 mb-1 items-center">
                  <div className="w-16 text-xs text-muted-foreground">{month}</div>
                  {demandData[monthIdx].map((value, weekIdx) => (
                    <div
                      key={weekIdx}
                      className={`flex-1 h-12 rounded ${getColor(value)} ${getIntensity(value)} hover:ring-2 hover:ring-primary transition-all cursor-pointer flex items-center justify-center text-xs font-medium text-foreground group relative`}
                    >
                      <span className="opacity-0 group-hover:opacity-100">{value}</span>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>

          {/* Peak Season Info */}
          <div className="mt-4 p-3 bg-muted/50 rounded-lg">
            <p className="text-sm text-foreground font-medium">Peak Season: June - August</p>
            <p className="text-xs text-muted-foreground mt-1">
              Highest demand during summer months with 90%+ booking rates
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};