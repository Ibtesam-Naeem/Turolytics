import { useEffect, useRef, useState, useCallback } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  Car, 
  Fuel, 
  Gauge, 
  MapPin, 
  Navigation, 
  AlertTriangle,
  Zap,
  ChevronRight,
  Circle,
  X
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useRegionalSettings } from "@/contexts/RegionalSettingsContext";
import { formatDistance } from "@/lib/regional-utils";
import { useBouncieLiveData, LiveVehicleData } from "@/hooks/useBouncieLiveData";
import { tripsService } from "@/services/trips-service";

interface Vehicle {
  id: string;
  name: string;
  coordinates: [number, number];
  status: "moving" | "parked";
  speed: number;
  guest: string;
  location: string;
  fuel: number;
  totalKm: number;
  allowedKm: number;
  flags: {
    speedAlerts: number;
    hardBraking: number;
    rapidAcceleration: number;
  };
}

const initialVehicles: Vehicle[] = [
  // Vehicles on trips - Moving
  { 
    id: "1", 
    name: "2024 Tesla Model 3", 
    coordinates: [-122.4194, 37.7749], 
    status: "moving", 
    speed: 45,
    guest: "John Smith",
    location: "San Francisco, CA",
    fuel: 85,
    totalKm: 280,
    allowedKm: 400,
    flags: { speedAlerts: 0, hardBraking: 1, rapidAcceleration: 3 }
  },
  { 
    id: "3", 
    name: "2024 Audi A6", 
    coordinates: [-122.3321, 47.6062], 
    status: "moving", 
    speed: 55,
    guest: "Michael Chen",
    location: "Seattle, WA",
    fuel: 78,
    totalKm: 320,
    allowedKm: 600,
    flags: { speedAlerts: 0, hardBraking: 0, rapidAcceleration: 2 }
  },
  { 
    id: "5", 
    name: "2024 Toyota Camry", 
    coordinates: [-112.0740, 33.4484], 
    status: "moving", 
    speed: 38,
    guest: "James Rodriguez",
    location: "Phoenix, AZ",
    fuel: 92,
    totalKm: 95,
    allowedKm: 350,
    flags: { speedAlerts: 0, hardBraking: 0, rapidAcceleration: 0 }
  },
  { 
    id: "6", 
    name: "2023 Honda Accord", 
    coordinates: [-104.9903, 39.7392], 
    status: "moving", 
    speed: 48,
    guest: "Lisa Wang",
    location: "Denver, CO",
    fuel: 68,
    totalKm: 225,
    allowedKm: 500,
    flags: { speedAlerts: 0, hardBraking: 3, rapidAcceleration: 4 }
  },
  { 
    id: "8", 
    name: "2024 Porsche Cayenne", 
    coordinates: [-80.1918, 25.7617], 
    status: "moving", 
    speed: 62,
    guest: "Amanda Foster",
    location: "Miami, FL",
    fuel: 88,
    totalKm: 145,
    allowedKm: 550,
    flags: { speedAlerts: 0, hardBraking: 2, rapidAcceleration: 5 }
  },
  { 
    id: "9", 
    name: "2024 Mercedes-Benz GLE", 
    coordinates: [-121.8947, 36.6002], 
    status: "moving", 
    speed: 78,
    guest: "Alexander Rivera",
    location: "Monterey, CA",
    fuel: 72,
    totalKm: 420,
    allowedKm: 600,
    flags: { speedAlerts: 0, hardBraking: 0, rapidAcceleration: 2 }
  },
  { 
    id: "10", 
    name: "2023 Subaru Outback", 
    coordinates: [-110.7624, 43.4799], 
    status: "moving", 
    speed: 65,
    guest: "Ryan O'Connor",
    location: "Jackson Hole, WY",
    fuel: 76,
    totalKm: 340,
    allowedKm: 500,
    flags: { speedAlerts: 0, hardBraking: 0, rapidAcceleration: 1 }
  },
  { 
    id: "11", 
    name: "2024 Land Rover Defender", 
    coordinates: [-109.5498, 38.5733], 
    status: "moving", 
    speed: 42,
    guest: "Olivia Bennett",
    location: "Moab, UT",
    fuel: 58,
    totalKm: 520,
    allowedKm: 650,
    flags: { speedAlerts: 0, hardBraking: 5, rapidAcceleration: 4 }
  },
  
  // Vehicles on trips - Parked
  { 
    id: "2", 
    name: "2023 BMW X5", 
    coordinates: [-118.2437, 34.0522], 
    status: "parked", 
    speed: 0,
    guest: "Emma Wilson",
    location: "Los Angeles, CA",
    fuel: 62,
    totalKm: 150,
    allowedKm: 500,
    flags: { speedAlerts: 0, hardBraking: 0, rapidAcceleration: 0 }
  },
  { 
    id: "4", 
    name: "2023 Mercedes E-Class", 
    coordinates: [-122.6784, 45.5152], 
    status: "parked", 
    speed: 0,
    guest: "Sarah Mitchell",
    location: "Portland, OR",
    fuel: 45,
    totalKm: 420,
    allowedKm: 450,
    flags: { speedAlerts: 0, hardBraking: 2, rapidAcceleration: 1 }
  },
  { 
    id: "7", 
    name: "2024 Lexus RX350", 
    coordinates: [-97.7431, 30.2672], 
    status: "parked", 
    speed: 0,
    guest: "Robert Thompson",
    location: "Austin, TX",
    fuel: 31,
    totalKm: 380,
    allowedKm: 400,
    flags: { speedAlerts: 0, hardBraking: 1, rapidAcceleration: 0 }
  },
  { 
    id: "12", 
    name: "2023 Audi Q7", 
    coordinates: [-119.5383, 37.8651], 
    status: "parked", 
    speed: 0,
    guest: "Sophie Laurent",
    location: "Yosemite National Park, CA",
    fuel: 45,
    totalKm: 380,
    allowedKm: 500,
    flags: { speedAlerts: 0, hardBraking: 2, rapidAcceleration: 1 }
  },
  { 
    id: "13", 
    name: "2024 Chevrolet Tahoe", 
    coordinates: [-112.1129, 36.1069], 
    status: "parked", 
    speed: 0,
    guest: "Patricia Williams",
    location: "Grand Canyon, AZ",
    fuel: 38,
    totalKm: 480,
    allowedKm: 600,
    flags: { speedAlerts: 0, hardBraking: 1, rapidAcceleration: 2 }
  },
  
  // Vehicles NOT on trips - Available/Parked
  { 
    id: "14", 
    name: "2024 Mercedes C-Class", 
    coordinates: [-117.1933, 32.7338], 
    status: "parked", 
    speed: 0,
    guest: "Not on trip",
    location: "San Diego, CA",
    fuel: 95,
    totalKm: 0,
    allowedKm: 0,
    flags: { speedAlerts: 0, hardBraking: 0, rapidAcceleration: 0 }
  },
  { 
    id: "15", 
    name: "2024 Tesla Model Y", 
    coordinates: [-122.2712, 37.8044], 
    status: "parked", 
    speed: 0,
    guest: "Not on trip",
    location: "Oakland, CA",
    fuel: 88,
    totalKm: 0,
    allowedKm: 0,
    flags: { speedAlerts: 0, hardBraking: 0, rapidAcceleration: 0 }
  },
  { 
    id: "16", 
    name: "2023 Audi A4", 
    coordinates: [-121.8863, 37.3382], 
    status: "parked", 
    speed: 0,
    guest: "Not on trip",
    location: "San Jose, CA",
    fuel: 75,
    totalKm: 0,
    allowedKm: 0,
    flags: { speedAlerts: 0, hardBraking: 0, rapidAcceleration: 0 }
  },
  { 
    id: "17", 
    name: "2024 Porsche 911", 
    coordinates: [-118.4004, 34.0736], 
    status: "parked", 
    speed: 0,
    guest: "Not on trip",
    location: "Beverly Hills, CA",
    fuel: 92,
    totalKm: 0,
    allowedKm: 0,
    flags: { speedAlerts: 0, hardBraking: 0, rapidAcceleration: 0 }
  },
  { 
    id: "18", 
    name: "2023 Range Rover Sport", 
    coordinates: [-122.2015, 47.6101], 
    status: "parked", 
    speed: 0,
    guest: "Not on trip",
    location: "Bellevue, WA",
    fuel: 82,
    totalKm: 0,
    allowedKm: 0,
    flags: { speedAlerts: 0, hardBraking: 0, rapidAcceleration: 0 }
  },
  { 
    id: "19", 
    name: "2024 BMW 5 Series", 
    coordinates: [-80.1300, 25.7907], 
    status: "parked", 
    speed: 0,
    guest: "Not on trip",
    location: "South Beach, FL",
    fuel: 70,
    totalKm: 0,
    allowedKm: 0,
    flags: { speedAlerts: 0, hardBraking: 0, rapidAcceleration: 0 }
  },
  { 
    id: "20", 
    name: "2024 Ford Mustang GT", 
    coordinates: [-115.4330, 36.1352], 
    status: "parked", 
    speed: 0,
    guest: "Not on trip",
    location: "Red Rock Canyon, NV",
    fuel: 65,
    totalKm: 0,
    allowedKm: 0,
    flags: { speedAlerts: 0, hardBraking: 0, rapidAcceleration: 0 }
  },
  { 
    id: "21", 
    name: "2023 Lexus RX 350", 
    coordinates: [-111.9261, 33.4942], 
    status: "parked", 
    speed: 0,
    guest: "Not on trip",
    location: "Scottsdale, AZ",
    fuel: 78,
    totalKm: 0,
    allowedKm: 0,
    flags: { speedAlerts: 0, hardBraking: 0, rapidAcceleration: 0 }
  },
  { 
    id: "22", 
    name: "2024 Jeep Wrangler", 
    coordinates: [-106.8175, 39.1911], 
    status: "parked", 
    speed: 0,
    guest: "Not on trip",
    location: "Aspen, CO",
    fuel: 85,
    totalKm: 0,
    allowedKm: 0,
    flags: { speedAlerts: 0, hardBraking: 0, rapidAcceleration: 0 }
  },
  { 
    id: "23", 
    name: "2024 Cadillac Escalade", 
    coordinates: [-96.7970, 32.7767], 
    status: "parked", 
    speed: 0,
    guest: "Not on trip",
    location: "Downtown Dallas, TX",
    fuel: 90,
    totalKm: 0,
    allowedKm: 0,
    flags: { speedAlerts: 0, hardBraking: 0, rapidAcceleration: 0 }
  },
  { 
    id: "24", 
    name: "2023 Volvo XC90", 
    coordinates: [-123.9615, 45.8918], 
    status: "parked", 
    speed: 0,
    guest: "Not on trip",
    location: "Cannon Beach, OR",
    fuel: 80,
    totalKm: 0,
    allowedKm: 0,
    flags: { speedAlerts: 0, hardBraking: 0, rapidAcceleration: 0 }
  },
];

