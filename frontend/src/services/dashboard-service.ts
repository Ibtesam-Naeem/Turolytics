// Stub service for demo mode
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

export interface EarningsBreakdown {
  type: string;
  amount: string;
  amount_numeric?: number;
  year?: number;
}

export interface MonthlyRevenue {
  month: string;
  revenue: number;
}

class DashboardService {
  async getDashboardStats(): Promise<DashboardStats> {
    // Demo mode - return mock stats
    return {
      totalRevenue: 24580,
      activeVehicles: 8,
      snoozedVehicles: 2,
      maintenanceVehicles: 1,
      inactiveVehicles: 0,
      upcomingTrips: 12,
      averageRating: 4.8,
      totalReviews: 127,
    };
  }

  async getEarnings(): Promise<{ breakdown: EarningsBreakdown[] }> {
    // Mock earnings breakdown with upcoming payments
    return {
      breakdown: [
        { type: "Upcoming Payments", amount: "$6,910", amount_numeric: 6910 },
        { type: "Current Trips", amount: "$4,815", amount_numeric: 4815 },
        { type: "Completed This Month", amount: "$12,855", amount_numeric: 12855 },
      ]
    };
  }

  async getMonthlyRevenue(year: number): Promise<{ months: MonthlyRevenue[] }> {
    // Mock monthly revenue data for 2025 and 2026
    // Revenue should correlate with utilization (higher utilization = higher revenue)
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    
    if (year === 2025) {
      // 2025: Starting lower, growing throughout the year
      const baseRevenue = [18500, 19200, 20100, 21500, 22800, 24200, 25100, 26300, 24800, 23100, 21900, 24580];
      return {
        months: months.map((month, index) => ({
          month,
          revenue: baseRevenue[index],
        })),
      };
    } else if (year === 2026) {
      // 2026: Higher baseline, continued growth
      const baseRevenue = [26800, 27500, 28900, 30200, 31800, 33100, 34500, 35200, 33800, 32500, 31200, 34200];
      return {
        months: months.map((month, index) => ({
          month,
          revenue: baseRevenue[index],
        })),
      };
    }
    
    return { months: [] };
  }
}

export const dashboardService = new DashboardService();
