import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { Fuel, Gauge, MapPin, User, AlertTriangle, Zap, Timer } from "lucide-react";

interface VehicleBottomSheetProps {
  vehicle: {
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
  } | null;
  isOpen: boolean;
  onClose: () => void;
}

export const VehicleBottomSheet = ({ vehicle, isOpen, onClose }: VehicleBottomSheetProps) => {
  if (!vehicle) return null;

  const hasAlerts = vehicle.flags.speedAlerts > 0 || vehicle.flags.hardBraking > 0 || vehicle.flags.rapidAcceleration > 0;
  const fuelStatus = vehicle.fuel < 30 ? "critical" : vehicle.fuel < 60 ? "warning" : "good";
  const tripProgress = Math.min((vehicle.totalKm / vehicle.allowedKm) * 100, 100);
  const isOverLimit = vehicle.totalKm > vehicle.allowedKm;

  return (
    <Sheet open={isOpen} onOpenChange={onClose}>
      <SheetContent side="bottom" className="h-[85vh] rounded-t-3xl p-0">
        <div className="flex flex-col h-full">
          <SheetHeader className="p-6 pb-4">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <SheetTitle className="text-2xl font-bold mb-2">{vehicle.name}</SheetTitle>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <MapPin className="w-4 h-4" />
                  <span>{vehicle.location}</span>
                </div>
              </div>
              <Badge 
                variant={vehicle.status === "moving" ? "default" : "secondary"}
                className="capitalize text-xs px-3 py-1"
              >
                {vehicle.status}
              </Badge>
            </div>
          </SheetHeader>

          <Separator />

          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* Guest Info */}
            <div className="bg-muted/50 rounded-xl p-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
                  <User className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Current Guest</p>
                  <p className="font-semibold text-lg">{vehicle.guest}</p>
                </div>
              </div>
            </div>

            {/* Real-time Stats */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-card border rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Fuel className={`w-5 h-5 ${fuelStatus === "critical" ? "text-destructive" : fuelStatus === "warning" ? "text-warning" : "text-success"}`} />
                  <span className="text-xs text-muted-foreground uppercase">Fuel Level</span>
                </div>
                <p className="text-2xl font-bold">{vehicle.fuel}%</p>
                <Progress value={vehicle.fuel} className="mt-2 h-2" />
              </div>

              {vehicle.status === "moving" && (
                <div className="bg-card border rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Gauge className="w-5 h-5 text-primary" />
                    <span className="text-xs text-muted-foreground uppercase">Speed</span>
                  </div>
                  <p className="text-2xl font-bold">{vehicle.speed} mph</p>
                  <p className="text-xs text-muted-foreground mt-1">Current Speed</p>
                </div>
              )}

              {vehicle.status === "parked" && (
                <div className="bg-card border rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Timer className="w-5 h-5 text-muted-foreground" />
                    <span className="text-xs text-muted-foreground uppercase">Status</span>
                  </div>
                  <p className="text-2xl font-bold">Parked</p>
                  <p className="text-xs text-muted-foreground mt-1">Vehicle at Rest</p>
                </div>
              )}
            </div>

            {/* Trip Progress */}
            <div className="bg-card border rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs text-muted-foreground uppercase">Trip Progress</span>
                <span className="text-sm font-semibold">{Math.round(tripProgress)}%</span>
              </div>
              <div className="flex justify-between text-sm mb-2">
                <span className="font-bold">{vehicle.totalKm} km</span>
                <span className="text-muted-foreground">of {vehicle.allowedKm} km</span>
              </div>
              <Progress 
                value={tripProgress} 
                className={`h-3 ${isOverLimit ? "[&>*]:bg-destructive" : ""}`}
              />
              {isOverLimit && (
                <p className="text-xs text-destructive mt-2 flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" />
                  Exceeded allowed distance
                </p>
              )}
            </div>

            {/* Driving Alerts */}
            {hasAlerts && (
              <div className="bg-card border rounded-xl p-4">
                <div className="flex items-center gap-2 mb-3">
                  <AlertTriangle className="w-5 h-5 text-warning" />
                  <span className="text-sm font-semibold">Driving Alerts</span>
                </div>
                <div className="space-y-2">
                  {vehicle.flags.speedAlerts > 0 && (
                    <div className="flex items-center justify-between bg-warning/10 rounded-lg px-3 py-2">
                      <span className="text-sm">Speed Alerts</span>
                      <Badge variant="outline" className="bg-warning/20 text-warning border-warning/30">
                        {vehicle.flags.speedAlerts}
                      </Badge>
                    </div>
                  )}
                  {vehicle.flags.hardBraking > 0 && (
                    <div className="flex items-center justify-between bg-destructive/10 rounded-lg px-3 py-2">
                      <span className="text-sm">Hard Braking</span>
                      <Badge variant="outline" className="bg-destructive/20 text-destructive border-destructive/30">
                        {vehicle.flags.hardBraking}
                      </Badge>
                    </div>
                  )}
                  {vehicle.flags.rapidAcceleration > 0 && (
                    <div className="flex items-center justify-between bg-primary/10 rounded-lg px-3 py-2">
                      <span className="text-sm flex items-center gap-1">
                        <Zap className="w-4 h-4" />
                        Rapid Acceleration
                      </span>
                      <Badge variant="outline" className="bg-primary/20 text-primary border-primary/30">
                        {vehicle.flags.rapidAcceleration}
                      </Badge>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
};