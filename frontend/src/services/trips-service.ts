import { apiClient } from '@/lib/api-client';

export interface Trip {
  id: number;
  trip_id: string;
  trip_url?: string;
  vehicle_id?: number;
  customer_name?: string;
  status: string;
  trip_type?: string;
  cancellation_info?: string;
  cancelled_by?: string;
  cancelled_date?: string;
  start_date?: string;
  start_time?: string;
  end_date?: string;
  end_time?: string;
  location_type?: string;
  address?: string;
  kilometers_driven?: number;
  kilometers_included?: number;
  overage_rate?: number;
  total_earnings?: number;
  protection_plan?: string;
  deductible?: string;
  created_at?: string;
  updated_at?: string;
  scraped_at?: string;
}

export interface TripsResponse {
  trips: Trip[];
  total: number;
  limit: number;
  offset: number;
}

export interface TripToday {
  id: number;
  trip_id: string;
  vehicle_name: string;
  guest_name: string;
  location: string;
  status: string;
  start_date?: string;
  start_time?: string;
}

export interface NewBookingToday {
  id: number;
  trip_id: string;
  guest_name: string;
  vehicle_name: string;
  dates: string;
  amount: string;
  created_at?: string;
}

export interface CheckoutToday {
  id: number;
  trip_id: string;
  vehicle_name: string;
  guest_name: string;
  time: string;
  location: string;
  end_date?: string;
  end_time?: string;
}

export interface UpcomingTrip {
  id: number;
  trip_id: string;
  vehicle_name: string;
  guest_name: string;
  pickup_location: string;
  dropoff_location: string;
  earnings: number;
  kms_allowed: number;
  start_date: string;
  start_date_raw?: string;
  start_time?: string;
  end_date?: string;
  end_time?: string;
  status?: string;
}

export interface CurrentTrip {
  id: number;
  trip_id: string;
  vehicle_name: string;
  vehicle_year: number;
  guest_name: string;
  location: string;
  coordinates: string;
  fuel_percent: number | null;
  speed: number;
  status: string;
  kms_driven: number;
  kms_allowed: number;
  earnings: number;
  top_speed: number;
  start_date?: string;
  start_time?: string;
  end_date?: string;
  end_time?: string;
}

class TripsService {
  async getTrips(params?: {
    trip_id?: string;
    status?: string;
    trip_type?: string;
    vehicle_id?: number;
    start_date?: string;
    end_date?: string;
    limit?: number;
    offset?: number;
  }): Promise<TripsResponse> {
    const queryParams = new URLSearchParams();
    if (params?.trip_id) {
      queryParams.append('trip_id', params.trip_id);
    }
    if (params?.status) {
      queryParams.append('status', params.status);
    }
    if (params?.trip_type) {
      queryParams.append('trip_type', params.trip_type);
    }
    if (params?.vehicle_id !== undefined) {
      queryParams.append('vehicle_id', params.vehicle_id.toString());
    }
    if (params?.start_date) {
      queryParams.append('start_date', params.start_date);
    }
    if (params?.end_date) {
      queryParams.append('end_date', params.end_date);
    }
    if (params?.limit) {
      queryParams.append('limit', params.limit.toString());
    }
    if (params?.offset) {
      queryParams.append('offset', params.offset.toString());
    }

    const response = await apiClient.get<{ success: boolean; data: TripsResponse }>(
      `/api/turo/data/trips${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    );
    // API returns { success: true, data: { trips: [], total: 0, limit: 50, offset: 0 } }
    if (!response.data) {
      throw new Error("Invalid API response structure");
    }
    return response.data;
  }

  async getTripsToday(): Promise<{ trips: TripToday[]; total: number }> {
    const response = await apiClient.get<{ success: boolean; data: { trips: TripToday[]; total: number } }>(
      '/api/turo/data/trips/today'
    );
    return response.data;
  }

  async getNewBookingsToday(): Promise<{ bookings: NewBookingToday[]; total: number }> {
    const response = await apiClient.get<{ success: boolean; data: { bookings: NewBookingToday[]; total: number } }>(
      '/api/turo/data/trips/new-bookings-today'
    );
    return response.data;
  }

  async getCheckoutsToday(): Promise<{ checkouts: CheckoutToday[]; total: number }> {
    const response = await apiClient.get<{ success: boolean; data: { checkouts: CheckoutToday[]; total: number } }>(
      '/api/turo/data/trips/checkouts-today'
    );
    return response.data;
  }

  async getUpcomingTrips(limit?: number): Promise<{ trips: UpcomingTrip[]; total: number }> {
    const queryParams = new URLSearchParams();
    if (limit) {
      queryParams.append('limit', limit.toString());
    }
    const response = await apiClient.get<{ success: boolean; data: { trips: UpcomingTrip[]; total: number } }>(
      `/api/turo/data/trips/upcoming${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    );
    return response.data;
  }

  async getCurrentTrips(limit?: number): Promise<{ trips: CurrentTrip[]; total: number }> {
    const queryParams = new URLSearchParams();
    if (limit) {
      queryParams.append('limit', limit.toString());
    }
    const response = await apiClient.get<{ success: boolean; data: { trips: CurrentTrip[]; total: number } }>(
      `/api/turo/data/trips/current${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    );
    return response.data;
  }
}

export const tripsService = new TripsService();

