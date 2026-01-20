// Stub service for demo mode
export interface BouncieIntegrationStatus {
  connected: boolean;
  message?: string;
}

export interface BouncieTripMatch {
  id: number;
  vehicle_id?: number;
  imei?: string;
  coordinates?: number[][]; // Array of [lat, lng] coordinate pairs
  match_data?: {
    all_trips?: Array<{
      coordinates?: number[][];
      gps?: {
        type: string;
        coordinates: number[][];
      };
      startTime?: string;
      endTime?: string;
      distance?: number;
    }>;
  };
  bouncie_trip_count?: number;
  aggregated_distance_km?: number;
  total_duration_hours?: number;
  coordinate_count?: number;
  bouncie_earliest_start?: string;
  bouncie_latest_end?: string;
  has_coordinates?: boolean;
  polyline?: string;
}

export interface BouncieDTCCode {
  id: number;
  imei: string;
  vehicle_name?: string;
  code: string;
  description?: string;
  is_active: boolean;
  first_seen?: string;
  last_seen?: string;
}

class BouncieService {
  async getIntegrationStatus(): Promise<BouncieIntegrationStatus> {
    return { connected: true }; // Demo: show as connected
  }

  async getVehicleMappings(limit: number, offset: number): Promise<{ mappings: any[]; total: number }> {
    return { mappings: [], total: 0 };
  }

  async syncMatches(days: number, skipExisting: boolean, forceRematch: boolean): Promise<{ matches_created?: number }> {
    return { matches_created: 0 };
  }

  async disconnect(): Promise<void> {
    // Stub
  }

  async deleteAllData(): Promise<void> {
    // Stub
  }

  async getAuthorizationUrl(isPopup: boolean): Promise<string> {
    throw new Error("Bouncie integration not available in demo mode");
  }

  async getDTCCodes(vehicleId?: number, imei?: string, activeOnly?: boolean, limit?: number, offset?: number): Promise<{ codes: BouncieDTCCode[]; total: number }> {
    // Mock DTC codes with real codes
    const mockCodes: BouncieDTCCode[] = [
      {
        id: 1,
        imei: "imei_002",
        vehicle_name: "BMW X5",
        code: "P0300",
        description: "Random/Multiple Cylinder Misfire Detected",
        is_active: true,
        first_seen: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
        last_seen: new Date().toISOString(),
      },
      {
        id: 2,
        imei: "imei_008",
        vehicle_name: "Chevrolet Tahoe",
        code: "P0420",
        description: "Catalyst System Efficiency Below Threshold",
        is_active: true,
        first_seen: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
        last_seen: new Date().toISOString(),
      },
    ];
    return { codes: mockCodes, total: mockCodes.length };
  }

  // Store trip_id -> match_id mapping for demo mode
  private tripMatchMap = new Map<string, number>();
  private matchTripMap = new Map<number, string>();

  async getTripMatches(tripId: string, includePolylines?: boolean, limit?: number, offset?: number): Promise<{ matches: BouncieTripMatch[]; total: number }> {
    // Demo mode - return a mock match for trips that have coordinates
    // Import mock trip history to check if trip has coordinates
    const { mockTripHistory } = await import("@/data/mockData");
    const trip = mockTripHistory.find(t => t.trip_id === tripId);
    
    if (trip && trip.coordinates && trip.coordinates.length > 0) {
      // Create or reuse match ID for this trip
      let matchId = this.tripMatchMap.get(tripId);
      if (!matchId) {
        matchId = Date.now(); // Use timestamp as unique ID
        this.tripMatchMap.set(tripId, matchId);
        this.matchTripMap.set(matchId, tripId);
      }
      
      return {
        matches: [{
          id: matchId,
          vehicle_id: trip.vehicle_id,
          imei: `imei_${String(trip.vehicle_id || 0).padStart(3, '0')}`,
        }],
        total: 1,
      };
    }
    
    return { matches: [], total: 0 };
  }

  async getTripMatchDetail(matchId: number, includeFullData?: boolean): Promise<BouncieTripMatch> {
    // Demo mode - return mock trip match detail with coordinates
    // Find the trip_id for this match
    const tripId = this.matchTripMap.get(matchId);
    if (!tripId) {
      return {
        id: matchId,
        bouncie_trip_count: 0,
        has_coordinates: false,
      };
    }
    
    const { mockTripHistory } = await import("@/data/mockData");
    const trip = mockTripHistory.find(t => t.trip_id === tripId);
    
    if (trip && trip.coordinates && trip.coordinates.length > 0) {
      const coordinates = trip.coordinates;
      const startDate = trip.start_date ? new Date(trip.start_date) : new Date();
      const endDate = trip.end_date ? new Date(trip.end_date) : new Date();
      
      // Calculate duration in hours
      const durationMs = endDate.getTime() - startDate.getTime();
      const durationHours = durationMs / (1000 * 60 * 60);
      
      return {
        id: matchId,
        vehicle_id: trip.vehicle_id,
        imei: `imei_${String(trip.vehicle_id || 0).padStart(3, '0')}`,
        coordinates: coordinates,
        match_data: {
          all_trips: [{
            coordinates: coordinates,
            startTime: startDate.toISOString(),
            endTime: endDate.toISOString(),
            distance: trip.kilometers_driven || 0,
          }],
        },
        bouncie_trip_count: 1,
        aggregated_distance_km: trip.kilometers_driven || 0,
        total_duration_hours: durationHours,
        coordinate_count: coordinates.length,
        bouncie_earliest_start: startDate.toISOString(),
        bouncie_latest_end: endDate.toISOString(),
        has_coordinates: true,
      };
    }
    
    // Fallback if no trip with coordinates found
    return {
      id: matchId,
      bouncie_trip_count: 0,
      has_coordinates: false,
    };
  }
}

export const bouncieService = new BouncieService();
