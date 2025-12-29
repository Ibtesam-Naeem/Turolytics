import { apiClient } from '@/lib/api-client';
import { bouncieApiClient } from './bouncie-api-client';

export interface BouncieIntegrationStatus {
  connected: boolean;
  expired?: boolean;
  bouncie_user_id?: string;
  bouncie_user_email?: string;
  expires_at?: string;
  created_at?: string;
  updated_at?: string;
  message?: string;
}

export interface BouncieVehicleMapping {
  id: number;
  vehicle_id: number;
  vehicle_name?: string;
  imei: string;
  bouncie_nickname?: string;
  bouncie_vin?: string;
  created_at?: string;
  updated_at?: string;
}

export interface BouncieTripMatch {
  id: number;
  trip_id?: string;
  turo_trip_id: number;
  bouncie_trip_count: number;
  aggregated_distance_km?: number;
  aggregated_distance_miles?: number;
  total_duration_hours?: number;
  coordinate_count?: number;
  has_polyline: boolean;
  has_coordinates: boolean;
  has_match_data: boolean;
  bouncie_earliest_start?: string;
  bouncie_latest_end?: string;
  created_at?: string;
  updated_at?: string;
}

export interface CreateVehicleMappingRequest {
  vehicle_id: number;
  imei: string;
  bouncie_nickname?: string;
  bouncie_vin?: string;
}

export interface UpdateVehicleMappingRequest {
  vehicle_id?: number;
  imei?: string;
  bouncie_nickname?: string;
  bouncie_vin?: string;
}

export interface MatchRequest {
  authorization_code?: string;
  trip_id?: string;
  imei?: string;
  days_back?: number;
}

export interface BouncieVehicle {
  imei: string;
  nickname?: string;
  vin?: string;
  make?: string;
  model?: string;
  year?: number;
  [key: string]: any;
}

export interface BouncieTrip {
  id?: string;
  imei: string;
  startTime?: string;
  endTime?: string;
  distance?: number;
  gps?: any;
  [key: string]: any;
}

export interface BouncieDTCCode {
  id: number;
  vehicle_id?: number;
  vehicle_name?: string;
  imei: string;
  code: string;
  description?: string;
  is_active: boolean;
  occurred_at: string;
  cleared_at?: string;
  created_at?: string;
  updated_at?: string;
}

class BouncieService {
  // Authentication
  async getAuthorizationUrl(popup: boolean = false): Promise<string> {
    const response = await apiClient.get<{ success: boolean; data: { authorization_url: string } }>(
      `/api/bouncie/auth/url${popup ? '?popup=true' : ''}`
    );
    return response.data.authorization_url;
  }

  async getIntegrationStatus(): Promise<BouncieIntegrationStatus> {
    const response = await apiClient.get<{ success: boolean; data: BouncieIntegrationStatus }>('/api/bouncie/auth/status');
    return response.data;
  }

  async disconnect(): Promise<void> {
    await apiClient.delete('/api/bouncie/auth/disconnect');
    this.clearTokenCache(); // Clear cached token on disconnect
  }

  async deleteAllData(): Promise<void> {
    await apiClient.delete('/api/bouncie/auth/delete-all-data');
  }

  // Vehicle Mappings
  async getVehicleMappings(limit: number = 100, offset: number = 0): Promise<{ mappings: BouncieVehicleMapping[]; total: number }> {
    const response = await apiClient.get<{ success: boolean; data: { mappings: BouncieVehicleMapping[]; total: number } }>(
      `/api/bouncie/mappings?limit=${limit}&offset=${offset}`
    );
    return response.data;
  }

  async getVehicleMapping(mappingId: number): Promise<BouncieVehicleMapping> {
    const response = await apiClient.get<{ success: boolean; data: BouncieVehicleMapping }>(`/api/bouncie/mappings/${mappingId}`);
    return response.data;
  }

  async createVehicleMapping(request: CreateVehicleMappingRequest): Promise<BouncieVehicleMapping> {
    const response = await apiClient.post<{ success: boolean; data: { mapping: BouncieVehicleMapping } }>(
      '/api/bouncie/mappings',
      request
    );
    return response.data.mapping;
  }

  async updateVehicleMapping(mappingId: number, request: UpdateVehicleMappingRequest): Promise<BouncieVehicleMapping> {
    const response = await apiClient.put<{ success: boolean; data: { mapping: BouncieVehicleMapping } }>(
      `/api/bouncie/mappings/${mappingId}`,
      request
    );
    return response.data.mapping;
  }

  async deleteVehicleMapping(mappingId: number): Promise<void> {
    await apiClient.delete(`/api/bouncie/mappings/${mappingId}`);
  }

  // Trip Matches
  async getTripMatches(
    tripId?: string,
    includePolylines: boolean = false,
    limit: number = 100,
    offset: number = 0
  ): Promise<{ matches: BouncieTripMatch[]; total: number }> {
    const params = new URLSearchParams({
      include_polylines: includePolylines.toString(),
      limit: limit.toString(),
      offset: offset.toString(),
    });
    if (tripId) {
      params.append('trip_id', tripId);
    }
    const response = await apiClient.get<{ success: boolean; data: { matches: BouncieTripMatch[]; total: number } }>(
      `/api/bouncie/matches?${params.toString()}`
    );
    return response.data;
  }

