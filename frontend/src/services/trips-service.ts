// Stub service for demo mode
export interface UpcomingTrip {
  id: string;
  vehicle_name: string;
  guest_name: string;
  pickup_location: string;
  dropoff_location: string;
  earnings: number;
  kms_allowed: number;
  start_date: string;
}

export interface CurrentTrip {
  vehicle_id?: number;
  vehicle_name: string;
  vehicle_year?: number;
  guest_name: string;
  location: string;
  coordinates?: string;
  fuel_percent?: number;
  speed?: number;
  status?: string;
  kms_driven?: number;
  kms_allowed?: number;
  earnings?: number;
  top_speed?: number;
  start_date?: string;
  start_time?: string;
  end_date?: string;
  end_time?: string;
}

export interface TripToday {
  id: string;
  vehicle_name: string;
  guest_name: string;
  location: string;
  status?: string;
}

export interface NewBookingToday {
  id: string;
  guest_name: string;
  vehicle_name: string;
  dates: string;
  amount: string;
}

export interface CheckoutToday {
  id: string;
  vehicle_name: string;
  guest_name: string;
  location: string;
  time: string;
}

export interface Trip {
  id: string;
  trip_id: string;
  vehicle_id?: number;
  customer_name?: string;
  start_date?: string;
  end_date?: string;
  address?: string;
  status?: string;
  kilometers_driven?: number;
  kilometers_included?: number;
  total_earnings?: number;
  trip_url?: string;
  coordinates?: number[][]; // Array of [lat, lng] coordinate pairs for route visualization
}

export interface TripsResponse {
  trips: Trip[];
  total: number;
}

class TripsService {
  async getUpcomingTrips(limit: number = 50): Promise<{ trips: UpcomingTrip[] }> {
    return { trips: [] };
  }

  async getCurrentTrips(limit: number = 50): Promise<{ trips: CurrentTrip[] }> {
    return { trips: [] };
  }

  async getTripsToday(): Promise<{ trips: TripToday[] }> {
    // Mock trips happening today (some current trips + some starting today)
    return {
      trips: [
        { id: "today1", vehicle_name: "Tesla Model 3", guest_name: "John Smith", location: "San Francisco, CA", status: "In Progress" },
        { id: "today2", vehicle_name: "BMW X5", guest_name: "Emma Wilson", location: "Los Angeles, CA", status: "In Progress" },
        { id: "today3", vehicle_name: "Mercedes-Benz GLE", guest_name: "Alexander Rivera", location: "Monterey, CA", status: "In Progress" },
        { id: "today4", vehicle_name: "Mercedes C-Class", guest_name: "Michael Brown", location: "San Diego Airport", status: "Starting Today" },
      ]
    };
  }

  async getNewBookingsToday(): Promise<{ bookings: NewBookingToday[] }> {
    // Mock new bookings received today
    return {
      bookings: [
        { id: "booking1", guest_name: "Sarah Martinez", vehicle_name: "Tesla Model Y", dates: "Dec 5-8", amount: "$560" },
        { id: "booking2", guest_name: "David Chen", vehicle_name: "Audi A4", dates: "Dec 6-9", amount: "$290" },
      ]
    };
  }

  async getCheckoutsToday(): Promise<{ checkouts: CheckoutToday[] }> {
    // Mock checkouts happening today
    return {
      checkouts: [
        { id: "checkout1", vehicle_name: "Honda Accord", guest_name: "Kevin Zhang", location: "Portland, OR", time: "2:30 PM" },
        { id: "checkout2", vehicle_name: "Subaru Outback", guest_name: "Ryan O'Connor", location: "Jackson Hole, WY", time: "5:45 PM" },
      ]
    };
  }

  async getTrips(params?: { status?: string; limit?: number; offset?: number }): Promise<TripsResponse> {
    // Demo mode - return mock trip history
    // Import mock data dynamically to avoid circular dependencies
    const { mockTripHistory } = await import("@/data/mockData");
    const trips = mockTripHistory || [];
    
    // Apply filters
    let filteredTrips = trips;
    if (params?.status) {
      filteredTrips = trips.filter(t => t.status?.toUpperCase() === params.status?.toUpperCase());
    }
    
    // Apply pagination
    const limit = params?.limit || 50;
    const offset = params?.offset || 0;
    const paginatedTrips = filteredTrips.slice(offset, offset + limit);
    
    return {
      trips: paginatedTrips,
      total: filteredTrips.length,
    };
  }
}

export const tripsService = new TripsService();
