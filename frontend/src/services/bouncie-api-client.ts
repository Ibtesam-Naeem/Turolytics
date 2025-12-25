import { apiClient } from '@/lib/api-client';

const BOUNCIE_API_BASE = 'https://api.bouncie.dev/v1';

interface TokenResponse {
  access_token: string;
  expires_in: number;
  token_type: string;
}

interface CachedToken {
  token: string;
  expiresAt: number;
}

class BouncieApiClient {
  private tokenCache: CachedToken | null = null;
  private tokenPromise: Promise<string> | null = null;

  /**
   * Get access token from backend, with caching and automatic refresh
   */
  private async getAccessToken(forceRefresh: boolean = false): Promise<string> {
    // Return cached token if still valid
    if (!forceRefresh && this.tokenCache && this.tokenCache.expiresAt > Date.now()) {
      return this.tokenCache.token;
    }

    // If already fetching token, return the existing promise
    if (this.tokenPromise) {
      return this.tokenPromise;
    }

    // Fetch new token from backend
    this.tokenPromise = (async () => {
      try {
        const response = await apiClient.get<{ success: boolean; data: TokenResponse }>(
          '/api/bouncie/auth/token'
        );

        if (!response.success || !response.data.access_token) {
          throw new Error('Failed to get Bouncie access token');
        }

        const { access_token, expires_in } = response.data;
        
        // Cache token with 5 minute buffer before expiration
        const bufferMs = 5 * 60 * 1000; // 5 minutes
        this.tokenCache = {
          token: access_token,
          expiresAt: Date.now() + (expires_in * 1000) - bufferMs,
        };

        return access_token;
      } catch (error) {
        this.tokenCache = null;
        throw error;
      } finally {
        this.tokenPromise = null;
      }
    })();

    return this.tokenPromise;
  }

  /**
   * Make a request to Bouncie API with automatic token management
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${BOUNCIE_API_BASE}${endpoint}`;
    let token = await this.getAccessToken();

    const makeRequest = async (): Promise<Response> => {
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...(options.headers as HeadersInit),
      };

      return fetch(url, {
        ...options,
        headers,
      });
    };

    let response = await makeRequest();

    // If 401, refresh token and retry once
    if (response.status === 401) {
      token = await this.getAccessToken(true); // Force refresh
      response = await makeRequest();
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: response.statusText }));
      throw new Error(error.message || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Get all vehicles from Bouncie
   */
  async getVehicles(): Promise<any[]> {
    const data = await this.request<any[]>('/vehicles');
    return Array.isArray(data) ? data : [];
  }

  /**
   * Get trips from Bouncie
   */
  async getTrips(params: {
    gpsFormat?: string;
    'starts-after'?: string;
    'ends-before'?: string;
    imei?: string;
  } = {}): Promise<any[]> {
    const queryParams = new URLSearchParams();
    
    if (params.gpsFormat) queryParams.append('gpsFormat', params.gpsFormat);
    if (params['starts-after']) queryParams.append('starts-after', params['starts-after']);
    if (params['ends-before']) queryParams.append('ends-before', params['ends-before']);
    if (params.imei) queryParams.append('imei', params.imei);

    const queryString = queryParams.toString();
    const endpoint = `/trips${queryString ? `?${queryString}` : ''}`;
    
    const data = await this.request<any[]>(endpoint);
    return Array.isArray(data) ? data : [];
  }

  /**
   * Clear cached token (useful on disconnect)
   */
  clearTokenCache(): void {
    this.tokenCache = null;
    this.tokenPromise = null;
  }
}

export const bouncieApiClient = new BouncieApiClient();

