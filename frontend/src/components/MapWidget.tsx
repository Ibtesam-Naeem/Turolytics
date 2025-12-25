import { useEffect, useRef } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

interface VehicleLocation {
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

const defaultVehicles: VehicleLocation[] = [
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
    flags: {
      speedAlerts: 0,
      hardBraking: 1,
      rapidAcceleration: 3
    }
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
    flags: {
      speedAlerts: 0,
      hardBraking: 0,
      rapidAcceleration: 0
    }
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
    flags: {
      speedAlerts: 0,
      hardBraking: 0,
      rapidAcceleration: 2
    }
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
    flags: {
      speedAlerts: 0,
      hardBraking: 2,
      rapidAcceleration: 1
    }
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
    flags: {
      speedAlerts: 0,
      hardBraking: 0,
      rapidAcceleration: 0
    }
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
    flags: {
      speedAlerts: 0,
      hardBraking: 3,
      rapidAcceleration: 4
    }
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
    flags: {
      speedAlerts: 0,
      hardBraking: 1,
      rapidAcceleration: 0
    }
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
    flags: {
      speedAlerts: 0,
      hardBraking: 2,
      rapidAcceleration: 5
    }
  },
];

interface MapWidgetProps {
  vehicles?: VehicleLocation[];
  onVehicleSelect?: (vehicle: VehicleLocation) => void;
}

