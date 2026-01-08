import { apiClient } from '@/lib/api-client';

export interface TuroIntegrationStatus {
  connected: boolean;
  email?: string;
  has_active_session?: boolean;
  created_at?: string;
  updated_at?: string;
  message?: string;
}

export interface TuroConnectRequest {
  email: string;
  password: string;
}

export interface Turo2FARequest {
  session_id: string;
  code: string;
}

export interface TuroConnectResponse {
  requires_2fa?: boolean;
  session_id?: string;
  message?: string;
  email?: string;
  account_id?: number;
}

class TuroService {
  // Authentication
  async getIntegrationStatus(): Promise<TuroIntegrationStatus> {
    const response = await apiClient.get<{ success: boolean; data: TuroIntegrationStatus }>('/api/turo/auth/status');
    return response.data;
  }

  async connect(request: TuroConnectRequest): Promise<TuroConnectResponse> {
    const response = await apiClient.post<{ success: boolean; data: TuroConnectResponse }>('/api/turo/auth/connect', request);
    return response.data;
  }

  async submit2FA(request: Turo2FARequest): Promise<TuroConnectResponse> {
    const response = await apiClient.post<{ success: boolean; data: TuroConnectResponse }>('/api/turo/auth/connect/2fa', request);
    return response.data;
  }

  async disconnect(): Promise<void> {
    await apiClient.delete('/api/turo/auth/disconnect');
  }

  async deleteAllData(): Promise<void> {
    await apiClient.delete('/api/turo/auth/delete-all-data');
  }

  // Scraping
  async scrape(scraperType: 'all' | 'vehicles' | 'trips' | 'reviews' | 'earnings' | 'transactions', email?: string, password?: string): Promise<{ task_id: string; account_id: number; scraper_type: string }> {
    const response = await apiClient.post<{ task_id: string; account_id: number; scraper_type: string }>(
      `/api/turo/scrape/${scraperType}`,
      email && password ? { email, password } : {}
    );
    return response;
  }

  async getScrapeStatus(taskId: string): Promise<any> {
    const response = await apiClient.get<{ success: boolean; data: any }>(`/api/turo/scrape/${taskId}/status`);
    return response.data;
  }
}

export const turoService = new TuroService();

