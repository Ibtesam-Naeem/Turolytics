import { apiClient } from '@/lib/api-client';

export interface ROICalculation {
  id: number;
  vehicle_name: string;
  vehicle_price: number;
  daily_rate: number;
  booking_days: number;
  monthly_expenses: number;
  insurance_monthly: number;
  annual_depreciation: number;
  roi: number;
  annual_profit: number;
  created_at: string;
  updated_at: string;
}

export interface ROICalculationCreate {
  vehicle_name: string;
  vehicle_price: number;
  daily_rate: number;
  booking_days: number;
  monthly_expenses: number;
  insurance_monthly: number;
  annual_depreciation: number;
  roi: number;
  annual_profit: number;
}

export interface ROICalculationsResponse {
  calculations: ROICalculation[];
  total: number;
}

class ROIService {
  /**
   * Get all saved ROI calculations for the current user
   */
  async getCalculations(): Promise<ROICalculationsResponse> {
    const response = await apiClient.get<{ success: boolean; data: ROICalculationsResponse }>(
      '/api/roi/calculations'
    );
    return response.data;
  }

  /**
   * Save a new ROI calculation
   */
  async saveCalculation(calculation: ROICalculationCreate): Promise<ROICalculation> {
    const response = await apiClient.post<{ success: boolean; data: { calculation: ROICalculation } }>(
      '/api/roi/calculations',
      calculation
    );
    return response.data.calculation;
  }

  /**
   * Update an existing ROI calculation
   */
  async updateCalculation(
    calculationId: number,
    updates: Partial<ROICalculationCreate>
  ): Promise<ROICalculation> {
    const response = await apiClient.patch<{ success: boolean; data: { calculation: ROICalculation } }>(
      `/api/roi/calculations/${calculationId}`,
      updates
    );
    return response.data.calculation;
  }

  /**
   * Delete an ROI calculation
   */
  async deleteCalculation(calculationId: number): Promise<void> {
    await apiClient.delete<{ success: boolean; data: { message: string } }>(
      `/api/roi/calculations/${calculationId}`
    );
  }
}

export const roiService = new ROIService();
