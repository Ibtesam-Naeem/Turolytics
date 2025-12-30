import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertTriangle, Droplet, Wrench, CheckCircle2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { bouncieService, BouncieDTCCode } from "@/services/bouncie-service";
import { useBouncieLiveData } from "@/hooks/useBouncieLiveData";
import { vehiclesService } from "@/services/vehicles-service";

interface VehicleInfo {
  name: string;
  location: string;
  details: string;
}

interface AlertItem {
  icon: React.ElementType;
  label: string;
  count: number;
  severity: "success" | "warning" | "destructive";
  vehicles: VehicleInfo[];
}

export const FleetHealthCard = () => {
  const navigate = useNavigate();
  const [bouncieConnected, setBouncieConnected] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);
  const [dtcCodes, setDtcCodes] = useState<BouncieDTCCode[]>([]);
  const [loadingDtcCodes, setLoadingDtcCodes] = useState(false);
  const [maintenanceVehicles, setMaintenanceVehicles] = useState<VehicleInfo[]>([]);
  const [loadingMaintenance, setLoadingMaintenance] = useState(false);
  
  // Get live vehicle data for fuel levels
  const { liveVehicles, bouncieConnected: liveDataConnected } = useBouncieLiveData(60000); // Refresh every minute

  useEffect(() => {
    const checkBouncieConnection = async () => {
      try {
        const status = await bouncieService.getIntegrationStatus();
        setBouncieConnected(status.connected);
      } catch (error) {
        console.error('Failed to check Bouncie connection status:', error);
        setBouncieConnected(false);
      } finally {
        setLoading(false);
      }
    };

    checkBouncieConnection();
  }, []);

  // Use live data connection status if available, otherwise use checked status
  const isConnected = liveDataConnected !== null ? liveDataConnected : bouncieConnected;

  // Fetch DTC codes when connected
  useEffect(() => {
    const fetchDtcCodes = async () => {
      if (!isConnected) {
        setDtcCodes([]);
        return;
      }

      try {
        setLoadingDtcCodes(true);
        const result = await bouncieService.getDTCCodes(undefined, undefined, true, 100, 0);
        setDtcCodes(result.codes || []);
      } catch (error) {
        console.error('Failed to fetch DTC codes:', error);
        setDtcCodes([]);
      } finally {
        setLoadingDtcCodes(false);
      }
    };

    fetchDtcCodes();
    // Refresh DTC codes every 2 minutes
    const interval = setInterval(fetchDtcCodes, 120000);
    return () => clearInterval(interval);
  }, [isConnected]);

  // Fetch maintenance vehicles
  useEffect(() => {
    const fetchMaintenanceVehicles = async () => {
      try {
        setLoadingMaintenance(true);
        const response = await vehiclesService.getVehicles({ include_stats: false, limit: 100 });
        const maintenance = response.vehicles
          .filter(v => v.status_mapped === "maintenance" || (v.status && v.status.toLowerCase().includes("maintenance")))
          .map(v => ({
            name: v.name + (v.year ? ` ${v.year}` : ''),
            location: v.license_plate || "No license plate",
            details: `Status: ${v.status || "Maintenance"}`
          }));
        setMaintenanceVehicles(maintenance);
      } catch (error) {
        console.error('Failed to fetch maintenance vehicles:', error);
        setMaintenanceVehicles([]);
      } finally {
        setLoadingMaintenance(false);
      }
    };

    fetchMaintenanceVehicles();
    // Refresh maintenance vehicles every 2 minutes
    const interval = setInterval(fetchMaintenanceVehicles, 120000);
    return () => clearInterval(interval);
  }, []);

  // Calculate low fuel vehicles (fuel level < 10%)
  const lowFuelVehicles = liveVehicles.filter(vehicle => {
    const fuelLevel = vehicle.fuelLevel;
    return fuelLevel !== null && fuelLevel !== undefined && fuelLevel < 10;
  });

  // Get active DTC codes grouped by vehicle
  const engineAlertVehicles = dtcCodes
    .filter(code => code.is_active)
    .reduce((acc, code) => {
      const vehicleName = code.vehicle_name || `Vehicle ${code.imei}`;
      const existing = acc.find(v => v.name === vehicleName);
      if (existing) {
        existing.details = `${existing.details}, ${code.code}`;
      } else {
        acc.push({
          name: vehicleName,
          location: `IMEI: ${code.imei}`,
          details: `${code.code}${code.description ? ` - ${code.description}` : ''}`
        });
      }
      return acc;
    }, [] as VehicleInfo[]);

  const alerts: AlertItem[] = [
    {
      icon: Wrench,
      label: "Maintenance required",
      count: maintenanceVehicles.length,
      severity: maintenanceVehicles.length > 0 ? "warning" : "success",
      vehicles: maintenanceVehicles
    },
    {
      icon: Droplet,
      label: "Low fuel",
      count: lowFuelVehicles.length,
      severity: lowFuelVehicles.length > 0 ? "warning" : "success",
      vehicles: lowFuelVehicles.map(vehicle => ({
        name: vehicle.vehicleName,
        location: vehicle.location 
          ? `${vehicle.location.lat.toFixed(4)}, ${vehicle.location.lon.toFixed(4)}`
          : "Location unknown",
        details: `Fuel: ${vehicle.fuelLevel?.toFixed(1) || 'N/A'}%`
      }))
    },
    {
      icon: AlertTriangle,
      label: "Engine alerts",
      count: engineAlertVehicles.length,
      severity: engineAlertVehicles.length > 0 ? "destructive" : "success",
      vehicles: engineAlertVehicles
    }
  ];

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "destructive":
        return "text-destructive";
      case "warning":
        return "text-warning";
      case "success":
        return "text-success";
      default:
        return "text-muted-foreground";
    }
  };

  const getSeverityBg = (severity: string) => {
    switch (severity) {
      case "destructive":
        return "bg-gradient-to-br from-destructive/20 to-destructive/10 border-destructive/20";
      case "warning":
        return "bg-gradient-to-br from-warning/20 to-warning/10 border-warning/20";
      case "success":
        return "bg-gradient-to-br from-success/20 to-success/10 border-success/20";
      default:
        return "bg-muted border-border";
    }
  };

  return (
    <Card className="rounded-2xl shadow-sm border-border/50">
      <CardHeader className="pb-4">
        <CardTitle className="text-lg font-bold flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-primary" />
          Fleet Health
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading || loadingDtcCodes || loadingMaintenance ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <p className="text-sm text-muted-foreground">Loading...</p>
          </div>
        ) : isConnected === false ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <AlertTriangle className="h-12 w-12 text-muted-foreground mb-4 opacity-50" />
            <p className="text-lg font-semibold text-foreground mb-2">Connect Bouncie to View Fleet Health</p>
            <p className="text-sm text-muted-foreground max-w-sm mb-4">
              Connect your Bouncie account to monitor vehicle health, fuel levels, engine alerts, and maintenance needs in real-time.
            </p>
            <Button 
              onClick={() => navigate('/settings?tab=integrations')}
              variant="default" 
              size="sm"
            >
              Connect Bouncie
            </Button>
          </div>
        ) : alerts.every(alert => alert.count === 0) ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <CheckCircle2 className="h-12 w-12 text-success mb-4 opacity-50" />
            <p className="text-lg font-semibold text-foreground mb-2">All Systems Healthy</p>
            <p className="text-sm text-muted-foreground max-w-sm">
              Your fleet is in good condition. Vehicle health alerts will appear here when maintenance is needed or issues are detected.
            </p>
          </div>
        ) : (
          <Accordion type="single" collapsible className="space-y-2.5">
            {alerts.map((alert, index) => {
            const Icon = alert.icon;
            return (
              <AccordionItem 
                key={index} 
                value={`item-${index}`}
                className="border-2 border-border/50 rounded-xl overflow-hidden hover:border-primary/30 transition-colors"
              >
                <AccordionTrigger className="hover:no-underline px-4 py-3.5 [&[data-state=open]]:border-b-2 [&[data-state=open]]:bg-muted/30">
                  <div className="flex items-center justify-between w-full pr-2">
                    <div className="flex items-center gap-3">
                      <div className={`rounded-lg p-2.5 border ${getSeverityBg(alert.severity)} shadow-sm`}>
                        <Icon className={`h-4 w-4 ${getSeverityColor(alert.severity)}`} />
                      </div>
                      <span className="text-sm font-bold text-foreground">
                        {alert.label}
                      </span>
                    </div>
                    <Badge
                      variant={alert.count === 0 ? "secondary" : "destructive"}
                      className={`font-bold ${
                        alert.count === 0 
                          ? "bg-success/15 text-success hover:bg-success/25 border border-success/30" 
                          : "shadow-md"
                      }`}
                    >
                      {alert.count}
                    </Badge>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="px-4 pb-4">
                  {alert.vehicles.length > 0 ? (
                    <div className="space-y-2.5 pt-3">
                      {alert.vehicles.map((vehicle, vIndex) => (
                        <div 
                          key={vIndex}
                          className="rounded-lg bg-gradient-to-br from-muted/60 to-muted/30 p-3.5 space-y-1.5 border border-border/50 hover:border-primary/30 transition-colors"
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-bold text-foreground">
                              {vehicle.name}
                            </span>
                          </div>
                          <p className="text-xs text-muted-foreground font-medium">
                            📍 {vehicle.location}
                          </p>
                          <p className="text-xs text-foreground font-semibold bg-card/50 px-2 py-1 rounded">
                            {vehicle.details}
                          </p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground pt-2 font-medium text-center py-2">
                      ✓ No vehicles with this alert
                    </p>
                  )}
                </AccordionContent>
              </AccordionItem>
            );
          })}
          </Accordion>
        )}
      </CardContent>
    </Card>
  );
};
