// Stub service for demo mode
export interface ROICalculation {
  id: number;
  vehicle_id?: number;
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
  updated_at?: string;
}

// In-memory storage for demo mode
let mockCalculations: ROICalculation[] = [];
let nextId = 1;

class ROIService {
  async getCalculations(params?: any): Promise<{ calculations: ROICalculation[]; total: number }> {
    // Return calculations sorted by most recent first
    const sorted = [...mockCalculations].sort((a, b) => 
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );
    return { calculations: sorted, total: sorted.length };
  }

  async saveCalculation(data: {
    vehicle_name: string;
    vehicle_price: number;
    daily_rate: number;
    booking_days: number;
    monthly_expenses: number;
    insurance_monthly: number;
    annual_depreciation: number;
    roi: number;
    annual_profit: number;
  }): Promise<ROICalculation> {
    const now = new Date().toISOString();
    const newCalculation: ROICalculation = {
      id: nextId++,
      vehicle_name: data.vehicle_name,
      vehicle_price: data.vehicle_price,
      daily_rate: data.daily_rate,
      booking_days: data.booking_days,
      monthly_expenses: data.monthly_expenses,
      insurance_monthly: data.insurance_monthly,
      annual_depreciation: data.annual_depreciation,
      roi: data.roi,
      annual_profit: data.annual_profit,
      created_at: now,
      updated_at: now,
    };
    mockCalculations.push(newCalculation);
    return newCalculation;
  }

  async updateCalculation(id: number, data: {
    vehicle_name: string;
    vehicle_price: number;
    daily_rate: number;
    booking_days: number;
    monthly_expenses: number;
    insurance_monthly: number;
    annual_depreciation: number;
    roi: number;
    annual_profit: number;
  }): Promise<ROICalculation> {
    const index = mockCalculations.findIndex(c => c.id === id);
    if (index === -1) {
      throw new Error("Calculation not found");
    }
    const updated: ROICalculation = {
      ...mockCalculations[index],
      ...data,
      updated_at: new Date().toISOString(),
    };
    mockCalculations[index] = updated;
    return updated;
  }

  async deleteCalculation(id: number): Promise<void> {
    const index = mockCalculations.findIndex(c => c.id === id);
    if (index === -1) {
      throw new Error("Calculation not found");
    }
    mockCalculations.splice(index, 1);
  }
}

export const roiService = new ROIService();
