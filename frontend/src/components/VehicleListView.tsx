import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Fuel, Gauge, MapPin, User, AlertTriangle } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";

interface Vehicle {
  id: string;
  name: string;
  coordinates: [number, number];
  status: "moving" | "parked";
  speed: number;
  guest: string;
  location: string;
  fuel: number;
  totalKm: number;
  allowedKm: number;
  flags: {
    speedAlerts: number;
    hardBraking: number;
    rapidAcceleration: number;
  };
}

interface VehicleListViewProps {
  vehicles: Vehicle[];
  onVehicleSelect: (vehicle: Vehicle) => void;
}

export const VehicleListView = ({ vehicles, onVehicleSelect }: VehicleListViewProps) => {
  return (
    <ScrollArea className="h-[calc(100vh-180px)]">
      <div className="grid gap-4 p-6">
        {vehicles.map((vehicle) => {
          const hasAlerts = vehicle.flags.speedAlerts > 0 || vehicle.flags.hardBraking > 0 || vehicle.flags.rapidAcceleration > 0;
          const fuelStatus = vehicle.fuel < 30 ? "critical" : vehicle.fuel < 60 ? "warning" : "good";
          const tripProgress = Math.min((vehicle.totalKm / vehicle.allowedKm) * 100, 100);
          const isOverLimit = vehicle.totalKm > vehicle.allowedKm;

          return (
            <Card 
              key={vehicle.id} 
              className="p-5 hover:shadow-lg transition-all cursor-pointer border-2 hover:border-primary/50"
              onClick={() => onVehicleSelect(vehicle)}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-bold mb-1">{vehicle.name}</h3>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
                    <MapPin className="w-4 h-4" />
                    <span>{vehicle.location}</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <User className="w-4 h-4 text-muted-foreground" />
                    <span className="font-medium">{vehicle.guest}</span>
                  </div>
                </div>
                <Badge 
                  variant={vehicle.status === "moving" ? "default" : "secondary"}
                  className="capitalize"
                >
                  {vehicle.status}
                </Badge>
              </div>

              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="bg-muted/50 rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <Fuel className={`w-4 h-4 ${fuelStatus === "critical" ? "text-destructive" : fuelStatus === "warning" ? "text-warning" : "text-success"}`} />
                    <span className="text-xs text-muted-foreground">Fuel</span>
                  </div>
                  <p className="text-lg font-bold">{vehicle.fuel}%</p>
                </div>

                <div className="bg-muted/50 rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <Gauge className="w-4 h-4 text-primary" />
                    <span className="text-xs text-muted-foreground">Speed</span>
                  </div>
                  <p className="text-lg font-bold">{vehicle.speed} mph</p>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">Trip Progress</span>
                  <span className="font-semibold">{vehicle.totalKm} / {vehicle.allowedKm} km</span>
                </div>
                <Progress 
                  value={tripProgress} 
                  className={`h-2 ${isOverLimit ? "[&>*]:bg-destructive" : ""}`}
                />
              </div>

              {hasAlerts && (
                <div className="flex items-center gap-2 mt-3 pt-3 border-t">
                  <AlertTriangle className="w-4 h-4 text-warning" />
                  <div className="flex gap-2 text-xs">
                    {vehicle.flags.speedAlerts > 0 && (
                      <Badge variant="outline" className="text-xs">
                        {vehicle.flags.speedAlerts} Speed
                      </Badge>
                    )}
                    {vehicle.flags.hardBraking > 0 && (
                      <Badge variant="outline" className="text-xs">
                        {vehicle.flags.hardBraking} Brake
                      </Badge>
                    )}
                    {vehicle.flags.rapidAcceleration > 0 && (
                      <Badge variant="outline" className="text-xs">
                        {vehicle.flags.rapidAcceleration} Accel
                      </Badge>
                    )}
                  </div>
                </div>
              )}
            </Card>
          );
        })}
      </div>
    </ScrollArea>
  );
};