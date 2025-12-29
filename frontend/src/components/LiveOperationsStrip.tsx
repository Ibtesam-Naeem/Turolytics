import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Calendar, Route, DollarSign, Star, LogOut, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { tripsService, TripToday, NewBookingToday, CheckoutToday } from "@/services/trips-service";
import { turoService } from "@/services/turo-service";
import { dashboardService } from "@/services/dashboard-service";
import { useBouncieLiveData } from "@/hooks/useBouncieLiveData";
import { useRegionalSettings } from "@/contexts/RegionalSettingsContext";
import { formatDistance } from "@/lib/regional-utils";

interface OperationMetric {
  label: string;
  value: string | number;
  icon: typeof Calendar;
  detailType: "trips" | "miles" | "payments" | "bookings" | "checkouts";
}

interface LiveOperationsStripProps {
  turoConnected?: boolean | null;
}

export const LiveOperationsStrip = ({ turoConnected: propTuroConnected }: LiveOperationsStripProps) => {
  const navigate = useNavigate();
  const { distanceUnit } = useRegionalSettings();
  const { totalMilesToday, bouncieConnected: bouncieConnectedLive, liveVehicles } = useBouncieLiveData(60000); // Refresh every minute
  const [selectedMetric, setSelectedMetric] = useState<OperationMetric | null>(null);
  const [tripsToday, setTripsToday] = useState<TripToday[]>([]);
  const [newBookings, setNewBookings] = useState<NewBookingToday[]>([]);
  const [checkoutsToday, setCheckoutsToday] = useState<CheckoutToday[]>([]);
  const [loading, setLoading] = useState(true);
  const [turoConnected, setTuroConnected] = useState<boolean | null>(null);
  const [milesDrivenToday, setMilesDrivenToday] = useState<number>(0);
  const [upcomingPaymentsTotal, setUpcomingPaymentsTotal] = useState<number>(0);
  const [earningsBreakdown, setEarningsBreakdown] = useState<Array<{ type: string; amount: string; amount_numeric?: number }>>([]);

  useEffect(() => {
    const checkTuroConnection = async () => {
      // Use prop if provided, otherwise check ourselves
      if (propTuroConnected !== undefined) {
        setTuroConnected(propTuroConnected);
        return;
      }
      
      try {
        const status = await turoService.getIntegrationStatus();
        setTuroConnected(status.connected);
      } catch (error) {
        console.error('Failed to check Turo connection status:', error);
        setTuroConnected(false);
      }
    };

    const loadTodayData = async () => {
      const isConnected = propTuroConnected !== undefined ? propTuroConnected : turoConnected;
      if (isConnected === false) {
        setLoading(false);
        setMilesDrivenToday(0);
        setUpcomingPaymentsTotal(0);
        return;
      }
      
      try {
        setLoading(true);
        // Get trips that are currently in progress (happening today/right now)
        // Use getTripsToday which gets trips that started today or are active today
        const [tripsRes, bookingsRes, checkoutsRes, earningsRes] = await Promise.all([
          tripsService.getTripsToday(),
          tripsService.getNewBookingsToday(),
          tripsService.getCheckoutsToday(),
          dashboardService.getEarnings(),
        ]);
        
        setTripsToday(tripsRes.trips);
        setNewBookings(bookingsRes.bookings);
        setCheckoutsToday(checkoutsRes.checkouts);
        
        // Miles driven today comes from Bouncie live data hook
        // Will be updated automatically by useBouncieLiveData
        
        // Get upcoming payments from earnings breakdown
        setEarningsBreakdown(earningsRes.breakdown);
        const upcomingEarnings = earningsRes.breakdown.find(
          item => item.type && item.type.toLowerCase().includes('upcoming')
        );
        if (upcomingEarnings) {
          // Use amount_numeric if available, otherwise parse the amount string
          const amount = upcomingEarnings.amount_numeric || 0;
          setUpcomingPaymentsTotal(amount);
        } else {
          setUpcomingPaymentsTotal(0);
        }
      } catch (error) {
        console.error('Failed to load today data:', error);
        setTripsToday([]);
        setNewBookings([]);
        setCheckoutsToday([]);
        // Don't reset milesDrivenToday here - let Bouncie hook handle it
        setUpcomingPaymentsTotal(0);
      } finally {
        setLoading(false);
      }
    };

    checkTuroConnection().then(() => {
      loadTodayData();
    });
  }, [propTuroConnected, turoConnected]);

  // Update miles driven from Bouncie live data
  useEffect(() => {
    if (bouncieConnectedLive && totalMilesToday !== undefined) {
      setMilesDrivenToday(totalMilesToday);
    } else if (bouncieConnectedLive === false) {
      setMilesDrivenToday(0);
    }
  }, [bouncieConnectedLive, totalMilesToday]);

  const todayMetrics: OperationMetric[] = [
    {
      label: "Trips booked for today",
      value: loading ? "..." : tripsToday.length,
      icon: Calendar,
      detailType: "trips",
    },
    {
      label: distanceUnit === "miles" ? "Miles driven today" : "Kilometers driven today",
      value: loading ? "..." : formatDistance(milesDrivenToday, distanceUnit),
      icon: Route,
      detailType: "miles",
    },
    {
      label: "Upcoming Payments",
      value: loading ? "..." : `$${Math.round(upcomingPaymentsTotal)}`,
      icon: DollarSign,
      detailType: "payments",
    },
    {
      label: "New bookings today",
      value: loading ? "..." : newBookings.length,
      icon: Star,
      detailType: "bookings",
    },
    {
      label: "Checkouts today",
      value: loading ? "..." : checkoutsToday.length,
      icon: LogOut,
      detailType: "checkouts",
    },
  ];

  // Get real miles breakdown from Bouncie live data
  // Note: milesDrivenToday is stored in km, formatDistance will convert for display
  const milesBreakdown = liveVehicles
    .filter(v => v.milesDrivenToday && v.milesDrivenToday > 0)
    .map(v => ({
      vehicle: v.vehicleName,
      km: v.milesDrivenToday!, // Already in km
      driver: v.activeTrip ? "Active Trip" : "No active trip",
    }))
    .sort((a, b) => b.km - a.km)
    .slice(0, 10); // Top 10 vehicles

  const renderDetailContent = () => {
    if (!selectedMetric) return null;

    switch (selectedMetric.detailType) {
      case "trips":
        return (
          <div className="space-y-3">
            {turoConnected === false ? (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <p className="text-sm text-muted-foreground mb-4">Link your Turo account to view trips today.</p>
                <Button onClick={() => navigate('/settings')} variant="default" size="sm">
                  Connect Turo Account
                </Button>
              </div>
            ) : tripsToday.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">No trips today</p>
            ) : (
              tripsToday.map((trip) => (
                <div key={trip.id} className="flex items-center justify-between p-3 rounded-lg bg-muted/50 border border-border">
                  <div>
                    <p className="font-medium text-foreground">{trip.vehicle_name}</p>
                    <p className="text-sm text-muted-foreground">{trip.guest_name} • {trip.location}</p>
                  </div>
                  <Badge variant={trip.status?.toUpperCase().includes("PROGRESS") || trip.status?.toUpperCase().includes("ACTIVE") ? "default" : "secondary"}>
                    {trip.status}
                  </Badge>
                </div>
              ))
            )}
          </div>
        );

      case "miles":
        return (
          <div className="space-y-3">
            {bouncieConnectedLive === false ? (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <p className="text-sm text-muted-foreground mb-4">Connect your Bouncie account to view miles driven today.</p>
                <Button onClick={() => navigate('/settings?tab=integrations')} variant="default" size="sm">
                  Connect Bouncie
                </Button>
              </div>
            ) : milesBreakdown.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">No miles driven today</p>
            ) : (
              milesBreakdown.map((item, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-muted/50 border border-border">
                  <div>
                    <p className="font-medium text-foreground">{item.vehicle}</p>
                    <p className="text-sm text-muted-foreground">{item.driver}</p>
                  </div>
                  <p className="text-lg font-bold text-primary">{formatDistance(item.km, distanceUnit)}</p>
                </div>
              ))
            )}
          </div>
        );

      case "payments":
        return (
          <div className="space-y-3">
            {turoConnected === false ? (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <p className="text-sm text-muted-foreground mb-4">Link your Turo account to view upcoming payments.</p>
                <Button onClick={() => navigate('/settings')} variant="default" size="sm">
                  Connect Turo Account
                </Button>
              </div>
            ) : earningsBreakdown.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">No earnings data available</p>
            ) : (
              earningsBreakdown.map((item, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-muted/50 border border-border">
                  <div>
                    <p className="font-medium text-foreground">{item.type}</p>
                    {item.year && (
                      <p className="text-sm text-muted-foreground">Year: {item.year}</p>
                    )}
                  </div>
                  <p className="text-lg font-bold text-success">{item.amount || `$${item.amount_numeric?.toLocaleString() || '0'}`}</p>
                </div>
              ))
            )}
          </div>
        );

      case "bookings":
        return (
          <div className="space-y-3">
            {turoConnected === false ? (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <p className="text-sm text-muted-foreground mb-4">Link your Turo account to view new bookings.</p>
                <Button onClick={() => navigate('/settings')} variant="default" size="sm">
                  Connect Turo Account
                </Button>
              </div>
            ) : newBookings.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">No new bookings today</p>
            ) : (
              newBookings.map((booking) => (
                <div key={booking.id} className="flex items-center justify-between p-3 rounded-lg bg-muted/50 border border-border">
                  <div>
                    <p className="font-medium text-foreground">{booking.guest_name}</p>
                    <p className="text-sm text-muted-foreground">{booking.vehicle_name} • {booking.dates}</p>
                  </div>
                  <p className="text-lg font-bold text-chart-1">{booking.amount}</p>
                </div>
              ))
            )}
          </div>
        );

      case "checkouts":
        return (
          <div className="space-y-3">
            {turoConnected === false ? (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <p className="text-sm text-muted-foreground mb-4">Link your Turo account to view checkouts.</p>
                <Button onClick={() => navigate('/settings')} variant="default" size="sm">
                  Connect Turo Account
                </Button>
              </div>
            ) : checkoutsToday.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">No checkouts today</p>
            ) : (
              checkoutsToday.map((checkout) => (
                <div key={checkout.id} className="flex items-center justify-between p-3 rounded-lg bg-muted/50 border border-border">
                  <div>
                    <p className="font-medium text-foreground">{checkout.vehicle_name}</p>
                    <p className="text-sm text-muted-foreground">{checkout.guest_name} • {checkout.location}</p>
                  </div>
                  <Badge variant="outline" className="text-chart-4 border-chart-4">
                    {checkout.time}
                  </Badge>
                </div>
              ))
            )}
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <>
      <Card className="rounded-2xl shadow-md overflow-hidden border-border/50 glass-card w-full max-w-full">
        <CardContent className="p-5 w-full">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6 w-full">
            {todayMetrics.map((metric, index) => {
              const Icon = metric.icon;
              return (
                <div 
                  key={index} 
                  className="flex items-center gap-3 group cursor-pointer hover:bg-muted/50 rounded-xl p-2 -m-2 transition-all duration-200"
                  style={{ animationDelay: `${index * 100}ms` }}
                  onClick={() => setSelectedMetric(metric)}
                >
                  <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-primary/20 to-primary/10 flex items-center justify-center shrink-0 shadow-lg shadow-primary/10 group-hover:scale-110 transition-transform duration-300 border border-primary/20">
                    <Icon className="h-5 w-5 text-primary" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs text-muted-foreground font-semibold uppercase tracking-wider mb-0.5">
                      {metric.label}
                    </p>
                    <p className="text-2xl font-bold text-foreground">
                      {metric.value}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      <Dialog open={!!selectedMetric} onOpenChange={() => setSelectedMetric(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {selectedMetric && (
                <>
                  <selectedMetric.icon className="h-5 w-5 text-primary" />
                  {selectedMetric.label}
                </>
              )}
            </DialogTitle>
          </DialogHeader>
          <div className="mt-2">
            {renderDetailContent()}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};
