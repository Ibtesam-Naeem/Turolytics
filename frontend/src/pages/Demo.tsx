import { DollarSign, Car, Calendar as CalendarIcon, Wallet, Star, RefreshCw } from "lucide-react";
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
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Link } from "react-router-dom";
import { Info, ArrowRight, X } from "lucide-react";
import { useState, useEffect } from "react";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { DemoSidebar } from "@/components/DemoSidebar";

const Demo = () => {
  const [isBannerDismissed, setIsBannerDismissed] = useState(false);

  useEffect(() => {
    // Check if banner was previously dismissed
    const dismissed = localStorage.getItem('demo_banner_dismissed') === 'true';
    setIsBannerDismissed(dismissed);
  }, []);

  const handleDismiss = () => {
    setIsBannerDismissed(true);
    localStorage.setItem('demo_banner_dismissed', 'true');
  };

  const upcomingTrips = [
    { id: "1", vehicleName: "Mercedes C-Class", guestName: "Michael Brown", pickupLocation: "San Diego Airport (SAN)", dropoffLocation: "La Jolla, CA", earnings: 420, kmsAllowed: 350, startDate: "Tomorrow, 9:00 AM" },
    { id: "2", vehicleName: "Tesla Model Y", guestName: "Sarah Johnson", pickupLocation: "Oakland, CA", dropoffLocation: "Napa Valley, CA", earnings: 560, kmsAllowed: 450, startDate: "Nov 21, 2:00 PM" },
    { id: "3", vehicleName: "Audi A4", guestName: "David Lee", pickupLocation: "San Jose, CA", dropoffLocation: "San Francisco Airport (SFO)", earnings: 290, kmsAllowed: 200, startDate: "Nov 23, 11:00 AM" },
    { id: "4", vehicleName: "BMW 5 Series", guestName: "Alex Martinez", pickupLocation: "Los Angeles, CA", dropoffLocation: "Beverly Hills, CA", earnings: 380, kmsAllowed: 300, startDate: "Dec 1, 10:30 AM" },
    { id: "5", vehicleName: "Ford Mustang", guestName: "Jennifer Adams", pickupLocation: "San Francisco, CA", dropoffLocation: "Monterey, CA", earnings: 520, kmsAllowed: 400, startDate: "Dec 3, 1:00 PM" },
    { id: "6", vehicleName: "Range Rover Sport", guestName: "Chris Taylor", pickupLocation: "San Diego, CA", dropoffLocation: "Palm Springs, CA", earnings: 650, kmsAllowed: 350, startDate: "Dec 5, 8:00 AM" },
    { id: "7", vehicleName: "Porsche 911", guestName: "Nicole Kim", pickupLocation: "Oakland, CA", dropoffLocation: "Lake Tahoe, CA", earnings: 890, kmsAllowed: 500, startDate: "Dec 7, 6:00 AM" },
    { id: "8", vehicleName: "Volvo XC90", guestName: "Daniel Park", pickupLocation: "San Jose, CA", dropoffLocation: "Carmel, CA", earnings: 440, kmsAllowed: 280, startDate: "Dec 10, 3:00 PM" },
  ];

  const currentTrips = [
    { vehicleName: "Tesla Model 3", year: 2024, guestName: "John Smith", location: "San Francisco, CA", coordinates: "37.7749°N, 122.4194°W", fuelPercent: 85, speed: 45, status: "Moving" as const, kmsDriven: 280, kmsAllowed: 400, earnings: 245, topSpeed: 68, flags: { rapidAcceleration: 3, hardBraking: 1, engineLight: false } },
    { vehicleName: "BMW X5", year: 2023, guestName: "Emma Wilson", location: "Los Angeles, CA", coordinates: "34.0522°N, 118.2437°W", fuelPercent: 62, speed: 0, status: "Parked" as const, kmsDriven: 150, kmsAllowed: 500, earnings: 380, topSpeed: 52, flags: { rapidAcceleration: 0, hardBraking: 0, engineLight: true } },
    { vehicleName: "Audi A6", year: 2024, guestName: "Michael Chen", location: "Seattle, WA", coordinates: "47.6062°N, 122.3321°W", fuelPercent: 78, speed: 55, status: "Moving" as const, kmsDriven: 320, kmsAllowed: 600, earnings: 495, topSpeed: 72, flags: { rapidAcceleration: 2, hardBraking: 0, engineLight: false } },
    { vehicleName: "Mercedes E-Class", year: 2023, guestName: "Sarah Mitchell", location: "Portland, OR", coordinates: "45.5152°N, 122.6784°W", fuelPercent: 45, speed: 0, status: "Parked" as const, kmsDriven: 420, kmsAllowed: 450, earnings: 585, topSpeed: 65, flags: { rapidAcceleration: 1, hardBraking: 2, engineLight: false } },
    { vehicleName: "Toyota Camry", year: 2024, guestName: "James Rodriguez", location: "Phoenix, AZ", coordinates: "33.4484°N, 112.0740°W", fuelPercent: 92, speed: 38, status: "Moving" as const, kmsDriven: 95, kmsAllowed: 350, earnings: 175, topSpeed: 55, flags: { rapidAcceleration: 0, hardBraking: 0, engineLight: false } },
    { vehicleName: "Honda Accord", year: 2023, guestName: "Lisa Wang", location: "Denver, CO", coordinates: "39.7392°N, 104.9903°W", fuelPercent: 68, speed: 48, status: "Moving" as const, kmsDriven: 225, kmsAllowed: 500, earnings: 340, topSpeed: 61, flags: { rapidAcceleration: 4, hardBraking: 3, engineLight: false } },
    { vehicleName: "Lexus RX350", year: 2024, guestName: "Robert Thompson", location: "Austin, TX", coordinates: "30.2672°N, 97.7431°W", fuelPercent: 31, speed: 0, status: "Parked" as const, kmsDriven: 380, kmsAllowed: 400, earnings: 520, topSpeed: 58, flags: { rapidAcceleration: 0, hardBraking: 1, engineLight: true } },
    { vehicleName: "Porsche Cayenne", year: 2024, guestName: "Amanda Foster", location: "Miami, FL", coordinates: "25.7617°N, 80.1918°W", fuelPercent: 88, speed: 62, status: "Moving" as const, kmsDriven: 145, kmsAllowed: 550, earnings: 680, topSpeed: 75, flags: { rapidAcceleration: 5, hardBraking: 2, engineLight: false } },
  ];

  return (
    <SidebarProvider>
      <div className="flex min-h-screen w-full">
        <DemoSidebar />
        <div className="flex-1 flex flex-col">
          {/* Demo Banner or Indicator */}
          {!isBannerDismissed ? (
            <div className="sticky top-0 z-50 border-b border-border bg-background/95 backdrop-blur-sm">
              <Alert className="border-primary/50 bg-primary/5 rounded-none m-0">
                <Info className="h-4 w-4 text-primary" />
                <AlertDescription className="flex items-center justify-between w-full">
                  <span className="text-sm">
                    <strong>Demo Mode:</strong> You're viewing sample data.{" "}
                    <Link to="/auth?mode=signup" className="underline hover:no-underline font-medium">
                      Sign up for free
                    </Link>{" "}
                    to access your real fleet data.
                  </span>
                  <div className="flex items-center gap-2">
                    <Link to="/auth?mode=signup">
                      <Button size="sm" className="gap-2">
                        Get Started
                        <ArrowRight className="w-3.5 h-3.5" />
                      </Button>
                    </Link>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0"
                      onClick={handleDismiss}
                      aria-label="Dismiss banner"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                </AlertDescription>
              </Alert>
            </div>
          ) : (
            <div className="sticky top-0 z-50 border-b border-border bg-background/95 backdrop-blur-sm">
              <div className="px-4 py-2 flex items-center justify-center">
                <div className="px-3 py-1.5 flex items-center gap-2 text-xs text-foreground bg-primary/90 backdrop-blur-md border border-primary/50 rounded-full shadow-lg">
                  <div className="h-1.5 w-1.5 rounded-full bg-primary-foreground animate-pulse" />
                  <span className="text-primary-foreground">
                    <strong>Demo Mode</strong> •{" "}
                    <Link 
                      to="/auth?mode=signup" 
                      className="underline hover:no-underline font-medium"
                    >
                      Sign up free
                    </Link>
                  </span>
                </div>
              </div>
            </div>
          )}

          <header className="h-12 flex items-center border-b border-border bg-background sticky top-0 z-10">
            <SidebarTrigger className="ml-2" />
          </header>

          <main className="flex-1">
            <div className="flex">
              {/* Main Content Area */}
              <div className="flex-1 p-3 lg:p-4 xl:pr-[300px] 2xl:pr-[340px] space-y-3 overflow-auto">
                {/* Header */}
                <div className="animate-fade-in flex items-center justify-between">
                  <div>
                    <h1 className="text-xl sm:text-2xl font-bold text-foreground">
                      Turolytics
                    </h1>
                    <p className="text-xs text-muted-foreground">Your fleet at a glance</p>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-2"
                    disabled
                  >
                    <RefreshCw className="h-4 w-4" />
                    Refresh
                  </Button>
                </div>

                {/* KPI Cards */}
                <div className="grid gap-2 grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
                  <KPICard title="Total Revenue" value="$24,580" trend="+12.5% from last month" trendPositive={true} icon={DollarSign} />
                  <KPICard title="Active Vehicles" value="8" trend="2 currently on trips" trendPositive={true} icon={Car} />
                  <KPICard title="Upcoming Trips" value="12" trend="+3 this week" trendPositive={true} icon={CalendarIcon} />
                  <KPICard title="Bank Balance" value="$42,150" trend="+8.2% this month" trendPositive={true} icon={Wallet} />
                  <KPICard title="Average Rating" value="4.8" trend="127 total reviews" trendPositive={true} icon={Star} />
                </div>

                {/* Live Operations Strip */}
                <LiveOperationsStrip />
                
                {/* Upcoming Trips */}
                <UpcomingTripsCard trips={upcomingTrips} />

                {/* Current Trips Section */}
                <div className="rounded-lg border bg-card shadow-sm p-3 lg:p-4">
                  <h2 className="mb-3 text-base font-bold text-foreground flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-success animate-pulse" />
                    Current Trips
                  </h2>
                  <ScrollArea className="h-[320px]">
                    <div className="grid gap-2 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 pr-4">
                      {currentTrips.map((trip, index) => (
                        <TripCard key={index} {...trip} />
                      ))}
                    </div>
                  </ScrollArea>
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
            </div>
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
};

export default Demo;