  async getTripMatchDetail(matchId: number, includeFullData: boolean = false): Promise<BouncieTripMatch> {
    const response = await apiClient.get<{ success: boolean; data: BouncieTripMatch }>(
      `/api/bouncie/matches/${matchId}?include_full_data=${includeFullData}`
    );
    return response.data;
  }

  // Actions
  async matchTrips(request: MatchRequest): Promise<any> {
    const response = await apiClient.post<{ success: boolean; data: any }>('/api/bouncie/matches/match', request);
    return response.data;
  }

  async syncMatches(daysBack: number = 365, skipExisting: boolean = true, forceRematch: boolean = false): Promise<any> {
    const response = await apiClient.post<{ success: boolean; data: any }>(
      `/api/bouncie/matches/sync?days_back=${daysBack}&skip_existing=${skipExisting}&force_rematch=${forceRematch}`
    );
    return response.data;
  }

  // Direct Bouncie API calls (frontend → Bouncie)
  
  /**
   * Get vehicles from backend proxy (avoids CORS issues)
   */
  async getVehiclesDirect(): Promise<BouncieVehicle[]> {
    const response = await apiClient.get<{ success: boolean; data: BouncieVehicle[] }>('/api/bouncie/vehicles');
    return response.data || [];
  }

  /**
   * Get trips from backend proxy (avoids CORS issues)
   */
  async getTripsDirect(params: {
    gpsFormat?: string;
    startDate?: string; // ISO date string (YYYY-MM-DD)
    endDate?: string; // ISO date string (YYYY-MM-DD)
    imei?: string;
  } = {}): Promise<BouncieTrip[]> {
    if (!params.imei) {
      throw new Error('IMEI is required for fetching trips');
    }
    
    const queryParams = new URLSearchParams();
    if (params.gpsFormat) queryParams.append('gps_format', params.gpsFormat);
    if (params.startDate) queryParams.append('start_date', params.startDate);
    if (params.endDate) queryParams.append('end_date', params.endDate);
    if (params.imei) queryParams.append('imei', params.imei);

    const response = await apiClient.get<{ success: boolean; data: BouncieTrip[] }>(
      `/api/bouncie/trips?${queryParams.toString()}`
    );
    return response.data || [];
  }

  /**
   * Get live vehicle status - use backend proxy
   * Note: Individual vehicle endpoint doesn't exist, use getAllVehiclesWithStatus instead
   */
  async getVehicleStatus(imei: string): Promise<any> {
    // Individual vehicle endpoint doesn't exist, get all and filter
    const vehicles = await this.getAllVehiclesWithStatus();
    return vehicles.find(v => v.imei === imei) || null;
  }

  /**
   * Get today's trips for calculating miles driven today
   */
  async getTripsToday(imei?: string): Promise<BouncieTrip[]> {
    if (!imei) {
      return [];
    }
    
    const today = new Date().toISOString().split('T')[0];
    return this.getTripsDirect({
      imei: imei,
      startDate: today,
      endDate: today,
      gpsFormat: 'geojson'
    });
  }

  /**
   * Get active trip for a vehicle
   */
  async getActiveTrip(imei: string): Promise<BouncieTrip | null> {
    const today = new Date().toISOString().split('T')[0];
    const trips = await this.getTripsDirect({
      imei: imei,
      startDate: today,
      gpsFormat: 'geojson'
    });
    
    // Find trip without endTime (active trip)
    return trips.find(trip => !trip.endTime) || null;
  }

  /**
   * Get all vehicles with their current status (uses backend proxy)
   */
  async getAllVehiclesWithStatus(): Promise<BouncieVehicle[]> {
    return this.getVehiclesDirect();
  }

  /**
   * Get aggregated live vehicle data with location, speed, fuel, trips
   * This endpoint processes Bouncie data and returns a clean structure optimized for map display
   */
  async getLiveVehicles(): Promise<any[]> {
    const response = await apiClient.get<{ success: boolean; data: { vehicles: any[] } }>('/api/bouncie/live');
    return response.data?.vehicles || [];
  }

  /**
   * Get DTC codes (Diagnostic Trouble Codes)
   */
  async getDTCCodes(
    vehicleId?: number,
    imei?: string,
    activeOnly: boolean = true,
    limit: number = 100,
    offset: number = 0
  ): Promise<{ codes: BouncieDTCCode[]; total: number }> {
    const params = new URLSearchParams({
      active_only: activeOnly.toString(),
      limit: limit.toString(),
      offset: offset.toString(),
    });
    if (vehicleId) {
      params.append('vehicle_id', vehicleId.toString());
    }
    if (imei) {
      params.append('imei', imei);
    }
    const response = await apiClient.get<{ success: boolean; data: { codes: BouncieDTCCode[]; total: number } }>(
      `/api/bouncie/dtc-codes?${params.toString()}`
    );
    return response.data;
  }

  /**
   * Clear a DTC code (mark as resolved)
   */
  async clearDTCCode(codeId: number): Promise<BouncieDTCCode> {
    const response = await apiClient.post<{ success: boolean; data: { code: BouncieDTCCode; message: string } }>(
      `/api/bouncie/dtc-codes/${codeId}/clear`
    );
    return response.data.code;
  }

  /**
   * Clear token cache (call on disconnect)
   */
  clearTokenCache(): void {
    bouncieApiClient.clearTokenCache();
  }
}

export const bouncieService = new BouncieService();

