import { useAuth } from "@/contexts/AuthContext";
import {
  demoKPIs,
  demoUpcomingTrips,
  demoCurrentTrips,
  demoLiveOperations,
  demoRevenueData,
  demoUtilizationData,
  demoFleetHealth,
  demoUpcomingMaintenance,
  demoActivityFeed,
  demoPerformanceLeaderboard,
  demoCalendarEvents,
} from "@/data/demoData";

// Hook to get dashboard data - returns demo data or real data based on auth state
export const useDashboardData = () => {
  const { isDemo, isAuthenticated } = useAuth();

  // If in demo mode, return demo data
  // If authenticated, fetch from your backend
  const useRealData = isAuthenticated && !isDemo;

  if (useRealData) {
    // TODO: Replace with your backend API calls
    // Example:
    // const { data: kpis } = useQuery(['kpis'], fetchKPIs);
    // const { data: trips } = useQuery(['trips'], fetchTrips);
    // return { kpis, trips, ... };

    // For now, return demo data as placeholder
    // Remove this and implement real data fetching
    console.log("Authenticated mode - implement real data fetching");
  }

  return {
    kpis: demoKPIs,
    upcomingTrips: demoUpcomingTrips,
    currentTrips: demoCurrentTrips,
    liveOperations: demoLiveOperations,
    revenueData: demoRevenueData,
    utilizationData: demoUtilizationData,
    fleetHealth: demoFleetHealth,
    upcomingMaintenance: demoUpcomingMaintenance,
    activityFeed: demoActivityFeed,
    performanceLeaderboard: demoPerformanceLeaderboard,
    calendarEvents: demoCalendarEvents,
    isLoading: false,
    isDemo: isDemo || !isAuthenticated,
  };
};
