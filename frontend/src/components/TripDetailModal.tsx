import { Dialog, DialogContent } from "@/components/ui/dialog";
import { useEffect, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight, X } from "lucide-react";
import { Card } from "@/components/ui/card";

interface TripDay {
  date: string;
  polyline: [number, number][];
  topSpeed: number;
  avgSpeed: number;
  distance: number;
  flags: {
    hardBraking: number;
    rapidAcceleration: number;
    speedAlerts: number;
  };
}

interface Trip {
  id: string;
  vehicle: string;
  guest: string;
  startDate: string;
  endDate: string;
  startLocation: string;
  endLocation: string;
  distance: number;
  earnings: number;
  status: string;
  days: TripDay[];
}

interface TripDetailModalProps {
  trip: Trip | null;
  open: boolean;
  onClose: () => void;
}

export const TripDetailModal = ({ trip, open, onClose }: TripDetailModalProps) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const [currentDayIndex, setCurrentDayIndex] = useState(0);

  useEffect(() => {
    if (!open || !trip || !mapContainer.current) {
      console.log("Modal not ready:", { open, hasTrip: !!trip, hasContainer: !!mapContainer.current });
      return;
    }

    console.log("Initializing map with trip:", trip.vehicle);
    
    const token = "pk.eyJ1IjoiaWJ0ZXNhbW5hZWVtIiwiYSI6ImNtaHY3amJ6aDA3dmUyaXExbG42OTdlbW0ifQ.mCJtklraw0s8tPOaXqkDYg";
    mapboxgl.accessToken = token;

    // Add a small delay to ensure the dialog is fully rendered
    const timeoutId = setTimeout(() => {
      if (!mapContainer.current) return;

      try {
        map.current = new mapboxgl.Map({
          container: mapContainer.current,
          style: "mapbox://styles/mapbox/light-v11",
          center: trip.days[0].polyline[0],
          zoom: 10,
        });

        map.current.addControl(new mapboxgl.NavigationControl(), "top-right");
        
        console.log("Map initialized successfully");
      } catch (error) {
        console.error("Error initializing map:", error);
      }
    }, 100);

    return () => {
      clearTimeout(timeoutId);
      map.current?.remove();
      map.current = null;
    };
  }, [open, trip]);

  // Update map when day changes
  useEffect(() => {
    if (!map.current || !trip || !trip.days[currentDayIndex]) return;

    const currentDay = trip.days[currentDayIndex];

    // Remove existing layers and sources
    if (map.current.getLayer("route")) {
      map.current.removeLayer("route");
    }
    if (map.current.getSource("route")) {
      map.current.removeSource("route");
    }

    // Add new route
    map.current.addSource("route", {
      type: "geojson",
      data: {
        type: "Feature",
        properties: {},
        geometry: {
          type: "LineString",
          coordinates: currentDay.polyline,
        },
      },
    });

    map.current.addLayer({
      id: "route",
      type: "line",
      source: "route",
      layout: {
        "line-join": "round",
        "line-cap": "round",
      },
      paint: {
        "line-color": "hsl(var(--primary))",
        "line-width": 4,
      },
    });

    // Add start marker
    new mapboxgl.Marker({ color: "#10b981" })
      .setLngLat(currentDay.polyline[0])
      .setPopup(new mapboxgl.Popup().setHTML("<div style='padding: 8px;'><strong>Start</strong></div>"))
      .addTo(map.current);

    // Add end marker
    new mapboxgl.Marker({ color: "#ef4444" })
      .setLngLat(currentDay.polyline[currentDay.polyline.length - 1])
      .setPopup(new mapboxgl.Popup().setHTML("<div style='padding: 8px;'><strong>End</strong></div>"))
      .addTo(map.current);

    // Fit bounds to show entire route
    const bounds = new mapboxgl.LngLatBounds();
    currentDay.polyline.forEach((coord) => bounds.extend(coord as [number, number]));
    map.current.fitBounds(bounds, { padding: 80 });
  }, [currentDayIndex, trip]);

  if (!trip) return null;

  const currentDay = trip.days[currentDayIndex];

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-[95vw] w-[95vw] h-[95vh] p-0 bg-background">
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-border">
            <div>
              <h2 className="text-2xl font-bold text-foreground">{trip.vehicle}</h2>
              <p className="text-sm text-muted-foreground">
                {trip.guest} • {trip.startDate} - {trip.endDate}
              </p>
            </div>
            <Button variant="ghost" size="icon" onClick={onClose}>
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* Content */}
          <div className="flex-1 flex overflow-hidden">
            {/* Map */}
            <div className="flex-1 relative">
              <div ref={mapContainer} className="w-full h-full" />
              
              {/* Day navigation */}
              {trip.days.length > 1 && (
                <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex items-center gap-2 bg-background/95 backdrop-blur-sm p-2 rounded-lg shadow-lg border border-border">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setCurrentDayIndex(Math.max(0, currentDayIndex - 1))}
                    disabled={currentDayIndex === 0}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <div className="px-4 text-sm font-medium text-foreground">
                    Day {currentDayIndex + 1} of {trip.days.length}
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setCurrentDayIndex(Math.min(trip.days.length - 1, currentDayIndex + 1))}
                    disabled={currentDayIndex === trip.days.length - 1}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              )}
            </div>

            {/* Trip Info Sidebar */}
            <div className="w-80 bg-muted/30 p-6 overflow-y-auto border-l border-border">
              <div className="space-y-6">
                <Card className="p-4">
                  <h3 className="font-semibold text-foreground mb-3">{currentDay.date}</h3>
                  <div className="space-y-3">
                    <div>
                      <p className="text-xs text-muted-foreground">TOP SPEED</p>
                      <p className="text-xl font-bold text-foreground">{currentDay.topSpeed} mph</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">AVG SPEED</p>
                      <p className="text-xl font-bold text-foreground">{currentDay.avgSpeed} mph</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">DISTANCE</p>
                      <p className="text-xl font-bold text-foreground">{currentDay.distance} mi</p>
                    </div>
                  </div>
                </Card>

                {/* Flags */}
                {(currentDay.flags.hardBraking > 0 || 
                  currentDay.flags.rapidAcceleration > 0 || 
                  currentDay.flags.speedAlerts > 0) && (
                  <Card className="p-4">
                    <h3 className="font-semibold text-foreground mb-3">Driving Alerts</h3>
                    <div className="space-y-2">
                      {currentDay.flags.hardBraking > 0 && (
                        <div className="flex items-center justify-between p-2 bg-destructive/10 rounded-lg">
                          <span className="text-sm text-foreground">🛑 Hard Braking</span>
                          <span className="text-sm font-semibold text-foreground">{currentDay.flags.hardBraking}</span>
                        </div>
                      )}
                      {currentDay.flags.rapidAcceleration > 0 && (
                        <div className="flex items-center justify-between p-2 bg-warning/10 rounded-lg">
                          <span className="text-sm text-foreground">⚡ Rapid Acceleration</span>
                          <span className="text-sm font-semibold text-foreground">{currentDay.flags.rapidAcceleration}</span>
                        </div>
                      )}
                      {currentDay.flags.speedAlerts > 0 && (
                        <div className="flex items-center justify-between p-2 bg-warning/10 rounded-lg">
                          <span className="text-sm text-foreground">🚨 Speed Alerts</span>
                          <span className="text-sm font-semibold text-foreground">{currentDay.flags.speedAlerts}</span>
                        </div>
                      )}
                    </div>
                  </Card>
                )}

                {/* Trip Summary */}
                <Card className="p-4">
                  <h3 className="font-semibold text-foreground mb-3">Trip Summary</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">From</span>
                      <span className="text-foreground font-medium">{trip.startLocation}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">To</span>
                      <span className="text-foreground font-medium">{trip.endLocation}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Total Distance</span>
                      <span className="text-foreground font-medium">{trip.distance} mi</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Earnings</span>
                      <span className="text-foreground font-medium">${trip.earnings}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Status</span>
                      <span className="px-2 py-1 rounded-full bg-success/10 text-success text-xs font-medium">
                        {trip.status}
                      </span>
                    </div>
                  </div>
                </Card>
              </div>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
