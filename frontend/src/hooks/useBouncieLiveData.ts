import { useState, useEffect, useCallback } from "react";
import { bouncieService } from "@/services/bouncie-service";
import { useRegionalSettings } from "@/contexts/RegionalSettingsContext";
import { useBouncieAutoReauth } from "./useBouncieAutoReauth";

export interface LiveVehicleData {
  vehicleId: number;
  vehicleName: string;
  imei: string;
  status?: "moving" | "parked" | "offline";
  location?: {
    lat: number;
    lon: number;
  };
  speed?: number;
  fuelLevel?: number;
  batteryLevel?: number;
  milesDrivenToday?: number;
  activeTrip?: any;
  flags?: {
    rapidAcceleration?: number;
    hardBraking?: number;
    engineLight?: boolean;
  };
  engineInfo?: any; // Engine information from Bouncie (standardEngine field)
  odometer?: number; // Current odometer reading in miles
}

export const useBouncieLiveData = (refreshInterval: number = 30000) => {
  const { distanceUnit } = useRegionalSettings();
  const { handleErrorWithAutoReauth } = useBouncieAutoReauth();
  const [bouncieConnected, setBouncieConnected] = useState<boolean | null>(null);
  const [liveVehicles, setLiveVehicles] = useState<LiveVehicleData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalMilesToday, setTotalMilesToday] = useState(0);
  const [reauthing, setReauthing] = useState(false);

  // Check Bouncie connection status
  const checkConnection = useCallback(async () => {
    try {
      const status = await bouncieService.getIntegrationStatus();
      setBouncieConnected(status.connected);
      return status.connected;
    } catch (err) {
      setBouncieConnected(false);
      return false;
    }
  }, []);


  // Fetch live data for all vehicles using the new aggregated endpoint
  const fetchLiveData = useCallback(async () => {
    if (!bouncieConnected) {
      console.log('[Bouncie Live Data] Bouncie not connected');
      setLoading(false);
      return;
    }

    try {
      setError(null);
      
      // Use the new aggregated endpoint that processes data similar to the test script
      const liveVehiclesData = await bouncieService.getLiveVehicles();
      console.log('[Bouncie Live Data] Live vehicles from API:', liveVehiclesData);
      console.log('[Bouncie Live Data] Number of vehicles:', liveVehiclesData.length);
      
      if (liveVehiclesData.length === 0) {
        console.log('[Bouncie Live Data] No vehicles with location data found');
        setLiveVehicles([]);
        setTotalMilesToday(0);
        setLoading(false);
        return;
      }

      // Transform backend data to frontend format
      // Backend returns milesDrivenToday in MILES (from Bouncie API)
      // We convert to km here, then formatDistance will handle unit conversion for display
      const liveData: LiveVehicleData[] = liveVehiclesData.map((vehicle: any) => {
        // Convert miles to km (formatDistance expects km as input)
        const km = (vehicle.milesDrivenToday || 0) * 1.60934;
        
        return {
          vehicleId: vehicle.vehicleId,
          vehicleName: vehicle.vehicleName,
          imei: vehicle.imei,
          location: vehicle.location,
          status: vehicle.status || "parked",
          speed: vehicle.speed || 0,
          fuelLevel: vehicle.fuelLevel,
          batteryLevel: vehicle.batteryLevel,
          milesDrivenToday: km, // Store in km (formatDistance will convert for display)
          activeTrip: vehicle.activeTrip,
          flags: vehicle.flags || {},
          engineInfo: vehicle.engineInfo,
          odometer: vehicle.odometer,
        };
      });

      // Calculate total (in km - formatDistance will convert for display)
      const totalKm = liveData.reduce((sum, v) => sum + (v.milesDrivenToday || 0), 0);
      
      console.log('[Bouncie Live Data] Processed liveData:', liveData);
      console.log('[Bouncie Live Data] Vehicles with location:', liveData.filter(v => v.location));
      
      setLiveVehicles(liveData);
      setTotalMilesToday(totalKm); // Store in km, formatDistance will convert for display
      setLoading(false);
    } catch (err) {
      console.error('Failed to fetch live Bouncie data:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch live vehicle data';
      setError(errorMessage);
      setLoading(false);
      
      // Check if this is a token expiration error and trigger auto re-auth
      const wasReauthing = await handleErrorWithAutoReauth(err);
      if (wasReauthing) {
        setReauthing(true);
        // Re-check connection status after re-auth
        setTimeout(async () => {
          const connected = await checkConnection();
          if (connected) {
            setReauthing(false);
            setError(null);
            // Retry fetching data
            await fetchLiveData();
          } else {
            setReauthing(false);
          }
        }, 2000);
      }
    }
  }, [bouncieConnected, distanceUnit, handleErrorWithAutoReauth, checkConnection]);

  // Initial load
  useEffect(() => {
    const initialize = async () => {
      const connected = await checkConnection();
      if (connected) {
        await fetchLiveData();
      } else {
        setLoading(false);
      }
    };
    initialize();
  }, [checkConnection, fetchLiveData]);

  // Set up polling for live data
  useEffect(() => {
    if (!bouncieConnected) return;

    const interval = setInterval(() => {
      fetchLiveData();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [bouncieConnected, fetchLiveData, refreshInterval]);

  // Get live data for a specific vehicle
  const getVehicleLiveData = useCallback((vehicleId: number): LiveVehicleData | undefined => {
    return liveVehicles.find(v => v.vehicleId === vehicleId);
  }, [liveVehicles]);

  // Get live data by IMEI
  const getVehicleLiveDataByImei = useCallback((imei: string): LiveVehicleData | undefined => {
    return liveVehicles.find(v => v.imei === imei);
  }, [liveVehicles]);

  return {
    bouncieConnected,
    liveVehicles,
    totalMilesToday,
    loading: loading || reauthing,
    error,
    reauthing,
    refresh: fetchLiveData,
    getVehicleLiveData,
    getVehicleLiveDataByImei,
  };
};