const MapPage = () => {
  const { distanceUnit } = useRegionalSettings();
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const markersRef = useRef<Map<string, mapboxgl.Marker>>(new Map());
  
  // Get real Bouncie live data
  const { liveVehicles, bouncieConnected, loading: bouncieLoading, error: bouncieError } = useBouncieLiveData(30000);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [selectedVehicle, setSelectedVehicle] = useState<Vehicle | null>(null);
  const [streetAddress, setStreetAddress] = useState<string>("");
  
  // Debug logging
  useEffect(() => {
    console.log('[MapPage] State update:', {
      bouncieConnected,
      bouncieLoading,
      bouncieError,
      liveVehiclesCount: liveVehicles.length,
      liveVehicles: liveVehicles,
      vehiclesCount: vehicles.length
    });
  }, [bouncieConnected, bouncieLoading, bouncieError, liveVehicles, vehicles]);

  // Reverse geocode to get street name
  const fetchStreetName = async (coordinates: [number, number]) => {
    try {
      const response = await fetch(
        `https://api.mapbox.com/geocoding/v5/mapbox.places/${coordinates[0]},${coordinates[1]}.json?access_token=${import.meta.env.VITE_MAPBOX_ACCESS_TOKEN || ""}&types=address,poi`
      );
      const data = await response.json();
      if (data.features && data.features.length > 0) {
        setStreetAddress(data.features[0].place_name);
      } else {
        setStreetAddress(`${coordinates[1].toFixed(4)}°N, ${Math.abs(coordinates[0]).toFixed(4)}°W`);
      }
    } catch {
      setStreetAddress(`${coordinates[1].toFixed(4)}°N, ${Math.abs(coordinates[0]).toFixed(4)}°W`);
    }
  };

  // Transform Bouncie live data + Turo trips into map vehicle format
  useEffect(() => {
    const loadVehicles = async () => {
      console.log('[MapPage] loadVehicles called');
      console.log('[MapPage] bouncieConnected:', bouncieConnected);
      console.log('[MapPage] liveVehicles:', liveVehicles);
      console.log('[MapPage] liveVehicles.length:', liveVehicles.length);
      
      // In demo mode (no Bouncie connection), use initial vehicles
      if (!bouncieConnected) {
        console.log('[MapPage] Demo mode - using initial vehicles');
        setVehicles(initialVehicles);
        return;
      }
      
      if (liveVehicles.length === 0) {
        console.log('[MapPage] No live vehicles available');
        setVehicles(initialVehicles); // Fallback to demo vehicles
        return;
      }

      try {
        // Get current Turo trips to get guest names and trip info
        let tripsMap = new Map();
        try {
          const tripsResponse = await tripsService.getCurrentTrips(50);
          tripsMap = new Map(
            tripsResponse.trips.map((trip: any) => [trip.vehicle_id, trip])
          );
          console.log('[MapPage] Loaded Turo trips:', tripsMap.size);
        } catch (err) {
          console.error("Failed to load trips:", err);
        }

        console.log('[MapPage] Filtering vehicles with location...');
        console.log('[MapPage] All liveVehicles:', JSON.stringify(liveVehicles, null, 2));
        const vehiclesWithLocation = liveVehicles.filter(v => {
          const hasLocation = v.location && typeof v.location === 'object' && 
                            typeof v.location.lat === 'number' && 
                            typeof v.location.lon === 'number';
          if (!hasLocation) {
            console.log(`[MapPage] Vehicle ${v.vehicleId} missing location:`, v.location);
          }
          return hasLocation;
        });
        console.log('[MapPage] Vehicles with location:', vehiclesWithLocation.length);
        console.log('[MapPage] Vehicles with location data:', vehiclesWithLocation);
        console.log('[MapPage] Vehicles without location:', liveVehicles.filter(v => !v.location || !v.location.lat || !v.location.lon));

        // Transform Bouncie live vehicles to map format
        const mapVehicles: Vehicle[] = vehiclesWithLocation
          .map((liveVehicle: LiveVehicleData) => {
            const trip = tripsMap.get(liveVehicle.vehicleId);
            const milesDriven = liveVehicle.milesDrivenToday || 0;
            const kmDriven = distanceUnit === "km" ? milesDriven * 1.60934 : milesDriven;
            
            return {
              id: liveVehicle.vehicleId.toString(),
              name: liveVehicle.vehicleName || `Vehicle ${liveVehicle.vehicleId}`,
              coordinates: [liveVehicle.location!.lon, liveVehicle.location!.lat] as [number, number], // Mapbox uses [lng, lat]
              status: liveVehicle.status === "moving" ? "moving" : "parked",
              speed: Math.round(liveVehicle.speed || 0),
              guest: trip?.customer_name || "No active trip",
              location: `${liveVehicle.location!.lat.toFixed(4)}, ${liveVehicle.location!.lon.toFixed(4)}`, // Will be replaced by geocoding
              fuel: Math.round(liveVehicle.fuelLevel || 0),
              totalKm: Math.round(kmDriven * 10) / 10,
              allowedKm: trip?.kilometers_included || 0,
              flags: {
                speedAlerts: 0, // Bouncie doesn't provide this directly
                hardBraking: liveVehicle.flags?.hardBraking || 0,
                rapidAcceleration: liveVehicle.flags?.rapidAcceleration || 0,
              },
            };
          });

        console.log('[MapPage] Final mapVehicles:', mapVehicles);
        console.log('[MapPage] Setting vehicles count:', mapVehicles.length);
        setVehicles(mapVehicles.length > 0 ? mapVehicles : initialVehicles); // Fallback to demo if no real data
      } catch (error) {
        console.error("Failed to load vehicles for map:", error);
        setVehicles(initialVehicles); // Fallback to demo vehicles on error
      }
    };

    // Always load vehicles - use real data if Bouncie connected, otherwise use demo
    if (!bouncieLoading) {
      loadVehicles();
    } else {
      // Show demo vehicles while loading
      setVehicles(initialVehicles);
    }
  }, [liveVehicles, bouncieConnected, bouncieLoading, distanceUnit]);

  // Fetch street name when vehicle is selected
  useEffect(() => {
    if (selectedVehicle) {
      fetchStreetName(selectedVehicle.coordinates);
    }
  }, [selectedVehicle]);

  // Initialize map
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    const mapboxToken = import.meta.env.VITE_MAPBOX_ACCESS_TOKEN || "";
    if (!mapboxToken) {
      console.error("Mapbox access token is not configured. Please set VITE_MAPBOX_ACCESS_TOKEN in your environment variables.");
      return;
    }
    mapboxgl.accessToken = mapboxToken;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: "mapbox://styles/mapbox/light-v11",
      center: [-98.5, 39.8],
      zoom: 3.5,
      pitch: 0,
    });

    map.current.addControl(new mapboxgl.NavigationControl({ showCompass: false }), "bottom-right");

    return () => {
      markersRef.current.forEach(marker => marker.remove());
      markersRef.current.clear();
      map.current?.remove();
      map.current = null;
    };
  }, []);

  // Add/update markers
  useEffect(() => {
    if (!map.current) return;

    vehicles.forEach((vehicle) => {
      let marker = markersRef.current.get(vehicle.id);

      if (marker) {
        marker.setLngLat(vehicle.coordinates);
      } else {
        const el = document.createElement("div");
        el.className = "vehicle-marker";
        el.innerHTML = `
          <div class="relative flex items-center justify-center">
            <div class="absolute w-10 h-10 rounded-full ${vehicle.status === 'moving' ? 'bg-emerald-500/20 animate-ping' : 'bg-primary/15'}"></div>
            <div class="relative w-5 h-5 rounded-full ${vehicle.status === 'moving' ? 'bg-emerald-500' : 'bg-primary'} border-2 border-card shadow-lg"></div>
          </div>
        `;
        el.style.cursor = "pointer";

        marker = new mapboxgl.Marker({ element: el, anchor: "center" })
          .setLngLat(vehicle.coordinates)
          .addTo(map.current!);

        el.addEventListener("click", () => {
          setSelectedVehicle(vehicle);
          map.current?.flyTo({
            center: vehicle.coordinates,
            zoom: 12,
            duration: 1000,
          });
        });

        markersRef.current.set(vehicle.id, marker);
      }
    });

    // Fit map to show all vehicles when they're loaded
    if (vehicles.length > 0 && map.current) {
      const bounds = new mapboxgl.LngLatBounds();
      vehicles.forEach(v => bounds.extend(v.coordinates));
      map.current.fitBounds(bounds, { 
        padding: { top: 100, bottom: 100, left: 100, right: 100 },
        duration: 1000,
        maxZoom: 10
      });
    }
  }, [vehicles]);

  // Real-time updates are handled by useBouncieLiveData hook (polls every 30 seconds)

  const handleVehicleClick = (vehicle: Vehicle) => {
    setSelectedVehicle(vehicle);
    map.current?.flyTo({
      center: vehicle.coordinates,
      zoom: 12,
      duration: 1000,
    });
  };

  const handleResetView = useCallback(() => {
    setSelectedVehicle(null);
    const bounds = new mapboxgl.LngLatBounds();
    vehicles.forEach(v => bounds.extend(v.coordinates));
    map.current?.fitBounds(bounds, { padding: 80, duration: 1000 });
  }, [vehicles]);

  // Handle ESC key to reset view
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && selectedVehicle) {
        handleResetView();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [selectedVehicle, handleResetView]);

  const movingCount = vehicles.filter(v => v.status === "moving").length;
  const parkedCount = vehicles.filter(v => v.status === "parked").length;
  const alertsCount = vehicles.filter(v => 
    v.flags.speedAlerts > 0 || v.flags.hardBraking > 0 || v.flags.rapidAcceleration > 0
  ).length;

  return (
    <div className="relative h-screen w-full overflow-hidden bg-background">
      {/* Map Container */}
      <div ref={mapContainer} className="absolute inset-0" />

      {/* Empty States - Only show if no vehicles at all */}
      {!bouncieConnected && !bouncieLoading && vehicles.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center z-20 bg-background/80 backdrop-blur-sm">
          <div className="text-center p-6 bg-card rounded-lg shadow-lg border border-border max-w-md">
            <p className="text-lg font-semibold mb-2">No Bouncie Connection</p>
            <p className="text-sm text-muted-foreground mb-4">
              Showing demo vehicles. Connect Bouncie in Settings to see live vehicle locations.
            </p>
          </div>
        </div>
      )}

      {bouncieConnected && vehicles.length === 0 && !bouncieLoading && (
        <div className="absolute inset-0 flex items-center justify-center z-20 bg-background/80 backdrop-blur-sm">
          <div className="text-center p-6 bg-card rounded-lg shadow-lg border border-border max-w-md">
            <p className="text-lg font-semibold mb-2">No Vehicles with Location Data</p>
            <p className="text-sm text-muted-foreground mb-4">
              No vehicles are currently reporting location data from Bouncie. Make sure your vehicles have active Bouncie devices.
            </p>
            {bouncieError && (
              <p className="text-sm text-destructive mb-2">Error: {bouncieError}</p>
            )}
            <p className="text-xs text-muted-foreground">
              Live vehicles: {liveVehicles.length} | 
              Vehicles with location: {liveVehicles.filter(v => v.location).length}
            </p>
            <details className="mt-4 text-left">
              <summary className="text-xs text-muted-foreground cursor-pointer">Debug Info</summary>
              <pre className="text-xs mt-2 p-2 bg-muted rounded overflow-auto max-h-40">
                {JSON.stringify(liveVehicles, null, 2)}
              </pre>
            </details>
          </div>
        </div>
      )}

      {bouncieLoading && (
        <div className="absolute inset-0 flex items-center justify-center z-20 bg-background/80 backdrop-blur-sm">
          <div className="text-center p-6 bg-card rounded-lg shadow-lg border border-border">
            <p className="text-sm text-muted-foreground">Loading vehicle locations...</p>
          </div>
        </div>
      )}

      {/* Top Stats Bar */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10">
        <div className="flex items-center gap-1 bg-card shadow-md border border-border rounded-lg px-1.5 py-1">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-emerald-50 text-emerald-700">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            <span className="text-xs font-medium">{movingCount} Moving</span>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-blue-50 text-blue-700">
            <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
            <span className="text-xs font-medium">{parkedCount} Parked</span>
          </div>
          {alertsCount > 0 && (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-amber-50 text-amber-700">
              <AlertTriangle className="w-3 h-3" />
              <span className="text-xs font-medium">{alertsCount} Alerts</span>
            </div>
          )}
        </div>
      </div>

      {/* Vehicle List - Compact Cards */}
      <div className="absolute left-4 top-16 bottom-4 z-10">
        <ScrollArea className="h-full w-72">
          <div className="space-y-2 pr-2">
            {vehicles.map((vehicle) => (
              <button
                key={vehicle.id}
                onClick={() => handleVehicleClick(vehicle)}
                className={cn(
                  "w-full text-left p-3.5 bg-card shadow-sm border border-border rounded-lg transition-all duration-150",
                  "hover:shadow-md hover:border-primary/40",
                  selectedVehicle?.id === vehicle.id && "ring-2 ring-primary border-primary"
                )}
              >
                <div className="flex items-start gap-3">
                  <div className={cn(
                    "w-2.5 h-2.5 rounded-full mt-1 shrink-0",
                    vehicle.status === "moving" ? "bg-emerald-500" : "bg-blue-500"
                  )} />
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-sm leading-tight truncate">{vehicle.name}</p>
                    <div className="flex items-center gap-1.5 mt-1.5 text-xs text-muted-foreground">
                      {vehicle.status === "moving" ? (
                        <span className="text-emerald-600 font-medium">{vehicle.speed} mph</span>
                      ) : (
                        <span>Parked</span>
                      )}
                      <span>•</span>
                      <span className={vehicle.fuel < 30 ? "text-red-500 font-medium" : ""}>{vehicle.fuel}%</span>
                      {(vehicle.flags.hardBraking > 0 || vehicle.flags.rapidAcceleration > 0) && (
                        <AlertTriangle className="w-3 h-3 text-amber-500 ml-0.5" />
                      )}
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </ScrollArea>
      </div>

      {/* Selected Vehicle Detail Panel */}
      {selectedVehicle && (
        <div className="absolute right-4 top-20 w-96 z-10">
          <div className="bg-card/95 backdrop-blur-md border border-border/50 rounded-2xl shadow-xl overflow-hidden">
            <div className="p-5 border-b border-border/50">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0 pr-2">
                  <h3 className="font-bold text-lg">{selectedVehicle.name}</h3>
                  <div className="flex items-center gap-1.5 mt-2 text-sm text-muted-foreground">
                    <MapPin className="w-4 h-4" />
                    <span className="truncate">{selectedVehicle.location}</span>
                  </div>
                </div>
                <Button 
                  variant="ghost" 
                  size="icon" 
                  className="h-9 w-9 shrink-0"
                  onClick={handleResetView}
                >
                  <X className="w-5 h-5" />
                </Button>
              </div>
            </div>

            <div className="p-5 space-y-5">
              {/* Status */}
              <div className="flex items-center justify-between">
                <span className="text-base text-muted-foreground font-medium">Status</span>
                <Badge 
                  variant={selectedVehicle.status === "moving" ? "default" : "secondary"}
                  className={cn(
                    "capitalize text-sm px-3 py-1",
                    selectedVehicle.status === "moving" && "bg-emerald-500/20 text-emerald-500 border-emerald-500/30"
                  )}
                >
                  <Circle className="w-2 h-2 fill-current mr-1.5" />
                  {selectedVehicle.status}
                </Badge>
              </div>

              {/* Guest */}
              <div className="flex items-center justify-between">
                <span className="text-base text-muted-foreground font-medium">Guest</span>
                <span className="text-base font-semibold">{selectedVehicle.guest}</span>
              </div>

              {/* Speed */}
              {selectedVehicle.status === "moving" && (
                <div className="bg-accent/50 rounded-xl p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <Gauge className="w-5 h-5 text-emerald-500" />
                      <span className="text-base font-medium">Current Speed</span>
                    </div>
                    <span className="text-2xl font-bold">{selectedVehicle.speed} <span className="text-base font-normal text-muted-foreground">mph</span></span>
                  </div>
                </div>
              )}

              {/* Fuel */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <Fuel className={cn(
                      "w-5 h-5",
                      selectedVehicle.fuel < 30 ? "text-red-500" : selectedVehicle.fuel < 60 ? "text-amber-500" : "text-emerald-500"
                    )} />
                    <span className="text-base font-medium">Fuel Level</span>
                  </div>
                  <span className="text-lg font-bold">{selectedVehicle.fuel}%</span>
                </div>
                <div className="h-2.5 bg-muted rounded-full overflow-hidden">
                  <div 
                    className={cn(
                      "h-full rounded-full transition-all",
                      selectedVehicle.fuel < 30 ? "bg-red-500" : selectedVehicle.fuel < 60 ? "bg-amber-500" : "bg-emerald-500"
                    )}
                    style={{ width: `${selectedVehicle.fuel}%` }}
                  />
                </div>
              </div>

              {/* Trip Progress */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <Navigation className="w-5 h-5 text-primary" />
                    <span className="text-base font-medium">Trip Distance</span>
                  </div>
                  <span className="text-base font-semibold">{formatDistance(selectedVehicle.totalKm, distanceUnit)} / {formatDistance(selectedVehicle.allowedKm, distanceUnit)}</span>
                </div>
                <div className="h-2.5 bg-muted rounded-full overflow-hidden">
                  <div 
                    className={cn(
                      "h-full rounded-full transition-all",
                      selectedVehicle.totalKm > selectedVehicle.allowedKm ? "bg-red-500" : "bg-primary"
                    )}
                    style={{ width: `${Math.min((selectedVehicle.totalKm / selectedVehicle.allowedKm) * 100, 100)}%` }}
                  />
                </div>
              </div>

              {/* Driving Alerts */}
              {(selectedVehicle.flags.hardBraking > 0 || selectedVehicle.flags.rapidAcceleration > 0) && (
                <div className="space-y-3 pt-3 border-t border-border/50">
                  <span className="text-sm text-muted-foreground uppercase tracking-wide font-semibold">Driving Alerts</span>
                  <div className="flex flex-wrap gap-2.5">
                    {selectedVehicle.flags.hardBraking > 0 && (
                      <Badge variant="outline" className="bg-red-500/10 text-red-500 border-red-500/30 text-sm px-3 py-1">
                        Hard Braking × {selectedVehicle.flags.hardBraking}
                      </Badge>
                    )}
                    {selectedVehicle.flags.rapidAcceleration > 0 && (
                      <Badge variant="outline" className="bg-amber-500/10 text-amber-500 border-amber-500/30 text-sm px-3 py-1">
                        <Zap className="w-3.5 h-3.5 mr-1.5" />
                        Rapid Accel × {selectedVehicle.flags.rapidAcceleration}
                      </Badge>
                    )}
                  </div>
                </div>
              )}

              {/* Street Address */}
              <div className="pt-3 border-t border-border/50">
                <div className="flex items-start gap-2">
                  <MapPin className="w-4 h-4 text-muted-foreground mt-0.5 shrink-0" />
                  <span className="text-sm text-muted-foreground leading-relaxed">
                    {streetAddress || "Loading address..."}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MapPage;