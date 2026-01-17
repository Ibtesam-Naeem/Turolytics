import { apiClient } from "@/lib/api-client";

export interface WaitlistRequest {
  email: string;
  vehicleCount?: string | null;
  trackingProduct?: string | null;
  trackingProductOther?: string | null;
  wouldUse?: string | null;
  priceWilling?: string | null;
  feedback?: string | null;
}

export interface WaitlistResponse {
  success: boolean;
  error?: string;
  message?: string;
  position?: number;
  total?: number;
}

export const waitlistService = {
  async joinWaitlist(data: WaitlistRequest): Promise<WaitlistResponse> {
    try {
      const response = await apiClient.post<{
        success: boolean;
        message: string;
        position?: number;
        total?: number;
      }>("/api/waitlist", data);

      return {
        success: response.success,
        message: response.message,
        position: response.position,
        total: response.total,
      };
    } catch (error) {
      // Handle HTTPException from backend
      if (error instanceof Error) {
        // The apiClient throws errors with the detail message
        return {
          success: false,
          error: error.message,
        };
      }
      return {
        success: false,
        error: "An unexpected error occurred",
      };
    }
  },
};