export const MapWidget = ({ vehicles = defaultVehicles, onVehicleSelect }: MapWidgetProps) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const markersRef = useRef<Map<string, mapboxgl.Marker>>(new Map());

  useEffect(() => {
    if (!mapContainer.current) return;

    // Hardcoded Mapbox token
    const token = "pk.eyJ1IjoiaWJ0ZXNhbW5hZWVtIiwiYSI6ImNtaHY3amJ6aDA3dmUyaXExbG42OTdlbW0ifQ.mCJtklraw0s8tPOaXqkDYg";

    mapboxgl.accessToken = token;

    try {
      map.current = new mapboxgl.Map({
        container: mapContainer.current,
        style: "mapbox://styles/mapbox/light-v11",
        center: [-98.5, 39.8],
        zoom: 3.5,
      });

      // Add navigation controls
      map.current.addControl(new mapboxgl.NavigationControl(), "top-right");

      // Add markers for each vehicle
      vehicles.forEach((vehicle) => {
        const el = document.createElement("div");
        el.className = "marker";
        el.style.width = "24px";
        el.style.height = "24px";
        el.style.borderRadius = "50%";
        el.style.backgroundColor = vehicle.status === "moving" ? "hsl(var(--success))" : "hsl(var(--primary))";
        el.style.border = "2px solid white";
        el.style.boxShadow = "0 2px 4px rgba(0,0,0,0.2)";

        const statusColor = vehicle.status === "moving" ? "#10b981" : "#3b82f6";
        const fuelColor = vehicle.fuel < 30 ? "#ef4444" : vehicle.fuel < 60 ? "#f59e0b" : "#10b981";
        const hasAlerts = vehicle.flags.speedAlerts > 0 || vehicle.flags.hardBraking > 0 || vehicle.flags.rapidAcceleration > 0;

        const popup = new mapboxgl.Popup({ 
          offset: 30,
          className: "vehicle-popup",
          maxWidth: "360px",
          closeButton: true,
          closeOnClick: false
        }).setHTML(
          `<div style="padding: 16px; font-family: system-ui, -apple-system, sans-serif;">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
              <div>
                <p style="font-weight: 600; font-size: 15px; margin-bottom: 4px; color: #0f172a;">${vehicle.name}</p>
                <p style="font-size: 13px; color: #64748b; margin-bottom: 2px;">Guest: ${vehicle.guest}</p>
                <p style="font-size: 13px; color: #64748b;">📍 ${vehicle.location}</p>
              </div>
              <span style="background: ${statusColor}; color: white; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 500; text-transform: capitalize;">
                ${vehicle.status}
              </span>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 12px; padding-top: 12px; border-top: 1px solid #e2e8f0;">
              <div>
                <p style="font-size: 11px; color: #64748b; margin-bottom: 4px;">FUEL LEVEL</p>
                <div style="display: flex; align-items: center; gap: 6px;">
                  <span style="font-size: 13px;">⛽</span>
                  <span style="font-weight: 600; font-size: 14px; color: ${fuelColor};">${vehicle.fuel}%</span>
                </div>
              </div>
              
              ${vehicle.status === "moving" ? `
                <div>
                  <p style="font-size: 11px; color: #64748b; margin-bottom: 4px;">CURRENT SPEED</p>
                  <div style="display: flex; align-items: center; gap: 6px;">
                    <span style="font-size: 13px;">🚗</span>
                    <span style="font-weight: 600; font-size: 14px; color: #0f172a;">${vehicle.speed} mph</span>
                  </div>
                </div>
              ` : ''}
            </div>
            
            <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #e2e8f0;">
              <p style="font-size: 11px; color: #64748b; margin-bottom: 6px;">TRIP PROGRESS</p>
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                <span style="font-size: 13px; color: #0f172a;">${vehicle.totalKm} / ${vehicle.allowedKm} km</span>
                <span style="font-size: 12px; color: #64748b;">${Math.round((vehicle.totalKm / vehicle.allowedKm) * 100)}%</span>
              </div>
              <div style="background: #e2e8f0; height: 6px; border-radius: 3px; overflow: hidden;">
                <div style="background: ${vehicle.totalKm > vehicle.allowedKm ? '#ef4444' : '#3b82f6'}; height: 100%; width: ${Math.min((vehicle.totalKm / vehicle.allowedKm) * 100, 100)}%; transition: width 0.3s;"></div>
              </div>
            </div>
            
            ${hasAlerts ? `
              <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #e2e8f0;">
                <p style="font-size: 11px; color: #64748b; margin-bottom: 8px;">VEHICLE ALERTS</p>
                <div style="display: flex; flex-wrap: wrap; gap: 6px;">
                  ${vehicle.flags.speedAlerts > 0 ? `
                    <span style="background: #fef3c7; color: #92400e; padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: 500;">
                      🚨 ${vehicle.flags.speedAlerts} Speed Alert${vehicle.flags.speedAlerts > 1 ? 's' : ''}
                    </span>
                  ` : ''}
                  ${vehicle.flags.hardBraking > 0 ? `
                    <span style="background: #fecaca; color: #991b1b; padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: 500;">
                      🛑 ${vehicle.flags.hardBraking} Hard Brake${vehicle.flags.hardBraking > 1 ? 's' : ''}
                    </span>
                  ` : ''}
                  ${vehicle.flags.rapidAcceleration > 0 ? `
                    <span style="background: #fed7aa; color: #9a3412; padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: 500;">
                      ⚡ ${vehicle.flags.rapidAcceleration} Rapid Accel.
                    </span>
                  ` : ''}
                </div>
              </div>
            ` : ''}
          </div>`
        );

        const marker = new mapboxgl.Marker(el)
          .setLngLat(vehicle.coordinates)
          .setPopup(popup)
          .addTo(map.current!);

        // Store marker reference
        markersRef.current.set(vehicle.id, marker);

        // Open bottom sheet on marker click
        el.addEventListener("click", () => {
          onVehicleSelect?.(vehicle);
        });

        // Center map on marker when popup opens - ensure full popup visibility
        popup.on("open", () => {
          if (map.current) {
            // Get map container dimensions
            const mapContainer = map.current.getContainer();
            const mapHeight = mapContainer.offsetHeight;
            const mapWidth = mapContainer.offsetWidth;
            
            // Calculate offset to show popup above the marker with proper spacing
            const popupHeight = 320; // Approximate popup height
            const verticalOffset = -(popupHeight / 2) - 60; // Center popup vertically with extra margin
            
            map.current.easeTo({
              center: vehicle.coordinates,
              zoom: Math.max(map.current.getZoom(), 10),
              padding: { 
                top: Math.min(100, mapHeight * 0.2), 
                bottom: Math.min(100, mapHeight * 0.2), 
                left: Math.min(80, mapWidth * 0.1), 
                right: Math.min(80, mapWidth * 0.1) 
              },
              offset: [0, verticalOffset],
              duration: 500,
            });
          }
        });

        // Zoom back out to show all markers when popup closes
        popup.on("close", () => {
          if (map.current) {
            const bounds = new mapboxgl.LngLatBounds();
            
            // Add all vehicle coordinates to bounds
            vehicles.forEach((v) => {
              bounds.extend(v.coordinates);
            });
            
            // Fit map to show all markers
            map.current.fitBounds(bounds, {
              padding: { top: 50, bottom: 50, left: 50, right: 50 },
              duration: 800,
              maxZoom: 6
            });
          }
        });
      });
    } catch (error) {
      console.error("Error initializing map:", error);
    }

    return () => {
      markersRef.current.forEach(marker => marker.remove());
      markersRef.current.clear();
      map.current?.remove();
    };
  }, [vehicles, onVehicleSelect]);

  // Update marker positions when vehicles change
  useEffect(() => {
    if (!map.current) return;

    vehicles.forEach((vehicle) => {
      const marker = markersRef.current.get(vehicle.id);
      if (marker) {
        marker.setLngLat(vehicle.coordinates);
      }
    });
  }, [vehicles]);


  return (
    <div ref={mapContainer} className="w-full h-full" />
  );
};
