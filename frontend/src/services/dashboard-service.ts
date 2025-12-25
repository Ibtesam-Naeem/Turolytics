import { apiClient } from '@/lib/api-client';

export interface DashboardStats {
  totalRevenue: number;
  activeVehicles: number;
  snoozedVehicles: number;
  maintenanceVehicles: number;
  inactiveVehicles: number;
  upcomingTrips: number;
  averageRating: number;
  totalReviews: number;
}

export interface MonthlyRevenue {
  month: string;
  revenue: number;
}

class DashboardService {
  async getDashboardStats(): Promise<DashboardStats> {
    // Initialize default stats
    const defaultStats: DashboardStats = {
      totalRevenue: 0,
      activeVehicles: 0,
      snoozedVehicles: 0,
      maintenanceVehicles: 0,
      inactiveVehicles: 0,
      upcomingTrips: 0,
      averageRating: 0,
      totalReviews: 0,
    };

    try {
      // Fetch vehicles to get counts by status
      let vehicles: Array<{
        status?: string;
        total_revenue?: number;
        avg_rating?: number;
        review_count?: number;
      }> = [];

      try {
        const vehiclesResponse = await apiClient.get<{
          success: boolean;
          data: {
            vehicles: Array<{
              status?: string;
              total_revenue?: number;
              avg_rating?: number;
              review_count?: number;
            }>;
            total: number;
          };
        }>('/api/turo/data/vehicles?include_stats=true&limit=1000');

        vehicles = vehiclesResponse.data?.vehicles || [];
        console.log('Dashboard: Fetched vehicles:', vehicles.length);
      } catch (error) {
        console.error('Error fetching vehicles:', error);
      }
      
      // Count vehicles by status (case-insensitive matching)
      const activeVehicles = vehicles.filter(v => {
        const status = (v.status || '').trim();
        return status === 'Listed' || status.toLowerCase() === 'listed';
      }).length;
      
      const snoozedVehicles = vehicles.filter(v => {
        const status = (v.status || '').trim();
        return status === 'Snoozed' || status.toLowerCase() === 'snoozed';
      }).length;
      
      const maintenanceVehicles = vehicles.filter(v => {
        const status = (v.status || '').trim();
        return status === 'Maintenance' || status.toLowerCase() === 'maintenance';
      }).length;
      
      const inactiveVehicles = vehicles.filter(v => {
        const status = (v.status || '').trim();
        return !status || (
          status !== 'Listed' && 
          status !== 'Snoozed' && 
          status !== 'Maintenance' &&
          status.toLowerCase() !== 'listed' &&
          status.toLowerCase() !== 'snoozed' &&
          status.toLowerCase() !== 'maintenance'
        );
      }).length;

      // FIX 1: Get total revenue from earnings breakdown (authoritative source)
      // This uses the earnings_breakdown table which has the correct total
      let totalRevenue = 0;
      try {
        const earningsResponse = await apiClient.get<{
          success: boolean;
          data: {
            breakdown: Array<{ type?: string; amount_numeric?: number }>;
            vehicle_earnings: Array<any>;
          };
        }>('/api/turo/data/earnings');
        
        const breakdown = earningsResponse.data?.breakdown || [];
        // Find "Trip earnings" in the breakdown
        const tripEarnings = breakdown.find(item => 
          item.type && item.type.toLowerCase().includes('trip earnings')
        );
        
        if (tripEarnings && tripEarnings.amount_numeric != null) {
          totalRevenue = tripEarnings.amount_numeric;
          console.log('Dashboard: Total revenue from earnings breakdown:', totalRevenue);
        } else {
          // Fallback: try to sum all earnings types
          totalRevenue = breakdown.reduce((sum, item) => {
            const amount = item.amount_numeric || 0;
            return sum + (typeof amount === 'number' ? amount : 0);
          }, 0);
          console.log('Dashboard: Total revenue (sum of all earnings types):', totalRevenue);
        }
      } catch (error) {
        console.error('Error fetching earnings breakdown:', error);
        // Fallback: calculate from completed trips
        try {
          const tripsResponse = await apiClient.get<{
            success: boolean;
            data: {
              trips: Array<{ total_earnings?: number; status?: string }>;
              total: number;
            };
          }>('/api/turo/data/trips?status=COMPLETED&limit=1000');
          
          const completedTrips = tripsResponse.data?.trips || [];
          totalRevenue = completedTrips.reduce((sum, trip) => {
            const earnings = trip.total_earnings || 0;
            return sum + (typeof earnings === 'number' ? earnings : 0);
          }, 0);
          console.log('Dashboard: Total revenue (fallback from trips):', totalRevenue);
        } catch (tripsError) {
          console.error('Error fetching trips for revenue:', tripsError);
          // Final fallback: vehicle-level calculation
          totalRevenue = vehicles.reduce((sum, v) => {
            const revenue = v.total_revenue || 0;
            return sum + (typeof revenue === 'number' ? revenue : 0);
          }, 0);
          console.log('Dashboard: Total revenue (final fallback from vehicles):', totalRevenue);
        }
      }

      // FIX 2: Calculate average rating and total reviews from ALL reviews directly
      // This ensures we get the correct overall average and total count
      let averageRating = 0;
      let totalReviews = 0;
      try {
        const reviewsResponse = await apiClient.get<{
          success: boolean;
          data: {
            reviews: Array<{ rating?: number }>;
            total: number;
          };
        }>('/api/turo/data/reviews?limit=1000');
        
        const allReviews = reviewsResponse.data?.reviews || [];
        totalReviews = allReviews.length;
        
        const reviewsWithRatings = allReviews.filter(r => r.rating != null && r.rating > 0);
        if (reviewsWithRatings.length > 0) {
          const sumRatings = reviewsWithRatings.reduce((sum, r) => sum + (r.rating || 0), 0);
          averageRating = sumRatings / reviewsWithRatings.length;
        }
        
        console.log('Dashboard: Average rating from reviews:', averageRating, 'from', totalReviews, 'total reviews');
      } catch (error) {
        console.error('Error fetching reviews:', error);
        // Fallback to vehicle-level calculation (old logic)
        const vehiclesWithRatings = vehicles.filter(v => {
          const rating = v.avg_rating;
          return rating !== null && rating !== undefined && rating !== 0;
        });
        
        totalReviews = vehicles.reduce((sum, v) => {
          const count = v.review_count || 0;
          return sum + (typeof count === 'number' ? count : 0);
        }, 0);
        
        averageRating = vehiclesWithRatings.length > 0
          ? vehiclesWithRatings.reduce((sum, v) => {
              const rating = v.avg_rating || 0;
              return sum + (typeof rating === 'number' ? rating : 0);
            }, 0) / vehiclesWithRatings.length
          : 0;
        console.log('Dashboard: Average rating (fallback from vehicles):', averageRating, 'from', totalReviews, 'reviews');
      }

      // Fetch upcoming trips (max limit is 100)
      let upcomingTrips = 0;
      try {
        const upcomingTripsResponse = await apiClient.get<{
          success: boolean;
          data: {
            trips: Array<any>;
            total: number;
          };
        }>('/api/turo/data/trips/upcoming?limit=100');

        upcomingTrips = upcomingTripsResponse.data?.total || 0;
        console.log('Dashboard: Upcoming trips:', upcomingTrips);
      } catch (error) {
        console.error('Error fetching upcoming trips:', error);
      }

      const stats: DashboardStats = {
        totalRevenue: Math.round(totalRevenue),
        activeVehicles,
        snoozedVehicles,
        maintenanceVehicles,
        inactiveVehicles,
        upcomingTrips,
        averageRating: Math.round(averageRating * 100) / 100, // Round to 2 decimals
        totalReviews,
      };

      console.log('Dashboard: Final stats:', stats);

      return stats;
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
      // Log more details about the error
      if (error instanceof Error) {
        console.error('Error message:', error.message);
        console.error('Error stack:', error.stack);
      }
      // Return default stats on error
      return defaultStats;
    }
  }

  async getMonthlyRevenue(year?: number): Promise<{ months: MonthlyRevenue[]; total: number }> {
    const queryParams = new URLSearchParams();
    if (year) {
      queryParams.append('year', year.toString());
    }
    const response = await apiClient.get<{ success: boolean; data: { months: MonthlyRevenue[]; total: number } }>(
      `/api/turo/data/revenue/monthly${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    );
    return response.data;
  }

  async getEarnings(year?: number): Promise<{ breakdown: Array<{ type: string; amount: string; amount_numeric?: number }>; vehicle_earnings: Array<any> }> {
    const queryParams = new URLSearchParams();
    if (year) {
      queryParams.append('year', year.toString());
    }
    const response = await apiClient.get<{ success: boolean; data: { breakdown: Array<{ type: string; amount: string; amount_numeric?: number }>; vehicle_earnings: Array<any> } }>(
      `/api/turo/data/earnings${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    );
    return response.data;
  }
}

export const dashboardService = new DashboardService();
