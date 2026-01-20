// Stub hook for demo mode
import { useState, useEffect, useCallback } from "react";

export interface LiveVehicleData {
  vehicleId: number;
  vehicleName: string;
  imei?: string;
  location?: { lat: number; lon: number };
  status?: string;
  speed?: number;
  fuelLevel?: number;
  batteryLevel?: number;
  milesDrivenToday?: number;
  activeTrip?: any;
  flags?: any;
  engineInfo?: any;
  odometer?: number;
}

export const useBouncieLiveData = (refreshInterval: number = 60000) => {
  const [bouncieConnected, setBouncieConnected] = useState<boolean>(true); // Demo: show as connected
  const [liveVehicles, setLiveVehicles] = useState<LiveVehicleData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalMilesToday, setTotalMilesToday] = useState(0);

  // Demo mode - return mock live data
  useEffect(() => {
    setBouncieConnected(true);
    setLoading(false);
    
    // Mock live vehicles with locations, statuses, and varied trip states
    // Vehicles on trips - Moving
    const mockLiveVehicles: LiveVehicleData[] = [
      { vehicleId: 1, vehicleName: "2024 Tesla Model 3", imei: "imei_001", location: { lat: 37.7749, lon: -122.4194 }, status: "moving", speed: 45, milesDrivenToday: 280, fuelLevel: 85, activeTrip: { maxSpeed: 68 }, flags: { hardBraking: 1, rapidAcceleration: 3 } },
      { vehicleId: 3, vehicleName: "2024 Audi A6", imei: "imei_003", location: { lat: 47.6062, lon: -122.3321 }, status: "moving", speed: 55, milesDrivenToday: 320, fuelLevel: 78, activeTrip: { maxSpeed: 75 }, flags: { hardBraking: 0, rapidAcceleration: 2 } },
      { vehicleId: 5, vehicleName: "2024 Toyota Camry", imei: "imei_005", location: { lat: 33.4484, lon: -112.0740 }, status: "moving", speed: 38, milesDrivenToday: 95, fuelLevel: 92, activeTrip: { maxSpeed: 60 }, flags: { hardBraking: 0, rapidAcceleration: 0 } },
      { vehicleId: 9, vehicleName: "2024 Mercedes-Benz GLE", imei: "imei_009", location: { lat: 36.6002, lon: -121.8947 }, status: "moving", speed: 78, milesDrivenToday: 420, fuelLevel: 72, activeTrip: { maxSpeed: 95 }, flags: { hardBraking: 0, rapidAcceleration: 2 } },
      
      // Vehicles on trips - Parked
      { vehicleId: 2, vehicleName: "2023 BMW X5", imei: "imei_002", location: { lat: 34.0522, lon: -118.2437 }, status: "parked", speed: 0, milesDrivenToday: 150, fuelLevel: 62, flags: { hardBraking: 0, rapidAcceleration: 0 } },
      { vehicleId: 4, vehicleName: "2023 Mercedes E-Class", imei: "imei_004", location: { lat: 45.5152, lon: -122.6784 }, status: "parked", speed: 0, milesDrivenToday: 420, fuelLevel: 45, flags: { hardBraking: 2, rapidAcceleration: 1 } },
      { vehicleId: 7, vehicleName: "2024 Lexus RX350", imei: "imei_007", location: { lat: 30.2672, lon: -97.7431 }, status: "parked", speed: 0, milesDrivenToday: 380, fuelLevel: 31, flags: { hardBraking: 1, rapidAcceleration: 0 } },
      
      // Vehicles NOT on trips - Available/Parked
      { vehicleId: 15, vehicleName: "2024 Tesla Model Y", imei: "imei_015", location: { lat: 37.8044, lon: -122.2712 }, status: "parked", speed: 0, milesDrivenToday: 0, fuelLevel: 88, flags: { hardBraking: 0, rapidAcceleration: 0 } },
      { vehicleId: 17, vehicleName: "2024 Porsche 911", imei: "imei_017", location: { lat: 34.0736, lon: -118.4004 }, status: "parked", speed: 0, milesDrivenToday: 0, fuelLevel: 92, flags: { hardBraking: 0, rapidAcceleration: 0 } },
      { vehicleId: 18, vehicleName: "2023 Range Rover Sport", imei: "imei_018", location: { lat: 47.6101, lon: -122.2015 }, status: "parked", speed: 0, milesDrivenToday: 0, fuelLevel: 82, flags: { hardBraking: 0, rapidAcceleration: 0 } },
      { vehicleId: 19, vehicleName: "2024 BMW 5 Series", imei: "imei_019", location: { lat: 25.7907, lon: -80.1300 }, status: "parked", speed: 0, milesDrivenToday: 0, fuelLevel: 70, flags: { hardBraking: 0, rapidAcceleration: 0 } },
      { vehicleId: 20, vehicleName: "2024 Ford Mustang GT", imei: "imei_020", location: { lat: 36.1352, lon: -115.4330 }, status: "parked", speed: 0, milesDrivenToday: 0, fuelLevel: 65, flags: { hardBraking: 0, rapidAcceleration: 0 } },
    ];
    
    setLiveVehicles(mockLiveVehicles);
    // Total miles = sum of all vehicles (in km, will be converted for display)
    const totalKm = mockLiveVehicles.reduce((sum, v) => sum + (v.milesDrivenToday || 0), 0);
    setTotalMilesToday(totalKm);
  }, []);

  const getVehicleLiveData = useCallback((vehicleId: number): LiveVehicleData | undefined => {
    return liveVehicles.find(v => v.vehicleId === vehicleId);
  }, [liveVehicles]);

  const getVehicleLiveDataByImei = useCallback((imei: string): LiveVehicleData | undefined => {
    return liveVehicles.find(v => v.imei === imei);
  }, [liveVehicles]);

  return {
    liveVehicles,
    bouncieConnected,
    loading,
    error,
    totalMilesToday,
    getVehicleLiveData,
    getVehicleLiveDataByImei,
  };
};
