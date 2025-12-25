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
];

const MapPage = () => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const markersRef = useRef<Map<string, mapboxgl.Marker>>(new Map());
  const [vehicles, setVehicles] = useState<Vehicle[]>(initialVehicles);
  const [selectedVehicle, setSelectedVehicle] = useState<Vehicle | null>(null);
  const [streetAddress, setStreetAddress] = useState<string>("");

  // Reverse geocode to get street name
  const fetchStreetName = async (coordinates: [number, number]) => {
    try {
      const response = await fetch(
        `https://api.mapbox.com/geocoding/v5/mapbox.places/${coordinates[0]},${coordinates[1]}.json?access_token=pk.eyJ1IjoiaWJ0ZXNhbW5hZWVtIiwiYSI6ImNtaHY3amJ6aDA3dmUyaXExbG42OTdlbW0ifQ.mCJtklraw0s8tPOaXqkDYg&types=address,poi`
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

  // Fetch street name when vehicle is selected
  useEffect(() => {
    if (selectedVehicle) {
      fetchStreetName(selectedVehicle.coordinates);
    }
  }, [selectedVehicle]);

  // Initialize map
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    mapboxgl.accessToken = "pk.eyJ1IjoiaWJ0ZXNhbW5hZWVtIiwiYSI6ImNtaHY3amJ6aDA3dmUyaXExbG42OTdlbW0ifQ.mCJtklraw0s8tPOaXqkDYg";

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
  }, [vehicles]);

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setVehicles(prev => prev.map(vehicle => {
        if (vehicle.status === "moving") {
          const latChange = (Math.random() - 0.5) * 0.005;
          const lngChange = (Math.random() - 0.5) * 0.005;
          const speedChange = Math.floor((Math.random() - 0.5) * 8);
          const newSpeed = Math.max(25, Math.min(75, vehicle.speed + speedChange));
          const fuelConsumption = Math.random() * 0.3;
          const kmIncrease = Math.random() * 1.5;
          
          return {
            ...vehicle,
            coordinates: [vehicle.coordinates[0] + lngChange, vehicle.coordinates[1] + latChange] as [number, number],
            speed: newSpeed,
            fuel: Math.max(0, Math.round((vehicle.fuel - fuelConsumption) * 10) / 10),
            totalKm: Math.round((vehicle.totalKm + kmIncrease) * 10) / 10
          };
        }
        return vehicle;
      }));
    }, 3000);

    return () => clearInterval(interval);
  }, []);

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
                  <span className="text-base font-semibold">{selectedVehicle.totalKm} / {selectedVehicle.allowedKm} km</span>
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