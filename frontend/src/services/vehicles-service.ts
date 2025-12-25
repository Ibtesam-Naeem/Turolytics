import { apiClient } from '@/lib/api-client';

export interface Vehicle {
  id: number;
  name: string;
  year?: string;
  trim?: string;
  license_plate?: string;
  status?: string;
  status_mapped?: "active" | "maintenance" | "inactive";
  rating?: number;
  trip_count?: number;
  created_at?: string;
  updated_at?: string;
  scraped_at?: string;
  // Aggregated statistics
  total_revenue?: number;
  total_odometer?: number;
  total_trips?: number;
  avg_rating?: number;
  review_count?: number;
  utilization?: number; // Utilization percentage (0-100)
}

export interface VehiclesResponse {
  vehicles: Vehicle[];
  total: number;
  limit: number;
  offset: number;
}

export interface VehiclePerformance {
  rank: number;
  vehicle_id: number;
  vehicle_name: string;
  revenue: number;
  utilization: number;
  rating: number;
  trips: number;
}

export interface TopPerformersResponse {
  vehicles: VehiclePerformance[];
  total: number;
}

class VehiclesService {
  async getVehicles(params?: {
    vehicle_id?: number;
    license_plate?: string;
    status?: string;
    include_stats?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<VehiclesResponse> {
    const queryParams = new URLSearchParams();
    if (params?.vehicle_id !== undefined) {
      queryParams.append('vehicle_id', params.vehicle_id.toString());
    }
    if (params?.license_plate) {
      queryParams.append('license_plate', params.license_plate);
    }
    if (params?.status) {
      queryParams.append('status', params.status);
    }
    if (params?.include_stats !== undefined) {
      queryParams.append('include_stats', params.include_stats.toString());
    }
    if (params?.limit) {
      queryParams.append('limit', params.limit.toString());
    }
    if (params?.offset) {
      queryParams.append('offset', params.offset.toString());
    }

    const response = await apiClient.get<{ success: boolean; data: VehiclesResponse }>(
      `/api/turo/data/vehicles${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    );
    return response.data;
  }

  async getTopPerformers(limit: number = 5): Promise<TopPerformersResponse> {
    const response = await apiClient.get<{ success: boolean; data: TopPerformersResponse }>(
      `/api/turo/data/vehicles/top-performers?limit=${limit}`
    );
    return response.data;
  }

  async getMonthlyUtilization(year?: number): Promise<{ months: MonthlyUtilization[]; total: number }> {
    const queryParams = new URLSearchParams();
    if (year) {
      queryParams.append('year', year.toString());
    }
    const response = await apiClient.get<{ success: boolean; data: { months: MonthlyUtilization[]; total: number } }>(
      `/api/turo/data/utilization/monthly${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    );
    return response.data;
  }
}

export interface VehicleUtilization {
  vehicle: string;
  utilization: number;
  trips: number;
  daysRented: number;
  totalDays: number;
}

export interface MonthlyUtilization {
  month: string;
  utilization: number;
  vehicles: VehicleUtilization[];
}

export const vehiclesService = new VehiclesService();

