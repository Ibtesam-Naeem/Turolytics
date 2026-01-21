import { apiClient } from "@/lib/api-client";

export interface WaitlistEntry {
  id: number;
  email: string;
  vehicle_count?: string | null;
  tracking_product?: string | null;
  tracking_product_other?: string | null;
  would_use?: string | null;
  price_willing?: string | null;
  feedback?: string | null;
  created_at: string;
  notified_at?: string | null;
}

export interface AuthResponse {
  success: boolean;
  authenticated: boolean;
  message?: string;
}

export interface WaitlistEntriesResponse {
  success: boolean;
  entries?: WaitlistEntry[];
  total?: number;
}

export const waitlistViewerService = {
  async authenticate(password: string): Promise<AuthResponse> {
    try {
      const response = await apiClient.post<AuthResponse>(
        "/api/waitlist/user/auth",
        { password },
        {
          credentials: "include", // Important: include cookies
        }
      );
      return response;
    } catch (error) {
      return {
        success: false,
        authenticated: false,
        message: error instanceof Error ? error.message : "Authentication failed",
      };
    }
  },

  async checkAuth(): Promise<AuthResponse> {
    try {
      // Try to fetch entries - if it works, we're authenticated
      const response = await apiClient.get<WaitlistEntriesResponse>(
        "/api/waitlist/user/entries",
        {
          credentials: "include",
        }
      );
      return {
        success: true,
        authenticated: response.success,
      };
    } catch (error) {
      return {
        success: false,
        authenticated: false,
      };
    }
  },

  async getEntries(): Promise<WaitlistEntriesResponse> {
    try {
      const response = await apiClient.get<WaitlistEntriesResponse>(
        "/api/waitlist/user/entries",
        {
          credentials: "include", // Important: include cookies
        }
      );
      return response;
    } catch (error) {
      return {
        success: false,
        entries: [],
        total: 0,
      };
    }
  },

  async logout(): Promise<{ success: boolean }> {
    try {
      await apiClient.post(
        "/api/waitlist/user/logout",
        {},
        {
          credentials: "include",
        }
      );
      return { success: true };
    } catch (error) {
      return { success: false };
    }
  },
};
