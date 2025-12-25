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

class BouncieService {
  // Authentication
  async getAuthorizationUrl(): Promise<string> {
    const response = await apiClient.get<{ success: boolean; data: { authorization_url: string } }>('/api/bouncie/auth/url');
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
   * Get vehicles directly from Bouncie API
   */
  async getVehiclesDirect(): Promise<BouncieVehicle[]> {
    return bouncieApiClient.getVehicles();
  }

  /**
   * Get trips directly from Bouncie API
   */
  async getTripsDirect(params: {
    gpsFormat?: string;
    startDate?: string; // ISO date string (YYYY-MM-DD)
    endDate?: string; // ISO date string (YYYY-MM-DD)
    imei?: string;
  } = {}): Promise<BouncieTrip[]> {
    const bouncieParams: {
      gpsFormat?: string;
      'starts-after'?: string;
      'ends-before'?: string;
      imei?: string;
    } = {};

    if (params.gpsFormat) bouncieParams.gpsFormat = params.gpsFormat;
    if (params.startDate) bouncieParams['starts-after'] = params.startDate;
    if (params.endDate) bouncieParams['ends-before'] = params.endDate;
    if (params.imei) bouncieParams.imei = params.imei;

    return bouncieApiClient.getTrips(bouncieParams);
  }

  /**
   * Clear token cache (call on disconnect)
   */
  clearTokenCache(): void {
    bouncieApiClient.clearTokenCache();
  }
}

export const bouncieService = new BouncieService();

