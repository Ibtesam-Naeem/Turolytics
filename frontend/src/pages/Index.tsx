import { DollarSign, Car, Calendar as CalendarIcon, Wallet, Star, RefreshCw, Route } from "lucide-react";
import { KPICard } from "@/components/KPICard";
import { TripCard } from "@/components/TripCard";
import { RevenueChart } from "@/components/RevenueChart";
import { UtilizationChart } from "@/components/UtilizationChart";
import { CalendarWidget } from "@/components/CalendarWidget";
import { PerformanceLeaderboard } from "@/components/PerformanceLeaderboard";
import { ActivityFeed } from "@/components/ActivityFeed";
import { UpcomingTripsCard } from "@/components/UpcomingTripsCard";
import { FleetHealthCard } from "@/components/FleetHealthCard";
import { UpcomingMaintenanceTimeline } from "@/components/UpcomingMaintenanceTimeline";
import { LiveOperationsStrip } from "@/components/LiveOperationsStrip";

import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { toast } from "@/hooks/use-toast";
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { dashboardService } from "@/services/dashboard-service";
import { tripsService, UpcomingTrip, CurrentTrip } from "@/services/trips-service";
import { turoService } from "@/services/turo-service";
import { useBouncieLiveData } from "@/hooks/useBouncieLiveData";
import { bouncieService } from "@/services/bouncie-service";
import { vehiclesService, Vehicle } from "@/services/vehicles-service";

