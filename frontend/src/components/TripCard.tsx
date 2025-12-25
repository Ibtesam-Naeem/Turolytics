import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { MapPin, Gauge, Fuel, DollarSign, Route, AlertTriangle, Zap, Wrench, Navigation, User, Calendar } from "lucide-react";
import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";

interface TripCardProps {
  vehicleName: string;
  year: number;
  guestName: string;
  location: string;
  coordinates: string;
  fuelPercent: number;
  speed: number;
  status: "Active" | "Parked" | "Moving" | "Alert";
  kmsDriven: number;
  kmsAllowed: number;
  earnings: number;
  topSpeed: number;
  startDate?: string;
  startTime?: string;
  endDate?: string;
  endTime?: string;
  flags?: {
    rapidAcceleration?: number;
    hardBraking?: number;
    engineLight?: boolean;
  };
}

export const TripCard = ({
  vehicleName,
  year,
  guestName,
  location,
  coordinates,
  fuelPercent,
  speed,
  status,
  kmsDriven,
  kmsAllowed,
  earnings,
  topSpeed,
  startDate,
  startTime,
  endDate,
  endTime,
  flags,
}: TripCardProps) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case "Active":
      case "Moving":
        return "border-success/50 bg-success/10 text-success";
      case "Parked":
        return "border-primary/50 bg-primary/10 text-primary";
      case "Alert":
        return "border-warning/50 bg-warning/10 text-warning";
      default:
        return "border-muted bg-muted/50 text-muted-foreground";
    }
  };

  const distancePercent = (kmsDriven / kmsAllowed) * 100;
  const hasFlags = flags && (flags.rapidAcceleration || flags.hardBraking || flags.engineLight);

  return (
    <>
      <Card 
        className={`self-start rounded-2xl shadow-sm transition-all duration-300 cursor-pointer overflow-hidden border-l-4 hover:shadow-xl hover:-translate-y-1 ${
          status === "Moving" ? "border-l-success" : status === "Parked" ? "border-l-primary" : "border-l-warning"
        }`}
        onClick={() => setIsModalOpen(true)}
      >
        <CardContent className="p-5">
          <div className="space-y-4">
            {/* Header */}
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h3 className="text-base font-bold text-foreground">
                  {year} {vehicleName}
                </h3>
                <p className="text-sm text-muted-foreground mt-0.5">{guestName}</p>
              </div>
              <Badge className={`${getStatusColor(status)} border font-semibold`}>
                {status}
              </Badge>
            </div>

            {/* Location */}
            <div className="flex items-start gap-2 text-sm">
              <MapPin className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-foreground font-medium truncate">{location}</p>
                <p className="text-xs text-muted-foreground">{coordinates}</p>
              </div>
            </div>

            {/* Trip Dates */}
            {(startDate || endDate) && (
              <div className="flex items-start gap-2 text-sm">
                <Calendar className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                <div className="flex-1 min-w-0 space-y-1">
                  {startDate && (
                    <div>
                      <p className="text-xs text-muted-foreground">Started</p>
                      <p className="text-foreground font-medium">
                        {startDate}{startTime ? ` • ${startTime}` : ''}
                      </p>
                    </div>
                  )}
                  {endDate && (
                    <div>
                      <p className="text-xs text-muted-foreground">Returns</p>
                      <p className="text-foreground font-medium">
                        {endDate}{endTime ? ` • ${endTime}` : ''}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Fuel Progress */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <Fuel className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground font-medium">Fuel</span>
                </div>
                <span className={`font-bold ${fuelPercent < 30 ? 'text-warning' : 'text-foreground'}`}>
                  {fuelPercent}%
                </span>
              </div>
              <Progress value={fuelPercent} className="h-2" />
            </div>

            {/* Speed Indicator */}
            <div className="flex items-center justify-between rounded-xl bg-gradient-to-r from-muted/80 to-muted/40 px-4 py-3 border border-border/50">
              <div className="flex items-center gap-2">
                <Navigation className={`h-4 w-4 ${status === "Moving" ? 'text-success' : 'text-muted-foreground'}`} />
                <span className="text-sm font-medium text-muted-foreground">Current Speed</span>
              </div>
              <span className="text-xl font-bold text-foreground">{speed} mph</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Trip Detail Modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Navigation className="h-5 w-5 text-primary" />
              Trip Details
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            {/* Trip Header */}
            <div className="bg-muted/30 rounded-lg p-4">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-bold text-lg">{year} {vehicleName}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <User className="h-4 w-4 text-primary" />
                    <span className="text-sm font-medium">{guestName}</span>
                  </div>
                </div>
                <Badge className={`${getStatusColor(status)} border font-semibold`}>
                  {status}
                </Badge>
              </div>
            </div>

            {/* Location */}
            <div className="flex items-start gap-2 text-sm">
              <MapPin className="h-4 w-4 text-primary mt-0.5" />
              <div>
                <p className="font-medium">{location}</p>
                <p className="text-xs text-muted-foreground">{coordinates}</p>
              </div>
            </div>

            {/* Trip Dates */}
            {(startDate || endDate) && (
              <>
                <Separator />
                <div className="flex items-start gap-2 text-sm">
                  <Calendar className="h-4 w-4 text-primary mt-0.5" />
                  <div className="flex-1 space-y-2">
                    {startDate && (
                      <div>
                        <p className="text-xs text-muted-foreground mb-0.5">Trip Started</p>
                        <p className="font-medium">
                          {startDate}{startTime ? ` at ${startTime}` : ''}
                        </p>
                      </div>
                    )}
                    {endDate && (
                      <div>
                        <p className="text-xs text-muted-foreground mb-0.5">Returns</p>
                        <p className="font-medium">
                          {endDate}{endTime ? ` at ${endTime}` : ''}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </>
            )}

            <Separator />

            {/* Live Stats */}
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-muted/30 rounded-lg p-3">
                <div className="flex items-center gap-2 mb-1">
                  <Navigation className={`h-4 w-4 ${status === "Moving" ? 'text-success' : 'text-muted-foreground'}`} />
                  <span className="text-xs text-muted-foreground">Current Speed</span>
                </div>
                <p className="text-xl font-bold">{speed} mph</p>
              </div>
              <div className="bg-muted/30 rounded-lg p-3">
                <div className="flex items-center gap-2 mb-1">
                  <Gauge className="h-4 w-4 text-primary" />
                  <span className="text-xs text-muted-foreground">Top Speed</span>
                </div>
                <p className="text-xl font-bold">{topSpeed} mph</p>
              </div>
            </div>

            {/* Fuel */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <Fuel className="h-4 w-4 text-muted-foreground" />
                  <span className="font-medium">Fuel Level</span>
                </div>
                <span className={`font-bold ${fuelPercent < 30 ? 'text-warning' : 'text-foreground'}`}>
                  {fuelPercent}%
                </span>
              </div>
              <Progress value={fuelPercent} className="h-2" />
            </div>

            <Separator />

            {/* Distance Tracking */}
            <div className="space-y-2 bg-gradient-to-br from-primary/5 to-transparent rounded-xl p-4 border border-primary/10">
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <Route className="h-4 w-4 text-primary" />
                  <span className="font-medium">Distance Traveled</span>
                </div>
                <span className="font-bold">
                  {kmsDriven} / {kmsAllowed} km
                </span>
              </div>
              <Progress value={distancePercent} className="h-2" />
              {distancePercent > 90 && (
                <div className="flex items-center gap-1.5 mt-1">
                  <AlertTriangle className="h-3 w-3 text-warning" />
                  <p className="text-xs font-semibold text-warning">Near distance limit!</p>
                </div>
              )}
            </div>

            {/* Earnings */}
            <div className="flex items-center justify-between rounded-xl bg-gradient-to-r from-success/15 to-success/5 px-4 py-3 border border-success/20">
              <div className="flex items-center gap-2">
                <DollarSign className="h-5 w-5 text-success" />
                <span className="text-sm font-medium text-muted-foreground">Trip Earnings</span>
              </div>
              <span className="text-xl font-bold text-success">
                ${earnings.toLocaleString()}
              </span>
            </div>

            {/* Flags */}
            {hasFlags && (
              <>
                <Separator />
                <div className="space-y-2 bg-warning/5 rounded-xl p-4 border border-warning/20">
                  <h4 className="text-sm font-bold text-foreground flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-warning" />
                    Vehicle Alerts
                  </h4>
                  <div className="space-y-2">
                    {flags?.rapidAcceleration && flags.rapidAcceleration > 0 && (
                      <div className="flex items-center justify-between text-sm bg-card px-3 py-2 rounded-lg border border-warning/20">
                        <div className="flex items-center gap-2">
                          <Zap className="h-3.5 w-3.5 text-warning" />
                          <span className="font-medium">Rapid Acceleration</span>
                        </div>
                        <span className="font-bold text-warning">{flags.rapidAcceleration}x</span>
                      </div>
                    )}
                    {flags?.hardBraking && flags.hardBraking > 0 && (
                      <div className="flex items-center justify-between text-sm bg-card px-3 py-2 rounded-lg border border-warning/20">
                        <div className="flex items-center gap-2">
                          <AlertTriangle className="h-3.5 w-3.5 text-warning" />
                          <span className="font-medium">Hard Braking</span>
                        </div>
                        <span className="font-bold text-warning">{flags.hardBraking}x</span>
                      </div>
                    )}
                    {flags?.engineLight && (
                      <div className="flex items-center justify-between text-sm bg-card px-3 py-2 rounded-lg border border-destructive/20">
                        <div className="flex items-center gap-2">
                          <Wrench className="h-3.5 w-3.5 text-destructive" />
                          <span className="font-medium">Engine Light Active</span>
                        </div>
                        <Badge variant="destructive" className="text-xs font-bold">Check Now</Badge>
                      </div>
                    )}
                  </div>
                </div>
              </>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};