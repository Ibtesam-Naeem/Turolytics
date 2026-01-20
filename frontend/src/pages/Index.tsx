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
import { useAuth } from "@/contexts/AuthContext";
import { mockStats, mockUpcomingTrips, mockCurrentTrips } from "@/data/mockData";

const Index = () => {
  const navigate = useNavigate();
  const { isDemo } = useAuth();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [turoConnected, setTuroConnected] = useState<boolean | null>(true);
  const [stats, setStats] = useState({
    totalRevenue: 0,
    activeVehicles: 0,
    snoozedVehicles: 0,
    maintenanceVehicles: 0,
    inactiveVehicles: 0,
    upcomingTrips: 0,
    currentTrips: 0,
    averageRating: 0,
    totalReviews: 0,
    bankBalance: 0,
  });

  const loadDashboardStats = async () => {
    // Demo mode - always use mock data
    setStats(mockStats);
    setIsLoading(false);
  };

  useEffect(() => {
    loadDashboardStats();
  }, [isDemo]);

  const handleRefresh = async () => {
    // Demo mode - just refresh mock data
    setIsRefreshing(true);
    await Promise.all([
      loadDashboardStats(),
      loadUpcomingTrips(),
      loadCurrentTrips(),
    ]);
    toast({
      title: "Data refreshed",
      description: "Dashboard has been updated with latest data",
    });
    setIsRefreshing(false);
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

  const loadUpcomingTrips = async () => {
    // Demo mode - always use mock data
    setUpcomingTrips(mockUpcomingTrips);
    setUpcomingTripsLoading(false);
  };

  const loadCurrentTrips = async () => {
    // Demo mode - always use mock data
    const mappedTrips = mockCurrentTrips.map(trip => ({
      vehicleName: trip.vehicleName,
      year: trip.year,
      guestName: trip.guestName,
      location: trip.location,
      coordinates: trip.coordinates,
      fuelPercent: trip.fuelPercent,
      speed: trip.speed,
      status: trip.status as "Active" | "Parked" | "Moving" | "Alert",
      kmsDriven: trip.kmsDriven,
      kmsAllowed: trip.kmsAllowed,
      earnings: trip.earnings,
      topSpeed: trip.topSpeed,
      flags: trip.flags,
    }));
    setCurrentTrips(mappedTrips);
    setCurrentTripsLoading(false);
  };

  useEffect(() => {
    loadUpcomingTrips();
    loadCurrentTrips();
  }, []);

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
            <div>
              <KPICard 
                title="Active Vehicles" 
                value={isLoading ? "..." : stats.activeVehicles.toString()} 
                trend={isLoading ? "" : (() => {
                  const parts = [];
                  if (stats.currentTrips > 0) parts.push(`${stats.currentTrips} on trips`);
                  if (stats.snoozedVehicles > 0) parts.push(`${stats.snoozedVehicles} snoozed`);
                  if (stats.maintenanceVehicles > 0) parts.push(`${stats.maintenanceVehicles} in maintenance`);
                  return parts.length > 0 ? parts.join(', ') : "All vehicles active";
                })()} 
                trendPositive={stats.snoozedVehicles === 0 && stats.maintenanceVehicles === 0} 
                icon={Car} 
              />
            </div>
            <KPICard 
              title="Upcoming Trips" 
              value={isLoading ? "..." : stats.upcomingTrips.toString()} 
              trend={isLoading ? "" : `${stats.currentTrips} currently active`} 
              trendPositive={true} 
              icon={CalendarIcon} 
            />
            <KPICard 
              title="Bank Balance" 
              value={isLoading ? "..." : formatCurrency(stats.bankBalance)} 
              trend={isLoading ? "" : "Available cash"} 
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
              <div className="flex items-center justify-center h-[380px]">
                <p className="text-muted-foreground">Loading current trips...</p>
              </div>
            ) : currentTrips.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-[380px] text-center">
                <Route className="h-12 w-12 text-muted-foreground mb-4 opacity-50" />
                <p className="text-lg font-semibold text-foreground mb-2">No current trips</p>
                <p className="text-sm text-muted-foreground">You don't have any active trips at the moment.</p>
              </div>
            ) : (
              <ScrollArea className="h-[380px]">
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
            <RevenueChart turoConnected={turoConnected} />
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

    </div>
  );
};

export default Index;
