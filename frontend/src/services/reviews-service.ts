import { apiClient } from '@/lib/api-client';

export interface Review {
  id: number;
  customer_name?: string;
  customer_id?: string;
  vehicle_id?: number;
  rating?: number;
  date?: string;
  vehicle_info?: string;
  review_text?: string;
  areas_of_improvement: string[];
  host_response?: string;
  has_host_response: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ReviewsResponse {
  reviews: Review[];
  total: number;
  limit: number;
  offset: number;
}

class ReviewsService {
  async getReviews(params?: {
    vehicle_id?: number;
    min_rating?: number;
    has_response?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<ReviewsResponse> {
    const queryParams = new URLSearchParams();
    if (params?.vehicle_id !== undefined) {
      queryParams.append('vehicle_id', params.vehicle_id.toString());
    }
    if (params?.min_rating !== undefined) {
      queryParams.append('min_rating', params.min_rating.toString());
    }
    if (params?.has_response !== undefined) {
      queryParams.append('has_response', params.has_response.toString());
    }
    if (params?.limit) {
      queryParams.append('limit', params.limit.toString());
    }
    if (params?.offset) {
      queryParams.append('offset', params.offset.toString());
    }

    const response = await apiClient.get<{ success: boolean; data: ReviewsResponse }>(
      `/api/turo/data/reviews${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    );
    // API returns { success: true, data: { reviews: [], total: 0, limit: 50, offset: 0 } }
    return response.data;
  }
}

export const reviewsService = new ReviewsService();

