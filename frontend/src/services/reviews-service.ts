// Stub service for demo mode
import { mockReviews } from "@/data/mockData";

export interface Review {
  id: string;
  vehicle_name?: string;
  guest_name?: string;
  customer_name?: string;
  vehicle_info?: string;
  rating?: number;
  comment?: string;
  review_text?: string;
  date?: string;
  has_host_response?: boolean;
  host_response?: string | null;
  areas_of_improvement?: string[];
}

class ReviewsService {
  async getReviews(params?: any): Promise<{ reviews: Review[]; total: number }> {
    // Demo mode - return mock reviews
    let filteredReviews = [...mockReviews];
    
    // Apply filters
    if (params?.min_rating) {
      filteredReviews = filteredReviews.filter(r => (r.rating || 0) >= params.min_rating);
    }
    
    // Apply pagination
    const limit = params?.limit || 50;
    const offset = params?.offset || 0;
    const paginatedReviews = filteredReviews.slice(offset, offset + limit);
    
    return { 
      reviews: paginatedReviews, 
      total: filteredReviews.length 
    };
  }
}

export const reviewsService = new ReviewsService();
