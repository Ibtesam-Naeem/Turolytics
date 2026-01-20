// Stub service for demo mode
import { mockTopPerformers, mockVehicles } from "@/data/mockData";

export interface Vehicle {
  id: number;
  name?: string;
  year?: number;
  status?: string;
  status_mapped?: string;
  license_plate?: string;
  total_revenue?: number;
  utilization?: number;
  total_trips?: number;
  trip_count?: number;
  avg_rating?: number;
  rating?: number;
  total_odometer?: number;
  listed_on_turo_date?: string;
  removed_from_turo_date?: string;
  utilization_goal?: number;
  fuel_level?: number;
}

export interface VehiclePerformance {
  rank: number;
  vehicle_name: string;
  trips: number;
  revenue: number;
  utilization: number;
  rating: number;
}

export interface VehiclesResponse {
  vehicles: Vehicle[];
  total: number;
}

export interface TopPerformersResponse {
  vehicles: VehiclePerformance[];
}

export interface MonthlyUtilization {
  month: string;
  utilization: number;
  vehicles: Array<{
    vehicle: string;
    utilization: number;
    trips: number;
    daysRented: number;
    totalDays: number;
  }>;
}

class VehiclesService {
  async getVehicles(params?: any): Promise<VehiclesResponse> {
    // Demo mode - return mock vehicles
    return { vehicles: mockVehicles, total: mockVehicles.length };
  }

  async updateVehicle(vehicleId: number, data: Partial<Vehicle>): Promise<Vehicle> {
    // Demo mode - update the vehicle in the mock array
    const vehicleIndex = mockVehicles.findIndex(v => v.id === vehicleId);
    if (vehicleIndex === -1) {
      throw new Error("Vehicle not found");
    }
    // Update the vehicle in place
    Object.assign(mockVehicles[vehicleIndex], data);
    return mockVehicles[vehicleIndex];
  }

  async getTopPerformers(limit: number = 5): Promise<TopPerformersResponse> {
    // Demo mode - return mock top performers
    return {
      vehicles: mockTopPerformers.slice(0, limit),
    };
  }

  async getMonthlyUtilization(year: number): Promise<{ months: MonthlyUtilization[] }> {
    // Mock monthly utilization data for 2025 and 2026
    // Utilization should correlate with revenue (higher utilization = higher revenue)
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const vehicleNames = ["Porsche 911", "Range Rover Sport", "Land Rover Defender", "BMW X5", "Mercedes-Benz GLE", "Tesla Model 3", "Audi Q7", "Porsche Cayenne"];
    
    const clampUtilization = (value: number) => Math.max(0, Math.min(100, Math.round(value * 10) / 10));
    const getDaysInMonth = (monthIndex: number) => {
      // Approximate days per month (accounting for Feb)
      const days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
      return days[monthIndex];
    };
    
    if (year === 2025) {
      // 2025: Starting lower, growing throughout the year
      const baseUtilization = [68, 71, 74, 78, 81, 84, 87, 89, 85, 80, 76, 78];
      return {
        months: months.map((month, index) => {
          const fleetUtil = baseUtilization[index];
          const totalDays = getDaysInMonth(index);
          return {
            month,
            utilization: fleetUtil,
            vehicles: vehicleNames.slice(0, 5 + Math.floor(Math.random() * 3)).map(name => {
              const vehicleUtil = clampUtilization(fleetUtil + (Math.random() * 10 - 5)); // ±5% variation
              const daysRented = Math.round((vehicleUtil / 100) * totalDays);
              const trips = Math.round(daysRented / 3.5 + Math.random() * 2); // ~3.5 days per trip on average
              return {
                vehicle: name,
                utilization: vehicleUtil,
                trips: Math.max(1, trips),
                daysRented: daysRented,
                totalDays: totalDays,
              };
            }),
          };
        }),
      };
    } else if (year === 2026) {
      // 2026: Higher baseline, continued growth
      const baseUtilization = [82, 84, 86, 88, 90, 91, 92, 93, 90, 87, 85, 88];
      return {
        months: months.map((month, index) => {
          const fleetUtil = baseUtilization[index];
          const totalDays = getDaysInMonth(index);
          return {
            month,
            utilization: fleetUtil,
            vehicles: vehicleNames.slice(0, 6 + Math.floor(Math.random() * 2)).map(name => {
              const vehicleUtil = clampUtilization(fleetUtil + (Math.random() * 8 - 4)); // ±4% variation
              const daysRented = Math.round((vehicleUtil / 100) * totalDays);
              const trips = Math.round(daysRented / 3.5 + Math.random() * 2); // ~3.5 days per trip on average
              return {
                vehicle: name,
                utilization: vehicleUtil,
                trips: Math.max(1, trips),
                daysRented: daysRented,
                totalDays: totalDays,
              };
            }),
          };
        }),
      };
    }
    
    return { months: [] };
  }
}

export const vehiclesService = new VehiclesService();
