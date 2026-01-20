// Stub service for demo mode
export interface TuroIntegrationStatus {
  connected: boolean;
  email?: string;
  has_active_session?: boolean;
  message?: string;
}

class TuroService {
  async getIntegrationStatus(): Promise<TuroIntegrationStatus> {
    return { connected: false, has_active_session: false };
  }

  async connect(credentials: { email: string; password: string }): Promise<any> {
    throw new Error("Turo integration not available in demo mode");
  }

  async submit2FA(data: { code: string; session_id: string }): Promise<any> {
    throw new Error("Turo integration not available in demo mode");
  }

  async disconnect(): Promise<void> {
    // Stub
  }

  async scrape(type: string): Promise<{ task_id: string }> {
    throw new Error("Turo scraping not available in demo mode");
  }

  async getScrapeStatus(taskId: string): Promise<any> {
    throw new Error("Turo scraping not available in demo mode");
  }
}

export const turoService = new TuroService();
