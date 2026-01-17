import { apiClient } from "@/lib/api-client";

export interface WaitlistEntry {
  id: number;
  email: string;
  vehicle_count?: string | null;
  tracking_product?: string | null;
  would_use?: string | null;
  price_willing?: string | null;
  feedback?: string | null;
  created_at: string;
  notified_at?: string | null;
}

export interface WaitlistListResponse {
  success: boolean;
  entries?: WaitlistEntry[];
  total?: number;
  page?: number;
  page_size?: number;
}

export interface BulkEmailResponse {
  success: boolean;
  message?: string;
  total_recipients?: number;
  sent_count?: number;
  failed_count?: number;
  failed_emails?: string[];
}

export const waitlistAdminService = {
  async getEntries(
    page: number = 1,
    pageSize: number = 50,
    search?: string
  ): Promise<WaitlistListResponse> {
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      });
      if (search) {
        params.append("search", search);
      }

      const response = await apiClient.get<WaitlistListResponse>(
        `/api/waitlist/admin?${params.toString()}`
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

  async sendBulkEmail(): Promise<BulkEmailResponse> {
    try {
      const response = await apiClient.post<BulkEmailResponse>(
        "/api/waitlist/admin/send-bulk"
      );
      return response;
    } catch (error) {
      return {
        success: false,
        message: error instanceof Error ? error.message : "Failed to send bulk email",
        total_recipients: 0,
        sent_count: 0,
        failed_count: 0,
      };
    }
  },
};
