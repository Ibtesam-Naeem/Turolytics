import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Car, TrendingUp, Star, Loader2 } from "lucide-react";
import { useState, useEffect } from "react";
import { vehiclesService, VehiclePerformance } from "@/services/vehicles-service";

const getRankColor = (rank: number) => {
  switch (rank) {
    case 1:
      return "from-yellow-500 to-yellow-600";
    case 2:
      return "from-slate-400 to-slate-500";
    case 3:
      return "from-amber-600 to-amber-700";
    case 4:
      return "from-blue-500 to-blue-600";
    case 5:
      return "from-purple-500 to-purple-600";
    default:
      return "from-muted to-muted";
  }
};

const getRankBadgeVariant = (rank: number): "default" | "secondary" | "outline" => {
  return rank <= 5 ? "default" : "outline";
};

export const PerformanceLeaderboard = () => {
  const [topVehicles, setTopVehicles] = useState<VehiclePerformance[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadTopPerformers = async () => {
      try {
        setLoading(true);
        const response = await vehiclesService.getTopPerformers(5);
        setTopVehicles(response.vehicles);
      } catch (error) {
        console.error('Failed to load top performers:', error);
        setTopVehicles([]);
      } finally {
        setLoading(false);
      }
    };
    loadTopPerformers();
  }, []);

  return (
    <Card className="rounded-xl shadow-sm h-full flex flex-col w-full max-w-full">
      <CardHeader className="pb-3 w-full">
        <CardTitle className="text-lg font-semibold flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-primary" />
          Top Performers
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 overflow-auto w-full">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : topVehicles.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <Car className="h-8 w-8 text-muted-foreground mb-2" />
            <p className="text-sm text-muted-foreground">No vehicle data available</p>
          </div>
        ) : (
        <div className="space-y-3 w-full">
          {topVehicles.map((vehicle) => (
            <div
              key={vehicle.rank}
              className="relative flex items-start gap-3 rounded-lg border bg-card p-3 transition-all hover:shadow-md hover:scale-[1.02]"
            >
              {/* Rank Badge */}
              <div className="flex-shrink-0">
                <div
                  className={`flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br ${getRankColor(
                    vehicle.rank
                  )} text-white font-bold text-sm shadow-sm`}
                >
                  {vehicle.rank}
                </div>
              </div>

              {/* Vehicle Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <Car className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                    <span className="font-semibold text-sm truncate">
                      {vehicle.vehicle_name}
                    </span>
                  </div>
                  <Badge variant={getRankBadgeVariant(vehicle.rank)} className="text-xs flex-shrink-0">
                    {vehicle.trips} trips
                  </Badge>
                </div>

                {/* Metrics */}
                <div className="mt-2 grid grid-cols-3 gap-2 text-xs">
                  <div>
                    <div className="text-muted-foreground">Revenue</div>
                    <div className="font-semibold text-foreground">${vehicle.revenue.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Utilization</div>
                    <div className="font-semibold text-foreground">{vehicle.utilization}%</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground flex items-center gap-0.5">
                      <Star className="h-3 w-3" />
                      Rating
                    </div>
                    <div className="font-semibold text-foreground">{vehicle.rating.toFixed(1)}</div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
        )}
      </CardContent>
    </Card>
  );
};