const Index = () => {
  const navigate = useNavigate();
  const { liveVehicles, getVehicleLiveData } = useBouncieLiveData(60000); // Refresh every minute
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [turoConnected, setTuroConnected] = useState<boolean | null>(null);
  const [stats, setStats] = useState({
    totalRevenue: 0,
    activeVehicles: 0,
    snoozedVehicles: 0,
    maintenanceVehicles: 0,
    inactiveVehicles: 0,
    upcomingTrips: 0,
    averageRating: 0,
    totalReviews: 0,
  });

  const loadDashboardStats = async () => {
    try {
      setIsLoading(true);
      const dashboardStats = await dashboardService.getDashboardStats();
      setStats(dashboardStats);
    } catch (error) {
      console.error('Failed to load dashboard stats:', error);
      toast({
        title: "Error loading dashboard",
        description: "Failed to fetch dashboard statistics. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardStats();
  }, []);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    toast({
      title: "Refreshing data...",
      description: "Scraping latest Turo data and updating dashboard",
    });
    
    try {
      // Check Turo connection first
      await checkTuroConnection();
      
      // Trigger a full data scrape (endpoint will use stored credentials if Turo is connected)
      try {
        const scrapeResult = await turoService.scrape('all');
        console.log('Scraping task started:', scrapeResult);
        toast({
          title: "Scraping started",
          description: `Scraping all Turo data (Task: ${scrapeResult.task_id.substring(0, 8)}...)`,
        });
      } catch (scrapeError: any) {
        console.error('Failed to start scraping:', scrapeError);
        // If scraping fails (e.g., Turo not connected), just refresh existing data
        const errorMessage = scrapeError?.message || 'Turo not connected or credentials missing';
        if (turoConnected) {
          toast({
            title: "Scraping failed",
            description: errorMessage,
            variant: "destructive",
          });
        }
      }
      
      // Refresh dashboard data (this will show the latest scraped data)
      await Promise.all([
        loadDashboardStats(),
        loadUpcomingTrips(),
        loadCurrentTrips(),
      ]);
      
      toast({
        title: "Data refreshed",
        description: turoConnected 
          ? "Scraping in progress. Dashboard will update when scraping completes."
          : "Dashboard has been updated with latest data",
      });
    } catch (error) {
      console.error('Error during refresh:', error);
      toast({
        title: "Refresh error",
        description: "Failed to refresh some data. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsRefreshing(false);
    }
  };

  // Format currency
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  // Format rating
  const formatRating = (rating: number) => {
    return rating.toFixed(1);
  };

  const [upcomingTrips, setUpcomingTrips] = useState<Array<{
    id: string;
    vehicleName: string;
    guestName: string;
    pickupLocation: string;
    dropoffLocation: string;
    earnings: number;
    kmsAllowed: number;
    startDate: string;
  }>>([]);
  const [upcomingTripsLoading, setUpcomingTripsLoading] = useState(true);
  const [currentTrips, setCurrentTrips] = useState<Array<{
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
    flags?: {
      rapidAcceleration?: number;
      hardBraking?: number;
      engineLight?: boolean;
    };
  }>>([]);
  const [currentTripsLoading, setCurrentTripsLoading] = useState(true);
  const [showActiveVehiclesDialog, setShowActiveVehiclesDialog] = useState(false);
  const [activeVehicles, setActiveVehicles] = useState<Vehicle[]>([]);
  const [activeVehiclesLoading, setActiveVehiclesLoading] = useState(false);

  const loadUpcomingTrips = async () => {
    try {
      setUpcomingTripsLoading(true);
      const response = await tripsService.getUpcomingTrips(50);
      
      // Map API response to component format
      const mappedTrips = response.trips.map((trip: UpcomingTrip) => ({
        id: trip.id.toString(),
        vehicleName: trip.vehicle_name,
        guestName: trip.guest_name,
        pickupLocation: trip.pickup_location,
        dropoffLocation: trip.dropoff_location,
        earnings: Math.round(trip.earnings || 0),
        kmsAllowed: trip.kms_allowed || 0,
        startDate: trip.start_date,
      }));
      
      setUpcomingTrips(mappedTrips);
    } catch (error) {
      console.error('Failed to load upcoming trips:', error);
      setUpcomingTrips([]);
    } finally {
      setUpcomingTripsLoading(false);
    }
  };

  const loadCurrentTrips = async () => {
    try {
      setCurrentTripsLoading(true);
      const response = await tripsService.getCurrentTrips(50);
      
      // Get vehicle mappings to match Turo trips with Bouncie IMEIs
      let vehicleMappings: Map<number, string> = new Map();
      try {
        const mappingsResponse = await bouncieService.getVehicleMappings(100, 0);
        mappingsResponse.mappings.forEach(m => {
          if (m.vehicle_id) {
            vehicleMappings.set(m.vehicle_id, m.imei);
          }
        });
      } catch (err) {
        console.error('Failed to load vehicle mappings:', err);
      }
      
      // Map API response to TripCard format and merge with Bouncie live data
      const mappedTrips = response.trips.map((trip: CurrentTrip) => {
        // Try to find Bouncie live data for this vehicle
        const imei = vehicleMappings.get(trip.vehicle_id || 0);
        const liveData = imei ? liveVehicles.find(v => v.imei === imei) : undefined;
        
        // Determine status from Bouncie or Turo data
        let status: "Active" | "Parked" | "Moving" | "Alert" = "Active";
        if (liveData?.status === "moving") {
          status = "Moving";
        } else if (liveData?.status === "parked") {
          status = "Parked";
        } else if (trip.status === "Moving") {
          status = "Moving";
        } else if (trip.status === "Parked") {
          status = "Parked";
        }
        
        return {
          vehicleName: trip.vehicle_name,
          year: trip.vehicle_year || new Date().getFullYear(),
          guestName: trip.guest_name,
          location: liveData?.location 
            ? `${liveData.location.lat.toFixed(4)}, ${liveData.location.lon.toFixed(4)}`
            : trip.location,
          coordinates: liveData?.location 
            ? `${liveData.location.lat}, ${liveData.location.lon}`
            : trip.coordinates || "N/A",
          fuelPercent: liveData?.fuelLevel !== undefined 
            ? Math.round(liveData.fuelLevel) 
            : (trip.fuel_percent ?? 75),
          speed: liveData?.speed || trip.speed || 0,
          status: status,
          kmsDriven: trip.kms_driven || 0,
          kmsAllowed: trip.kms_allowed || 0,
          earnings: Math.round(trip.earnings || 0),
          topSpeed: liveData?.activeTrip?.maxSpeed || trip.top_speed || 0,
          startDate: trip.start_date,
          startTime: trip.start_time,
          endDate: trip.end_date,
          endTime: trip.end_time,
          flags: {
            // Use real Bouncie data if available
            rapidAcceleration: liveData?.flags?.rapidAcceleration,
            hardBraking: liveData?.flags?.hardBraking,
            engineLight: liveData?.flags?.engineLight || false,
          },
        };
      });
      
      setCurrentTrips(mappedTrips);
    } catch (error) {
      console.error('Failed to load current trips:', error);
      setCurrentTrips([]);
    } finally {
      setCurrentTripsLoading(false);
    }
  };

  const checkTuroConnection = async () => {
    try {
      const status = await turoService.getIntegrationStatus();
      setTuroConnected(status.connected);
    } catch (error) {
      console.error('Failed to check Turo connection status:', error);
      setTuroConnected(false);
    }
  };

  const loadActiveVehicles = async () => {
    try {
      setActiveVehiclesLoading(true);
      const response = await vehiclesService.getVehicles({
        include_stats: true,
        limit: 1000,
      });
      
      // Show all vehicles, sorted by status (active first)
      const allVehicles = response.vehicles.sort((a, b) => {
        const aStatus = (a.status || '').trim().toLowerCase();
        const bStatus = (b.status || '').trim().toLowerCase();
        const aIsActive = aStatus === 'listed' || aStatus === 'available';
        const bIsActive = bStatus === 'listed' || bStatus === 'available';
        
        if (aIsActive && !bIsActive) return -1;
        if (!aIsActive && bIsActive) return 1;
        return 0;
      });
      
      setActiveVehicles(allVehicles);
    } catch (error) {
      console.error('Failed to load vehicles:', error);
      setActiveVehicles([]);
      toast({
        title: "Error loading vehicles",
        description: "Failed to fetch vehicles. Please try again.",
        variant: "destructive",
      });
    } finally {
      setActiveVehiclesLoading(false);
    }
  };

  const handleActiveVehiclesClick = () => {
    setShowActiveVehiclesDialog(true);
    if (activeVehicles.length === 0) {
      loadActiveVehicles();
    }
  };

  useEffect(() => {
    checkTuroConnection();
    loadUpcomingTrips();
    loadCurrentTrips();
  }, []);

  // Reload current trips when Bouncie live data updates
  useEffect(() => {
    if (liveVehicles.length > 0 && !currentTripsLoading) {
      loadCurrentTrips();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [liveVehicles]);

  return (
    <div className="min-h-screen bg-background">
      <div className="flex">
        {/* Main Content Area */}
        <div className="flex-1 p-3 lg:p-4 space-y-3 overflow-auto">
          {/* Header */}
          <div className="animate-fade-in flex items-center justify-between">
            <div>
              <h1 className="text-xl sm:text-2xl font-bold text-foreground">
                Turolytics
              </h1>
              <p className="text-xs text-muted-foreground">Your fleet at a glance</p>
            </div>
            <Button
              onClick={handleRefresh}
              disabled={isRefreshing}
              variant="outline"
              size="sm"
              className="gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>

          {/* KPI Cards */}
          <div className="grid gap-2 grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
            <KPICard 
              title="Total Revenue" 
              value={isLoading ? "..." : formatCurrency(stats.totalRevenue)} 
              trend={isLoading ? "" : "From completed trips"} 
              trendPositive={true} 
              icon={DollarSign} 
            />
            <div onClick={handleActiveVehiclesClick} className="cursor-pointer">
              <KPICard 
                title="Active Vehicles" 
                value={isLoading ? "..." : stats.activeVehicles.toString()} 
                trend={isLoading ? "" : (() => {
                  const parts = [];
                  if (stats.snoozedVehicles > 0) parts.push(`${stats.snoozedVehicles} snoozed`);
                  if (stats.maintenanceVehicles > 0) parts.push(`${stats.maintenanceVehicles} in maintenance`);
                  if (stats.inactiveVehicles > 0) parts.push(`${stats.inactiveVehicles} inactive`);
                  return parts.length > 0 ? parts.join(', ') : "All vehicles active";
                })()} 
                trendPositive={stats.snoozedVehicles === 0 && stats.maintenanceVehicles === 0 && stats.inactiveVehicles === 0} 
                icon={Car} 
              />
            </div>
            <KPICard 
              title="Upcoming Trips" 
              value={isLoading ? "..." : stats.upcomingTrips.toString()} 
              trend={isLoading ? "" : "Scheduled trips"} 
              trendPositive={true} 
              icon={CalendarIcon} 
            />
            <KPICard 
              title="Bank Balance" 
              value="$0" 
              trend="" 
              trendPositive={true} 
              icon={Wallet} 
            />
            <KPICard 
              title="Average Rating" 
              value={isLoading ? "..." : formatRating(stats.averageRating)} 
              trend={isLoading ? "" : `${stats.totalReviews} total reviews`} 
              trendPositive={true} 
              icon={Star} 
            />
          </div>

          {/* Live Operations Strip */}
          <LiveOperationsStrip turoConnected={turoConnected} />
          
          {/* Upcoming Trips */}
          <UpcomingTripsCard 
            trips={upcomingTrips} 
            turoConnected={turoConnected}
            onConnectClick={() => navigate('/settings?tab=integrations')}
          />

          {/* Current Trips Section */}
          <div className="rounded-lg border bg-card shadow-sm p-3 lg:p-4 h-[450px]">
            <h2 className="mb-3 text-base font-bold text-foreground flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-success animate-pulse" />
              Current Trips
            </h2>
            {currentTripsLoading ? (
              <div className="flex items-center justify-center h-[320px]">
                <p className="text-muted-foreground">Loading current trips...</p>
              </div>
            ) : turoConnected === false ? (
              <div className="flex flex-col items-center justify-center h-[320px] text-center">
                <Route className="h-12 w-12 text-muted-foreground mb-4 opacity-50" />
                <p className="text-lg font-semibold text-foreground mb-2">Link Turo Account</p>
                <p className="text-sm text-muted-foreground mb-4">Connect your Turo account to view current trips.</p>
                <Button 
                  onClick={() => navigate('/settings?tab=integrations')}
                  variant="default" 
                  size="sm"
                >
                  Connect Turo Account
                </Button>
              </div>
            ) : currentTrips.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-[320px] text-center">
                <Route className="h-12 w-12 text-muted-foreground mb-4 opacity-50" />
                <p className="text-lg font-semibold text-foreground mb-2">No current trips</p>
                <p className="text-sm text-muted-foreground">You don't have any active trips at the moment.</p>
              </div>
            ) : (
              <ScrollArea className="h-[320px]">
                <div className="grid gap-2 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 pr-4">
                  {currentTrips.map((trip, index) => (
                    <TripCard key={index} {...trip} />
                  ))}
                </div>
              </ScrollArea>
            )}
          </div>

          {/* Charts */}
          <div className="grid gap-3 grid-cols-1 lg:grid-cols-2">
            <RevenueChart />
            <UtilizationChart />
          </div>

          {/* Fleet Operations */}
          <div className="grid gap-3 grid-cols-1 md:grid-cols-2 xl:grid-cols-3">
            <FleetHealthCard />
            <UpcomingMaintenanceTimeline />
            <ActivityFeed />
          </div>
        </div>

        {/* Right Sidebar - Calendar & Leaderboard (Fixed) */}
        <aside className="hidden xl:flex flex-col w-[280px] 2xl:w-[320px] border-l border-border bg-card/30 p-3 gap-3 shrink-0 fixed right-0 top-12 h-[calc(100vh-3rem)] overflow-y-auto z-10">
          <CalendarWidget />
          <PerformanceLeaderboard />
        </aside>
        
        {/* Spacer for fixed sidebar */}
        <div className="hidden xl:block w-[280px] 2xl:w-[320px] shrink-0" />
      </div>

      {/* Active Vehicles Dialog */}
      <Dialog open={showActiveVehiclesDialog} onOpenChange={setShowActiveVehiclesDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Car className="h-5 w-5 text-primary" />
              All Vehicles
            </DialogTitle>
          </DialogHeader>
          <div className="mt-2">
            {activeVehiclesLoading ? (
              <div className="flex items-center justify-center py-8">
                <p className="text-sm text-muted-foreground">Loading vehicles...</p>
              </div>
            ) : activeVehicles.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">No vehicles found</p>
            ) : (
              <div className="space-y-3 max-h-[400px] overflow-y-auto">
                {activeVehicles.map((vehicle) => {
                  const status = (vehicle.status || '').trim().toLowerCase();
                  const isActive = status === 'listed' || status === 'available';
                  const isSnoozed = status === 'snoozed';
                  const isMaintenance = status === 'maintenance';
                  
                  let badgeVariant: "default" | "secondary" | "outline" = "default";
                  if (isActive) badgeVariant = "default";
                  else if (isSnoozed) badgeVariant = "secondary";
                  else if (isMaintenance) badgeVariant = "outline";
                  else badgeVariant = "secondary";
                  
                  return (
                    <div 
                      key={vehicle.id} 
                      className="flex items-center justify-between p-3 rounded-lg bg-muted/50 border border-border hover:bg-muted/70 transition-colors cursor-pointer"
                      onClick={() => navigate(`/vehicles/${vehicle.id}`)}
                    >
                      <div className="flex-1">
                        <p className="font-medium text-foreground">{vehicle.name}</p>
                        {vehicle.year && (
                          <p className="text-sm text-muted-foreground mt-1">{vehicle.year}</p>
                        )}
                      </div>
                      <Badge variant={badgeVariant} className="ml-2 capitalize">
                        {vehicle.status || 'Unknown'}
                      </Badge>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Index;
