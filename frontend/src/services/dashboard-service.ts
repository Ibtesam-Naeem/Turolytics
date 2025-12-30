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

      // Calculate total revenue from earnings breakdown (Total earnings)
      let totalRevenue = 0;
      try {
        const earningsResponse = await this.getEarnings();
        const totalEarnings = earningsResponse.breakdown.find(
          item => item.type === 'Total earnings'
        );
        if (totalEarnings && totalEarnings.amount_numeric !== undefined) {
          totalRevenue = totalEarnings.amount_numeric;
        } else if (totalEarnings && totalEarnings.amount) {
          // Fallback: parse the amount string if amount_numeric is not available
          const parsed = parseFloat(totalEarnings.amount.replace(/[^0-9.-]+/g, ''));
          if (!isNaN(parsed)) {
            totalRevenue = parsed;
          }
        }
        console.log('Dashboard: Total revenue from earnings breakdown:', totalRevenue);
      } catch (error) {
        console.error('Error fetching earnings breakdown:', error);
        // Fallback to vehicle revenue calculation if earnings endpoint fails
        totalRevenue = vehicles.reduce((sum, v) => {
          const revenue = v.total_revenue || 0;
          return sum + (typeof revenue === 'number' ? revenue : 0);
        }, 0);
        console.log('Dashboard: Fallback - Total revenue calculated from vehicles:', totalRevenue);
      }

      console.log('Dashboard: Total revenue calculated:', totalRevenue);

      // Calculate average rating and total reviews
      const vehiclesWithRatings = vehicles.filter(v => {
        const rating = v.avg_rating;
        return rating !== null && rating !== undefined && rating !== 0;
      });
      
      // Fetch total reviews directly from reviews endpoint for accurate count
      let totalReviews = 0;
      try {
        const reviewsResponse = await apiClient.get<{
          success: boolean;
          data: {
            reviews: Array<any>;
            total: number;
          };
        }>('/api/turo/data/reviews?limit=1');
        
        totalReviews = reviewsResponse.data?.total || 0;
        console.log('Dashboard: Total reviews from reviews endpoint:', totalReviews);
      } catch (error) {
        console.error('Error fetching total reviews:', error);
        // Fallback to summing vehicle review counts
        totalReviews = vehicles.reduce((sum, v) => {
          const count = v.review_count || 0;
          return sum + (typeof count === 'number' ? count : 0);
        }, 0);
        console.log('Dashboard: Fallback - Total reviews calculated from vehicles:', totalReviews);
      }
      
      const averageRating = vehiclesWithRatings.length > 0
        ? vehiclesWithRatings.reduce((sum, v) => {
            const rating = v.avg_rating || 0;
            return sum + (typeof rating === 'number' ? rating : 0);
          }, 0) / vehiclesWithRatings.length
        : 0;

      console.log('Dashboard: Average rating calculated:', averageRating, 'from', vehiclesWithRatings.length, 'vehicles');
      console.log('Dashboard: Total reviews:', totalReviews);

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
        averageRating: Math.round(averageRating * 10) / 10, // Round to 1 decimal
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
