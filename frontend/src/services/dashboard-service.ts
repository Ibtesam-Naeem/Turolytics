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
      // Active vehicles: "Listed" (scraped from Turo) or "Available" (legacy/seed data)
      const activeVehicles = vehicles.filter(v => {
        const status = (v.status || '').trim().toLowerCase();
        return status === 'listed' || status === 'available';
      }).length;
      
      const snoozedVehicles = vehicles.filter(v => {
        const status = (v.status || '').trim().toLowerCase();
        return status === 'snoozed';
      }).length;
      
      const maintenanceVehicles = vehicles.filter(v => {
        const status = (v.status || '').trim().toLowerCase();
        return status === 'maintenance';
      }).length;
      
      // Inactive vehicles: empty status, "Unlisted", or any other status that's not active/snoozed/maintenance
      const inactiveVehicles = vehicles.filter(v => {
        const status = (v.status || '').trim().toLowerCase();
        return !status || 
          status === 'unlisted' ||
          (
            status !== 'listed' && 
            status !== 'available' &&
            status !== 'snoozed' && 
            status !== 'maintenance'
          );
      }).length;
      
      console.log('Dashboard: Vehicle status counts:', {
        total: vehicles.length,
        active: activeVehicles,
        snoozed: snoozedVehicles,
        maintenance: maintenanceVehicles,
        inactive: inactiveVehicles,
        statuses: vehicles.map(v => v.status)
      });

      // Calculate total revenue from earnings breakdown
      // Total revenue = Trip earnings + Incentives ONLY
      let totalRevenue = 0;
      try {
        const earningsResponse = await this.getEarnings();
        const breakdown = earningsResponse.breakdown || [];
        
        console.log('Dashboard: Earnings breakdown items:', breakdown.map(item => ({
          type: item.type,
          amount_numeric: item.amount_numeric,
          amount: item.amount
        })));
        
        // Only include Trip earnings and Incentives
        const includedTypes = ['Trip earnings', 'Incentives'];
        
        if (breakdown.length > 0) {
          totalRevenue = breakdown.reduce((sum, item) => {
            const itemType = item.type || '';
            const itemTypeLower = itemType.toLowerCase();
            
            // Only include Trip earnings and Incentives (case-insensitive)
            const isIncluded = includedTypes.some(included => included.toLowerCase() === itemTypeLower);
            if (!isIncluded) {
              return sum;
            }
            
            // Get the numeric value
            let amount = 0;
            if (item.amount_numeric !== undefined && item.amount_numeric !== null) {
              amount = item.amount_numeric;
            } else if (item.amount) {
              const parsed = parseFloat(item.amount.replace(/[^0-9.-]+/g, ''));
              amount = isNaN(parsed) ? 0 : parsed;
            }
            
            console.log(`Dashboard: Adding ${itemType}: ${amount}`);
            return sum + amount;
          }, 0);
          console.log('Dashboard: Total revenue calculated (Trip earnings + Incentives):', totalRevenue);
        }
        
        // If earnings breakdown didn't yield revenue, fall back to vehicle revenue
        if (totalRevenue === 0) {
          totalRevenue = vehicles.reduce((sum, v) => {
            const revenue = v.total_revenue || 0;
            return sum + (typeof revenue === 'number' ? revenue : 0);
          }, 0);
          console.log('Dashboard: Fallback - Total revenue calculated from vehicles:', totalRevenue);
        }
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
