import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Car,
  Calendar,
  MapPin,
  DollarSign,
  User,
  Route,
  Search,
  AlertTriangle,
  Shield,
  ExternalLink,
  Loader2,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { useState, useEffect, useRef } from "react";
import { tripsService, Trip } from "@/services/trips-service";
import { vehiclesService, Vehicle } from "@/services/vehicles-service";
import { bouncieService, BouncieTripMatch } from "@/services/bouncie-service";
import { dashboardService } from "@/services/dashboard-service";
import { format, parseISO } from "date-fns";
import { useRegionalSettings } from "@/contexts/RegionalSettingsContext";
import { formatDistance, formatCurrency, formatCurrencyDecimal, formatTimeString, formatTime } from "@/lib/regional-utils";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

const TripHistory = () => {
  const { distanceUnit, currency, timeFormat } = useRegionalSettings();
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [sortBy, setSortBy] = useState("newest");
  const [vehicleFilter, setVehicleFilter] = useState<string>("all");
  // Default to "all" to show all trips, user can filter by year if needed
  const [yearFilter, setYearFilter] = useState<number | "all">("all");
  const [selectedTrip, setSelectedTrip] = useState<Trip | null>(null);
  const [trips, setTrips] = useState<Trip[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalTrips, setTotalTrips] = useState(0);
  const [limit] = useState(50);
  const [offset, setOffset] = useState(0);
  const [vehiclesMap, setVehiclesMap] = useState<Map<number, Vehicle>>(new Map());
  const [allVehicles, setAllVehicles] = useState<Vehicle[]>([]);
  const [tripMatch, setTripMatch] = useState<BouncieTripMatch | null>(null);
  const [isLoadingMatch, setIsLoadingMatch] = useState(false);
  const [individualTrips, setIndividualTrips] = useState<any[]>([]);
  const [currentTripIndex, setCurrentTripIndex] = useState(0);
  const [mapError, setMapError] = useState<string | null>(null);
  const [totalEarningsFromAPI, setTotalEarningsFromAPI] = useState<number>(0);
  const [isLoadingEarnings, setIsLoadingEarnings] = useState(false);
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const markersRef = useRef<mapboxgl.Marker[]>([]);
  const layersRef = useRef<string[]>([]);
  const touchStartX = useRef<number | null>(null);
  const touchStartY = useRef<number | null>(null);
  const touchEndX = useRef<number | null>(null);
  const touchEndY = useRef<number | null>(null);
  const isUpdatingMap = useRef<boolean>(false);

  // Fetch trips and vehicles from API
  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const [tripsResponse, vehiclesResponse] = await Promise.all([
          tripsService.getTrips({
            status: statusFilter !== "all" ? statusFilter.toUpperCase() : undefined,
            // Removed trip_type filter to show all trips from database
            limit,
            offset: 0, // Reset to 0 when filters change
          }),
          vehiclesService.getVehicles({ limit: 1000 }), // Get all vehicles
        ]);

        console.log("TripHistory: Loaded trips response:", {
          tripsCount: tripsResponse?.trips?.length || 0,
          total: tripsResponse?.total || 0,
          trips: tripsResponse?.trips?.slice(0, 3) // First 3 trips for debugging
        });

        setTrips(tripsResponse?.trips || []);
        setTotalTrips(tripsResponse?.total || 0);
        setOffset(0);

        // Create a map of vehicle_id -> Vehicle for quick lookup
        const vehiclesMap = new Map<number, Vehicle>();
        const vehiclesList = vehiclesResponse?.vehicles || [];
        vehiclesList.forEach(vehicle => {
          vehiclesMap.set(vehicle.id, vehicle);
        });
        setVehiclesMap(vehiclesMap);
        setAllVehicles(vehiclesList);
      } catch (err) {
        console.error("Error loading data:", err);
        const errorMessage = err instanceof Error ? err.message : "Failed to load trips. Please try again.";
        setError(errorMessage);
        setTrips([]);
        setTotalTrips(0);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [statusFilter, limit]);

  // Fetch earnings data for selected year
  useEffect(() => {
    const loadEarnings = async () => {
      setIsLoadingEarnings(true);
      try {
        const earningsResponse = await dashboardService.getEarnings(yearFilter === "all" ? undefined : yearFilter);
        const breakdown = earningsResponse.breakdown || [];
        
        // Calculate total earnings: Trip earnings + Incentives (same as dashboard)
        const includedTypes = ['Trip earnings', 'Incentives'];
        const totalRevenue = breakdown.reduce((sum, item) => {
          const itemType = item.type || '';
          const itemTypeLower = itemType.toLowerCase();
          
          // Only include Trip earnings and Incentives (case-insensitive)
          const isIncluded = includedTypes.some(included => included.toLowerCase() === itemTypeLower);
          if (!isIncluded) {
            return sum;
          }
          
          // Get the numeric value
          const amount = item.amount_numeric !== undefined && item.amount_numeric !== null
            ? item.amount_numeric
            : (item.amount ? parseFloat(item.amount.replace(/[^0-9.-]+/g, '')) || 0 : 0);
          
          return sum + amount;
        }, 0);
        
        setTotalEarningsFromAPI(totalRevenue);
      } catch (err) {
        console.error("Error loading earnings:", err);
        setTotalEarningsFromAPI(0);
      } finally {
        setIsLoadingEarnings(false);
      }
    };

    loadEarnings();
  }, [yearFilter]);

  // Filter and sort trips
  const filteredTrips = trips
    .filter(trip => {
      const matchesSearch = 
        trip.customer_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        trip.trip_id.toLowerCase().includes(searchQuery.toLowerCase());
      
      const matchesVehicle = vehicleFilter === "all" || 
        (trip.vehicle_id && vehicleFilter === trip.vehicle_id.toString());
      
      // Filter by year based on start_date or end_date (more flexible)
      const matchesYear = (() => {
        // If "all" is selected, show all trips
        if (yearFilter === "all") return true;
        
        // If no date fields, include the trip
        if (!trip.start_date && !trip.end_date) return true;
        
        // Try to parse start_date first
        let tripYear: number | null = null;
        if (trip.start_date) {
          try {
            const tripDate = parseISO(trip.start_date);
            if (!isNaN(tripDate.getTime())) {
              tripYear = tripDate.getFullYear();
            } else {
              // Try parsing as regular date string
              const parsed = new Date(trip.start_date);
              if (!isNaN(parsed.getTime())) {
                tripYear = parsed.getFullYear();
              }
            }
          } catch {
            // Parsing failed, try end_date
          }
        }
        
        // If start_date didn't work, try end_date
        if (tripYear === null && trip.end_date) {
          try {
            const tripDate = parseISO(trip.end_date);
            if (!isNaN(tripDate.getTime())) {
              tripYear = tripDate.getFullYear();
            } else {
              const parsed = new Date(trip.end_date);
              if (!isNaN(parsed.getTime())) {
                tripYear = parsed.getFullYear();
              }
            }
          } catch {
            // Both parsing failed
          }
        }
        
        // If we couldn't determine the year, include the trip
        if (tripYear === null) return true;
        
        // Check if year matches
        return tripYear === yearFilter;
      })();
      
      return matchesSearch && matchesVehicle && matchesYear;
    })
    .sort((a, b) => {
      if (sortBy === "earnings") {
        return (b.total_earnings || 0) - (a.total_earnings || 0);
      }
      if (sortBy === "earnings-lowest") {
        return (a.total_earnings || 0) - (b.total_earnings || 0);
      }
      if (sortBy === "distance") {
        return (b.kilometers_driven || 0) - (a.kilometers_driven || 0);
      }
      if (sortBy === "distance-lowest") {
        return (a.kilometers_driven || 0) - (b.kilometers_driven || 0);
      }
      // Sort by date: newest to oldest or oldest to newest
      const dateA = a.start_date ? new Date(a.start_date).getTime() : (a.created_at ? new Date(a.created_at).getTime() : 0);
      const dateB = b.start_date ? new Date(b.start_date).getTime() : (b.created_at ? new Date(b.created_at).getTime() : 0);
      if (sortBy === "oldest") {
        return dateA - dateB; // Oldest first
      }
      // Default: newest to oldest
      return dateB - dateA;
    });

  const loadMoreTrips = async () => {
    try {
      const newOffset = offset + limit;
      const response = await tripsService.getTrips({
        status: statusFilter !== "all" ? statusFilter.toUpperCase() : undefined,
        // Removed trip_type filter to show all trips from database
        limit,
        offset: newOffset,
      });
      setTrips(prev => [...prev, ...response.trips]);
      setOffset(newOffset);
    } catch (err) {
      console.error("Error loading more trips:", err);
      setError("Failed to load more trips. Please try again.");
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return "N/A";
    try {
      const date = parseISO(dateString);
      return format(date, "EEE, MMM d");
    } catch {
      return dateString;
    }
  };

  const formatTime = (timeString?: string) => {
    if (!timeString) return "";
    return formatTimeString(timeString, timeFormat);
  };

  // Helper function to normalize coordinates to [lat, lng] format
  // Validates and converts coordinates if needed
  const normalizeCoordinates = (coords: any[]): number[][] => {
    if (!Array.isArray(coords) || coords.length === 0) {
      return [];
    }

    return coords
      .map((coord: any) => {
        if (!Array.isArray(coord) || coord.length < 2) {
          return null;
        }

        const [first, second] = coord;
        
        // Validate that values are numbers
        if (typeof first !== 'number' || typeof second !== 'number') {
          return null;
        }

        // Check if coordinates are already in [lat, lng] format
        // Latitude must be between -90 and 90
        if (first >= -90 && first <= 90 && Math.abs(second) <= 180) {
          // Already in [lat, lng] format
          return [first, second];
        }
        
        // Check if coordinates are in [lng, lat] format
        // Longitude must be between -180 and 180
        if (second >= -90 && second <= 90 && Math.abs(first) <= 180) {
          // Convert from [lng, lat] to [lat, lng]
          return [second, first];
        }

        // If we can't determine, assume [lat, lng] and return as-is
        // (This handles edge cases where coordinates might be slightly outside normal ranges)
        return [first, second];
      })
      .filter((coord: any) => coord !== null) as number[][];
  };


  const handleCloseModal = () => {
    setSelectedTrip(null);
    setTripMatch(null);
    setIndividualTrips([]);
    setCurrentTripIndex(0);
    setMapError(null);
    // Clean up map completely
    if (map.current) {
      try {
        markersRef.current.forEach(marker => marker.remove());
        markersRef.current = [];
        layersRef.current.forEach(layerId => {
          if (map.current?.getLayer(layerId)) {
            map.current.removeLayer(layerId);
          }
          if (map.current?.getSource(layerId)) {
            map.current.removeSource(layerId);
          }
        });
        layersRef.current = [];
        // Remove the map instance
        map.current.remove();
        map.current = null;
      } catch (error) {
        console.warn("Error cleaning up map:", error);
        map.current = null;
      }
    }
  };

  const handlePreviousTrip = () => {
    if (currentTripIndex > 0) {
      setCurrentTripIndex(currentTripIndex - 1);
    }
  };

  const handleNextTrip = () => {
    if (currentTripIndex < individualTrips.length - 1) {
      setCurrentTripIndex(currentTripIndex + 1);
    }
  };

  // Swipe gesture handlers - only trigger on horizontal swipes
  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartX.current = e.touches[0].clientX;
    touchStartY.current = e.touches[0].clientY;
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    touchEndX.current = e.touches[0].clientX;
    touchEndY.current = e.touches[0].clientY;
  };

  const handleTouchEnd = () => {
    if (!touchStartX.current || !touchEndX.current || !touchStartY.current || !touchEndY.current) return;
    
    const deltaX = touchStartX.current - touchEndX.current;
    const deltaY = Math.abs(touchStartY.current - (touchEndY.current || touchStartY.current));
    const minSwipeDistance = 50; // Minimum distance for a swipe
    
    // Only trigger if horizontal swipe is dominant (more horizontal than vertical)
    if (Math.abs(deltaX) > minSwipeDistance && Math.abs(deltaX) > deltaY) {
      if (deltaX > 0) {
        // Swipe left - next trip
        handleNextTrip();
      } else {
        // Swipe right - previous trip
        handlePreviousTrip();
      }
    }
    
    touchStartX.current = null;
    touchStartY.current = null;
    touchEndX.current = null;
    touchEndY.current = null;
  };

  // Fetch Bouncie trip match when trip is selected
  useEffect(() => {
    const fetchTripMatch = async () => {
      if (!selectedTrip) {
        setTripMatch(null);
        return;
      }

      setIsLoadingMatch(true);
      try {
        const response = await bouncieService.getTripMatches(
          selectedTrip.trip_id,
          true, // include_polylines
          1,
          0
        );
        
        if (response.matches && response.matches.length > 0) {
          // Get full detail with coordinates
          const matchDetail = await bouncieService.getTripMatchDetail(
            response.matches[0].id,
            true // include_full_data
          );
          setTripMatch(matchDetail);
          
          // Extract individual trips from match_data
          if (matchDetail.match_data && matchDetail.match_data.all_trips) {
            const trips = matchDetail.match_data.all_trips;
            console.log("Individual trips from match_data:", trips);
            console.log("First trip sample:", trips[0]);
            
            // Process trips to ensure coordinates are properly extracted
            // Backend stores coordinates as [lat, lng] (see helpers.py line 37)
            // We need to keep them in [lat, lng] format here, then convert to [lng, lat] for Mapbox
            const processedTrips = trips.map((trip: any, index: number) => {
              let coords = trip.coordinates;
              
              console.log(`Trip ${index} raw data:`, {
                hasCoordinates: !!trip.coordinates,
                coordinatesLength: trip.coordinates?.length,
                hasGps: !!trip.gps,
                gpsType: trip.gps?.type,
                gpsCoordsLength: trip.gps?.coordinates?.length,
                firstCoord: trip.coordinates?.[0] || trip.gps?.coordinates?.[0]
              });
              
              // If coordinates don't exist or empty, try to extract from GPS data
              if (!coords || coords.length === 0) {
                if (trip.gps) {
                  const gps = trip.gps;
                  if (gps.type === 'LineString' && gps.coordinates && Array.isArray(gps.coordinates)) {
                    // GPS coordinates from Bouncie API are in GeoJSON format [lng, lat]
                    // Backend should have converted them, but if we're getting raw GPS data,
                    // we need to convert from [lng, lat] to [lat, lng] to match backend format
                    coords = gps.coordinates
                      .map((c: number[]) => {
                        if (!Array.isArray(c) || c.length < 2) return null;
                        // Assume raw GPS data is [lng, lat] (GeoJSON standard)
                        // Convert to [lat, lng] to match backend storage format
                        return [c[1], c[0]];
                      })
                      .filter((c: any) => c !== null);
                      
                      console.log(`Trip ${index} extracted ${coords.length} coordinates from GPS (converted from [lng,lat] to [lat,lng])`);
                    }
                  }
                }
              
              // Normalize coordinates to ensure they're in [lat, lng] format
              coords = normalizeCoordinates(coords);
              
              console.log(`Trip ${index} final coordinates:`, coords.length > 0 ? `${coords.length} points, first: [${coords[0][0]}, ${coords[0][1]}]` : 'none');
              
              return {
                ...trip,
                coordinates: coords, // Store as [lat, lng] - will convert to [lng, lat] for Mapbox
                coordinate_count: coords.length,
              };
            });
            
            console.log("Processed trips:", processedTrips);
            setIndividualTrips(processedTrips);
            setCurrentTripIndex(0);
          } else {
            // Fallback: if no individual trips, create one from aggregated coordinates
            if (matchDetail.coordinates && matchDetail.coordinates.length > 0) {
              const normalizedCoords = normalizeCoordinates(matchDetail.coordinates);
              setIndividualTrips([{
                coordinates: normalizedCoords,
                polyline: matchDetail.polyline,
                startTime: matchDetail.bouncie_earliest_start,
                endTime: matchDetail.bouncie_latest_end,
                distance: matchDetail.aggregated_distance_km,
                coordinate_count: normalizedCoords.length,
              }]);
              setCurrentTripIndex(0);
            } else {
              setIndividualTrips([]);
            }
          }
        } else {
          setTripMatch(null);
          setIndividualTrips([]);
        }
      } catch (err) {
        console.error("Error fetching trip match:", err);
        setTripMatch(null);
      } finally {
        setIsLoadingMatch(false);
      }
    };

    fetchTripMatch();
  }, [selectedTrip]);

  // Initialize map when trip match is loaded
  useEffect(() => {
    // Wait for map container to be available and individual trips to be loaded
    if (!selectedTrip || !mapContainer.current) {
      return;
    }

    // Check if we have individual trips or need to use aggregated coordinates
    if (individualTrips.length === 0) {
      // If no individual trips but we have tripMatch with coordinates, wait for it to load
      if (tripMatch && tripMatch.coordinates && tripMatch.coordinates.length > 0) {
        // This case is handled by the fallback in the fetchTripMatch useEffect
        // Just return here and let that handle it
        return;
      }
      return;
    }

    const currentTrip = individualTrips[currentTripIndex];
    
    // Validate trip has coordinates
    if (!currentTrip || !currentTrip.coordinates || !Array.isArray(currentTrip.coordinates) || currentTrip.coordinates.length === 0) {
      console.warn("No coordinates available for current trip, skipping map update", {
        hasTrip: !!currentTrip,
        hasCoordinates: !!currentTrip?.coordinates,
        coordinatesLength: currentTrip?.coordinates?.length,
        currentTripIndex,
        individualTripsLength: individualTrips.length
      });
      return;
    }

    const token = "pk.eyJ1IjoiaWJ0ZXNhbW5hZWVtIiwiYSI6ImNtaHY3amJ6aDA3dmUyaXExbG42OTdlbW0ifQ.mCJtklraw0s8tPOaXqkDYg";
    mapboxgl.accessToken = token;

    // Clean up existing map layers and markers
    const cleanup = () => {
      if (!map.current) return;
      
      // Remove all markers
      markersRef.current.forEach(marker => {
        try {
          marker.remove();
        } catch (e) {
          console.warn("Error removing marker:", e);
        }
      });
      markersRef.current = [];
      
      // Remove all tracked layers and sources
      layersRef.current.forEach(layerId => {
        try {
          if (map.current?.getLayer(layerId)) {
            map.current.removeLayer(layerId);
          }
          if (map.current?.getSource(layerId)) {
            map.current.removeSource(layerId);
          }
        } catch (e) {
          console.warn(`Error removing layer/source ${layerId}:`, e);
        }
      });
      
      // Also try to remove any route-* layers that might exist (cleanup any orphaned layers)
      try {
        const style = map.current.getStyle();
        if (style && style.layers) {
          style.layers.forEach((layer: any) => {
            if (layer.id && (layer.id.startsWith('route-') || layer.id.includes('route-'))) {
              try {
                if (map.current?.getLayer(layer.id)) {
                  map.current.removeLayer(layer.id);
                }
              } catch (e) {
                // Layer might already be removed
              }
            }
          });
        }
        
        // Also clean up sources
        if (style && style.sources) {
          Object.keys(style.sources).forEach((sourceId: string) => {
            if (sourceId.startsWith('route-') || sourceId.includes('route-')) {
              try {
                if (map.current?.getSource(sourceId)) {
                  map.current.removeSource(sourceId);
                }
              } catch (e) {
                // Source might already be removed
              }
            }
          });
        }
      } catch (e) {
        console.warn("Error during comprehensive cleanup:", e);
      }
      
      layersRef.current = [];
    };

    // Update map with current trip data - defined first so it can be called from initializeMap
    const updateMap = () => {
      // Prevent concurrent updates
      if (isUpdatingMap.current) {
        console.log("Map update already in progress, skipping...");
        return;
      }
      
      isUpdatingMap.current = true;
      
      try {
        // Get current trip again in case it changed
        const trip = individualTrips[currentTripIndex];
        
        if (!map.current || !trip) {
          console.warn("Cannot update map - map or trip not available", {
            hasMap: !!map.current,
            hasTrip: !!trip,
            currentTripIndex,
            individualTripsLength: individualTrips.length
          });
          isUpdatingMap.current = false;
          return;
        }

        // Validate trip has coordinates
        if (!trip.coordinates || !Array.isArray(trip.coordinates) || trip.coordinates.length === 0) {
          console.warn("No coordinates available for trip, skipping map update", {
            hasCoordinates: !!trip.coordinates,
            coordinatesLength: trip.coordinates?.length,
            currentTripIndex
          });
          isUpdatingMap.current = false;
          return;
        }

        // Clean up ALL existing layers and sources first
        cleanup();

        // Get coordinates - prefer coordinates array, fallback to polyline if needed
        let validCoords: number[][] = [];
        
        if (trip.coordinates && Array.isArray(trip.coordinates) && trip.coordinates.length > 0) {
          // Use coordinates array directly
          validCoords = trip.coordinates
            .map((coord: number[]) => {
              if (!Array.isArray(coord) || coord.length < 2) {
                return null;
              }
              
              const lat = coord[0];
              const lng = coord[1];
              
              // Validate coordinate ranges
              if (typeof lat !== 'number' || typeof lng !== 'number') {
                return null;
              }
              
              // Check if coordinates are valid (lat: -90 to 90, lng: -180 to 180)
              // Backend stores as [lat, lng], convert to [lng, lat] for Mapbox
              if (lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180) {
                return [lng, lat];
              }
              
              // If coordinates seem reversed (lng in lat position), try swapping
              if (lng >= -90 && lng <= 90 && lat >= -180 && lat <= 180) {
                return [lat, lng];
              }
              
              return null;
            })
            .filter((coord: any) => coord !== null && coord[0] !== null && coord[1] !== null && 
                    !isNaN(coord[0]) && !isNaN(coord[1]));
        } else if (trip.polyline && typeof trip.polyline === 'string') {
          // Try to decode polyline if coordinates aren't available
          // Note: Would need @mapbox/polyline package for this
          console.warn("Polyline string available but decoding not implemented. Using coordinates instead.");
        }

        if (validCoords.length === 0) {
          console.warn("No valid coordinates available for route", {
            hasCoordinates: !!trip.coordinates,
            coordinatesLength: trip.coordinates?.length,
            hasPolyline: !!trip.polyline,
            rawFirstCoord: trip.coordinates?.[0],
            rawLastCoord: trip.coordinates?.[trip.coordinates?.length - 1]
          });
          isUpdatingMap.current = false;
          return;
        }

        console.log(`Drawing route with ${validCoords.length} GPS points for trip ${currentTripIndex + 1}`);
        console.log("First few coordinates:", validCoords.slice(0, 3));
        console.log("Last few coordinates:", validCoords.slice(-3));

        const routeId = `route-${currentTripIndex}`;

        try {
          // Ensure map is loaded and style is loaded
          if (!map.current.loaded() || !map.current.isStyleLoaded()) {
            console.warn("Map not ready yet, waiting...", {
              loaded: map.current.loaded(),
              styleLoaded: map.current.isStyleLoaded()
            });
            const onLoad = () => {
              console.log("Map ready, retrying route update");
              isUpdatingMap.current = false; // Reset before retry
              updateMap();
            };
            if (!map.current.loaded()) {
              map.current.once("load", onLoad);
            } else {
              map.current.once("styledata", onLoad);
            }
            isUpdatingMap.current = false; // Reset since we're waiting
            return;
          }

          // Remove any existing layers and sources with this routeId (should already be cleaned, but double-check)
          try {
            if (map.current.getLayer(routeId)) {
              map.current.removeLayer(routeId);
            }
            if (map.current.getLayer(`${routeId}-outline`)) {
              map.current.removeLayer(`${routeId}-outline`);
            }
            if (map.current.getSource(routeId)) {
              map.current.removeSource(routeId);
            }
          } catch (e) {
            console.warn("Error removing existing layers (may not exist):", e);
          }

          // Create GeoJSON feature
          const routeFeature = {
            type: "Feature" as const,
            properties: {},
            geometry: {
              type: "LineString" as const,
              coordinates: validCoords,
            },
          };

          console.log("Adding route source with feature:", {
            type: routeFeature.type,
            coordinatesCount: routeFeature.geometry.coordinates.length,
            firstCoord: routeFeature.geometry.coordinates[0],
            lastCoord: routeFeature.geometry.coordinates[routeFeature.geometry.coordinates.length - 1]
          });

          // Add route source with error handling
          try {
            // Double-check source doesn't exist
            if (map.current.getSource(routeId)) {
              console.log("Source already exists, updating data");
              const existingSource = map.current.getSource(routeId) as mapboxgl.GeoJSONSource;
              existingSource.setData(routeFeature);
            } else {
              map.current.addSource(routeId, {
                type: "geojson",
                data: routeFeature,
              });
              console.log("Route source added successfully");
            }
          } catch (sourceError: any) {
            console.error("Error adding route source:", sourceError);
            // If source already exists, try to update it
            if (sourceError.message?.includes("already exists") || sourceError.message?.includes("duplicate")) {
              try {
                const source = map.current.getSource(routeId) as mapboxgl.GeoJSONSource;
                if (source) {
                  source.setData(routeFeature);
                  console.log("Updated existing route source");
                }
              } catch (updateError) {
                console.error("Error updating source:", updateError);
                // Try removing and re-adding
                try {
                  map.current.removeSource(routeId);
                  map.current.addSource(routeId, {
                    type: "geojson",
                    data: routeFeature,
                  });
                  console.log("Re-added route source after error");
                } catch (retryError) {
                  console.error("Failed to re-add source:", retryError);
                  isUpdatingMap.current = false;
                  return; // Can't proceed without source
                }
              }
            } else {
              console.error("Unexpected error adding source:", sourceError);
              isUpdatingMap.current = false;
              return; // Can't proceed without source
            }
          }

          // Add outline layer first (will appear behind main route)
          try {
            if (map.current.getLayer(`${routeId}-outline`)) {
              map.current.removeLayer(`${routeId}-outline`);
            }
            map.current.addLayer({
              id: `${routeId}-outline`,
              type: "line",
              source: routeId,
              layout: {
                "line-join": "round",
                "line-cap": "round",
              },
              paint: {
                "line-color": "#ffffff",
                "line-width": 6,
                "line-opacity": 0.4,
              },
            });
            layersRef.current.push(`${routeId}-outline`);
            console.log("Outline layer added");
          } catch (layerError: any) {
            console.error("Error adding outline layer:", layerError);
            // Continue anyway - main layer might still work
          }
          
          // Add main route layer (will appear on top of outline)
          try {
            if (map.current.getLayer(routeId)) {
              map.current.removeLayer(routeId);
            }
            map.current.addLayer({
              id: routeId,
              type: "line",
              source: routeId,
              layout: {
                "line-join": "round",
                "line-cap": "round",
              },
              paint: {
                "line-color": "#3b82f6", // Use explicit blue color instead of CSS variable
                "line-width": 4,
                "line-opacity": 1.0,
              },
            });
            layersRef.current.push(routeId);
            console.log("Main route layer added successfully");
          } catch (layerError: any) {
            console.error("Error adding main route layer:", layerError);
            // This is critical - if we can't add the main layer, the route won't show
            if (layerError.message?.includes("already exists") || layerError.message?.includes("duplicate")) {
              // Layer exists, try to update the source data instead
              try {
                const source = map.current.getSource(routeId) as mapboxgl.GeoJSONSource;
                if (source) {
                  source.setData(routeFeature);
                  console.log("Updated source data for existing layer");
                }
              } catch (updateError) {
                console.error("Failed to update existing layer:", updateError);
              }
            }
          }

          console.log("Route layers added successfully");
          
          // Verify layers were added
          const outlineLayerExists = map.current.getLayer(`${routeId}-outline`);
          const mainLayerExists = map.current.getLayer(routeId);
          const sourceExists = map.current.getSource(routeId);
          
          console.log("Layer verification:", {
            outlineLayer: !!outlineLayerExists,
            mainLayer: !!mainLayerExists,
            source: !!sourceExists,
            coordinateCount: validCoords.length
          });
          
          if (!mainLayerExists || !sourceExists) {
            console.error("Critical: Main layer or source was not added properly!");
            isUpdatingMap.current = false;
            return;
          }

          // Add start marker
          const startCoord = trip.coordinates[0];
          if (Array.isArray(startCoord) && startCoord.length >= 2) {
            const startMarker = new mapboxgl.Marker({ color: "#10b981" })
              .setLngLat([startCoord[1], startCoord[0]])
              .setPopup(new mapboxgl.Popup().setHTML("<div style='padding: 8px;'><strong>Start</strong></div>"))
              .addTo(map.current);
            markersRef.current.push(startMarker);
          }

          // Add end marker
          const endCoord = trip.coordinates[trip.coordinates.length - 1];
          if (Array.isArray(endCoord) && endCoord.length >= 2) {
            const endMarker = new mapboxgl.Marker({ color: "#ef4444" })
              .setLngLat([endCoord[1], endCoord[0]])
              .setPopup(new mapboxgl.Popup().setHTML("<div style='padding: 8px;'><strong>End</strong></div>"))
              .addTo(map.current);
            markersRef.current.push(endMarker);
          }

          // Fit bounds to show entire route
          const bounds = new mapboxgl.LngLatBounds();
          trip.coordinates.forEach((coord: number[]) => {
            if (Array.isArray(coord) && coord.length >= 2) {
              bounds.extend([coord[1], coord[0]]);
            }
          });
          
          if (bounds.isEmpty()) {
            console.warn("Bounds are empty, cannot fit bounds");
          } else {
            map.current.fitBounds(bounds, { padding: 80, duration: 500 });
          }
          
          // Force map to refresh/render after a brief delay to ensure layers are visible
          setTimeout(() => {
            if (map.current) {
              try {
                map.current.triggerRepaint();
                // Also try resizing to force a render
                if (mapContainer.current) {
                  const rect = mapContainer.current.getBoundingClientRect();
                  if (rect.width > 0 && rect.height > 0) {
                    map.current.resize();
                  }
                }
              } catch (e) {
                console.warn("Error refreshing map:", e);
              }
            }
          }, 100);
        } catch (error) {
          console.error("Error updating map:", error);
        }
      } catch (error) {
        console.error("Error in updateMap:", error);
      } finally {
        isUpdatingMap.current = false;
      }
    };

    // Initialize map if it doesn't exist
    const initializeMap = () => {
      if (!mapContainer.current) {
        console.warn("Map container not available");
        return;
      }

      if (map.current) {
        // Map exists, check if it's still attached to the container
        const mapContainerElement = map.current.getContainer();
        if (mapContainerElement && mapContainerElement.parentElement) {
          // Map is still attached, just update it with current trip
          console.log("Map exists, updating with current trip");
          updateMap();
          return;
        } else {
          // Map container was removed, clean up and recreate
          console.log("Map container was removed, cleaning up and recreating");
          try {
            map.current.remove();
          } catch (e) {
            console.warn("Error removing old map:", e);
          }
          map.current = null;
        }
      }

      // Create new map
      const firstCoord = currentTrip.coordinates[0];
      const center: [number, number] = Array.isArray(firstCoord) && firstCoord.length >= 2
        ? [firstCoord[1], firstCoord[0]] // Mapbox expects [lng, lat]
        : [-98.5, 39.8]; // Default center

      try {
        map.current = new mapboxgl.Map({
          container: mapContainer.current,
          style: "mapbox://styles/mapbox/light-v11",
          center: center,
          zoom: 10,
          // Add error handling for rate limiting
          maxZoom: 18,
          minZoom: 1,
        });

        map.current.addControl(new mapboxgl.NavigationControl(), "top-right");

        // Handle map errors (including rate limiting)
        map.current.on("error", (e: any) => {
          console.error("Map error:", e);
          const errorMessage = e.error?.message || e.message || "Unknown map error";
          if (errorMessage.includes("rate limit") || errorMessage.includes("quota") || errorMessage.includes("429")) {
            setMapError("Mapbox rate limit exceeded. The map may not load properly. Please check your Mapbox account or try again later.");
            console.error("Mapbox rate limit exceeded. Please check your Mapbox account.");
          } else {
            setMapError(`Map error: ${errorMessage}`);
          }
        });

        // Wait for map to load before adding sources
        map.current.once("load", () => {
          console.log("Map loaded successfully, updating with trip data");
          setMapError(null); // Clear any previous errors
          // Small delay to ensure style is fully loaded
          setTimeout(() => {
            if (map.current && mapContainer.current) {
              updateMap();
            }
          }, 150);
        });

        // Handle style data load
        map.current.once("styledata", () => {
          console.log("Map style loaded");
        });

        // Handle map resize to ensure it renders correctly
        map.current.once("resize", () => {
          console.log("Map resized");
          if (map.current) {
            map.current.resize();
          }
        });

        // Force a resize after a short delay to ensure proper rendering
        // This is especially important when the map is in a dialog that was just opened
        setTimeout(() => {
          if (map.current && mapContainer.current) {
            // Check if container is visible
            const rect = mapContainer.current.getBoundingClientRect();
            if (rect.width > 0 && rect.height > 0) {
              map.current.resize();
            } else {
              // Container not visible yet, try again
              setTimeout(() => {
                if (map.current && mapContainer.current) {
                  map.current.resize();
                }
              }, 300);
            }
          }
        }, 200);
      } catch (error) {
        console.error("Error initializing map:", error);
      }
    };

    // Check if map already exists and is ready - if so, just update it
    if (map.current) {
      const mapContainerElement = map.current.getContainer();
      if (mapContainerElement && mapContainerElement.parentElement) {
        // Map exists and is attached, just update it directly
        console.log("Map exists, updating with current trip index:", currentTripIndex);
        
        // If map is not ready yet, wait for it
        if (!map.current.loaded() || !map.current.isStyleLoaded()) {
          const onLoad = () => {
            console.log("Map ready, updating with trip");
            updateMap();
          };
          if (!map.current.loaded()) {
            map.current.once("load", onLoad);
          } else {
            map.current.once("styledata", onLoad);
          }
        } else {
          // Map is ready, update immediately with a small delay to ensure state is settled
          setTimeout(() => {
            updateMap();
          }, 50);
        }
        
        // Return cleanup function - no timeouts to clean up in this path
        return;
      }
    }

    // Use a more robust initialization with retry logic
    // The map container might not be rendered yet, so we need to wait for it
    let retryCount = 0;
    const maxRetries = 10; // Increased retries
    const retryDelay = 150; // Increased delay
    
    const tryInitialize = () => {
      // Check if container exists and has dimensions (is actually rendered)
      if (!mapContainer.current) {
        if (retryCount < maxRetries) {
          retryCount++;
          setTimeout(tryInitialize, retryDelay);
          return;
        }
        console.warn("Map container not available after retries");
        return;
      }

      // Check if container has dimensions (is visible)
      const container = mapContainer.current;
      const hasDimensions = container.offsetWidth > 0 && container.offsetHeight > 0;
      
      if (!hasDimensions) {
        if (retryCount < maxRetries) {
          retryCount++;
          setTimeout(tryInitialize, retryDelay);
          return;
        }
        console.warn("Map container has no dimensions after retries");
        return;
      }

      // Container is ready, initialize map
      initializeMap();
    };

    // Start initialization with a small delay to ensure DOM is ready
    const timeoutId = setTimeout(tryInitialize, 50);

    return () => {
      clearTimeout(timeoutId);
      // Clean up map when component unmounts or dependencies change
      if (map.current) {
        cleanup();
        // Don't remove the map instance, just clean up layers
        // The map instance will be reused if it exists
      }
    };
  }, [selectedTrip, individualTrips, currentTripIndex, tripMatch]);

  // Resize map when dialog opens (to handle case where map was initialized before dialog was visible)
  useEffect(() => {
    if (selectedTrip && map.current && mapContainer.current) {
      // Small delay to ensure dialog is fully rendered
      const timeoutId = setTimeout(() => {
        if (map.current && mapContainer.current) {
          const rect = mapContainer.current.getBoundingClientRect();
          if (rect.width > 0 && rect.height > 0) {
            map.current.resize();
            console.log("Map resized after dialog open");
          }
        }
      }, 300);
      
      return () => clearTimeout(timeoutId);
    }
  }, [selectedTrip]);

  const getStatusBadge = (status: string) => {
    const statusUpper = status.toUpperCase();
    if (statusUpper === "COMPLETED") {
      return <Badge className="bg-success/10 text-success border-success/20">Completed</Badge>;
    }
    if (statusUpper.includes("CANCELLED") || statusUpper.includes("CANCELED")) {
      return <Badge variant="destructive">Cancelled</Badge>;
    }
    return <Badge variant="secondary">{status}</Badge>;
  };

  // Use earnings from API (Trip earnings + Incentives) for the selected year
  const totalEarnings = totalEarningsFromAPI;
  const totalDistance = filteredTrips.reduce((sum, t) => sum + (t.kilometers_driven || 0), 0);
  const completedTrips = filteredTrips.filter(t => t.status?.toUpperCase().includes("COMPLETED")).length;

  if (isLoading && trips.length === 0) {
    return (
      <div className="min-h-screen bg-background p-6 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-muted-foreground">Loading trips...</p>
        </div>
      </div>
    );
  }

  if (error && trips.length === 0) {
    return (
      <div className="min-h-screen bg-background p-6 flex items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="p-6">
            <p className="text-destructive mb-4">{error}</p>
            <Button onClick={() => window.location.reload()}>Retry</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-foreground">Trip History</h1>
          <p className="text-muted-foreground">View and analyze your past trips</p>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="rounded-xl">
            <CardContent className="p-4 flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-success/10 flex items-center justify-center">
                <DollarSign className="h-5 w-5 text-success" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Total Earnings</p>
                <p className="text-xl font-bold">
                  {isLoadingEarnings ? "..." : formatCurrency(totalEarnings)}
                </p>
              </div>
            </CardContent>
          </Card>
          <Card className="rounded-xl">
            <CardContent className="p-4 flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                <Route className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Total Distance</p>
                <p className="text-xl font-bold">{formatDistance(totalDistance, distanceUnit)}</p>
              </div>
            </CardContent>
          </Card>
          <Card className="rounded-xl">
            <CardContent className="p-4 flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-chart-2/10 flex items-center justify-center">
                <Calendar className="h-5 w-5 text-chart-2" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Total Trips</p>
                <p className="text-xl font-bold">{filteredTrips.length}</p>
              </div>
            </CardContent>
          </Card>
          <Card className="rounded-xl">
            <CardContent className="p-4 flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-warning/10 flex items-center justify-center">
                <Car className="h-5 w-5 text-warning" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Completed</p>
                <p className="text-xl font-bold">{completedTrips}</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Filters */}
        <Card className="rounded-xl">
          <CardContent className="p-4">
            <div className="flex flex-wrap gap-4">
              <div className="relative flex-1 min-w-[200px]">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search by customer, vehicle, or trip ID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                />
              </div>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                  <SelectItem value="cancelled">Cancelled</SelectItem>
                </SelectContent>
              </Select>
              <Select value={vehicleFilter} onValueChange={setVehicleFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Vehicle Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Vehicles</SelectItem>
                  {allVehicles.map(vehicle => (
                    <SelectItem key={vehicle.id} value={vehicle.id.toString()}>
                      {vehicle.name}{vehicle.year ? ` ${vehicle.year}` : ''}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={yearFilter.toString()} onValueChange={(value) => setYearFilter(value === "all" ? "all" : parseInt(value))}>
                <SelectTrigger className="w-[120px]">
                  <SelectValue placeholder="Year" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Years</SelectItem>
                  <SelectItem value="2024">2024</SelectItem>
                  <SelectItem value="2025">2025</SelectItem>
                  <SelectItem value="2026">2026</SelectItem>
                </SelectContent>
              </Select>
              <Select value={sortBy} onValueChange={setSortBy}>
                <SelectTrigger className="w-[160px]">
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="newest">Newest to Oldest</SelectItem>
                  <SelectItem value="oldest">Oldest to Newest</SelectItem>
                  <SelectItem value="earnings">Highest Earnings</SelectItem>
                  <SelectItem value="earnings-lowest">Lowest Earnings</SelectItem>
                  <SelectItem value="distance">Highest Distance</SelectItem>
                  <SelectItem value="distance-lowest">Lowest Distance</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Trip List */}
        <div className="grid gap-4">
          {filteredTrips.length === 0 ? (
            <Card className="rounded-xl">
              <CardContent className="p-12 text-center">
                <Car className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                <p className="text-muted-foreground">
                  {searchQuery ? "No trips match your search" : "No trips found"}
                </p>
              </CardContent>
            </Card>
          ) : (
            filteredTrips.map((trip) => {
              const hasOverage = (trip.kilometers_driven || 0) > (trip.kilometers_included || 0);
              const overageKm = hasOverage ? (trip.kilometers_driven || 0) - (trip.kilometers_included || 0) : 0;
              const startDate = formatDate(trip.start_date);
              const endDate = formatDate(trip.end_date);
              
              // Calculate trip duration in days
              let tripDays = 0;
              if (trip.start_date && trip.end_date) {
                try {
                  const start = parseISO(trip.start_date);
                  const end = parseISO(trip.end_date);
                  const diffTime = Math.abs(end.getTime() - start.getTime());
                  tripDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
                } catch {
                  tripDays = 0;
                }
              }
              
              // Get vehicle name
              const vehicle = trip.vehicle_id ? vehiclesMap.get(trip.vehicle_id) : null;
              const vehicleName = vehicle 
                ? `${vehicle.name}${vehicle.year ? ` ${vehicle.year}` : ''}`
                : trip.trip_id;

              return (
                <Card
                  key={trip.id}
                  className="rounded-xl hover:shadow-lg transition-all cursor-pointer hover:border-primary/50 group"
                  onClick={() => setSelectedTrip(trip)}
                >
                  <CardContent className="p-5">
                    <div className="flex flex-col md:flex-row md:items-center gap-4">
                      {/* Left: Trip Info */}
                      <div className="flex-1 space-y-3">
                        {/* Vehicle Name */}
                        <div className="flex items-center gap-3 flex-wrap">
                          <h3 className="font-bold text-lg group-hover:text-primary transition-colors">
                            {vehicleName}
                          </h3>
                          {getStatusBadge(trip.status)}
                          {hasOverage && (
                            <Badge variant="outline" className="text-warning border-warning/50 bg-warning/10">
                              +{overageKm} km over
                            </Badge>
                          )}
                        </div>
                        
                        {/* Guest Name */}
                        {trip.customer_name && (
                          <p className="text-sm text-foreground font-medium">
                            {trip.customer_name}
                          </p>
                        )}
                        
                        {/* Dates */}
                        {(trip.start_date || trip.end_date) && (
                          <p className="text-sm text-muted-foreground">
                            {startDate} → {endDate}
                          </p>
                        )}
                        
                        {/* Location */}
                        {trip.address && (
                          <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                            <MapPin className="h-4 w-4" />
                            <span>{trip.address}</span>
                          </div>
                        )}
                      </div>

                      {/* Right: Stats */}
                      <div className="flex items-center gap-6">
                        {trip.kilometers_driven != null && (
                          <div className="text-center">
                            <p className="text-xs text-muted-foreground">Distance</p>
                            <p className="text-lg font-bold">{formatDistance(trip.kilometers_driven, distanceUnit)}</p>
                            {trip.kilometers_included && (
                              <p className="text-xs text-muted-foreground">/ {formatDistance(trip.kilometers_included, distanceUnit)}</p>
                            )}
                          </div>
                        )}
                        {tripDays > 0 && (
                          <div className="text-center">
                            <p className="text-xs text-muted-foreground">Days</p>
                            <p className="text-lg font-bold">{tripDays}</p>
                          </div>
                        )}
                        {trip.total_earnings != null && (
                          <div className="text-center min-w-[80px]">
                            <p className="text-xs text-muted-foreground">Earnings</p>
                            <p className="text-lg font-bold text-success">{formatCurrencyDecimal(trip.total_earnings || 0, currency)}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })
          )}
        </div>

        {/* Load More */}
        {filteredTrips.length > 0 && offset + limit < totalTrips && (
          <div className="flex justify-center">
            <Button 
              variant="outline" 
              onClick={loadMoreTrips}
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Loading...
                </>
              ) : (
                `Load More (${totalTrips - (offset + filteredTrips.length)} remaining)`
              )}
            </Button>
          </div>
        )}

        {/* Trip Detail Modal */}
        <Dialog open={!!selectedTrip} onOpenChange={handleCloseModal}>
          <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Car className="h-5 w-5 text-primary" />
                Trip Details
              </DialogTitle>
            </DialogHeader>

            {selectedTrip && (
              <div className="space-y-5">
                {/* Header */}
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="text-xl font-bold">{selectedTrip.trip_id}</h2>
                    <div className="flex items-center gap-2 mt-1 text-sm text-muted-foreground">
                      {selectedTrip.customer_name && (
                        <>
                          <User className="h-4 w-4" />
                          <span>{selectedTrip.customer_name}</span>
                        </>
                      )}
                      {getStatusBadge(selectedTrip.status)}
                    </div>
                  </div>
                  {selectedTrip.trip_url && (
                    <Button variant="outline" size="sm" asChild>
                      <a href={selectedTrip.trip_url} target="_blank" rel="noopener noreferrer">
                        <ExternalLink className="h-4 w-4 mr-2" />
                        View on Turo
                      </a>
                    </Button>
                  )}
                </div>

                {/* Schedule & Location */}
                <div className="grid grid-cols-2 gap-4">
                  <Card className="rounded-xl">
                    <CardContent className="p-4 space-y-3">
                      <h4 className="font-semibold flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-primary" />
                        Schedule
                      </h4>
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div>
                          <p className="text-xs text-muted-foreground">Start</p>
                          <p className="font-medium">{formatDate(selectedTrip.start_date)}</p>
                          {selectedTrip.start_time && (
                            <p className="text-muted-foreground">{formatTime(selectedTrip.start_time)}</p>
                          )}
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">End</p>
                          <p className="font-medium">{formatDate(selectedTrip.end_date)}</p>
                          {selectedTrip.end_time && (
                            <p className="text-muted-foreground">{formatTime(selectedTrip.end_time)}</p>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                  
                  {selectedTrip.address && (
                    <Card className="rounded-xl">
                      <CardContent className="p-4 space-y-3">
                        <h4 className="font-semibold flex items-center gap-2">
                          <MapPin className="h-4 w-4 text-primary" />
                          {selectedTrip.location_type || "Location"}
                        </h4>
                        <p className="text-sm">{selectedTrip.address}</p>
                      </CardContent>
                    </Card>
                  )}
                </div>

                {/* Distance */}
                {(selectedTrip.kilometers_driven != null || selectedTrip.kilometers_included != null) && (
                  <Card className="rounded-xl">
                    <CardContent className="p-4 space-y-3">
                      <h4 className="font-semibold flex items-center gap-2">
                        <Route className="h-4 w-4 text-primary" />
                        Distance
                      </h4>
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Driven / Included</span>
                          <span className="font-medium">
                            {formatDistance(selectedTrip.kilometers_driven ?? 0, distanceUnit)} / {formatDistance(selectedTrip.kilometers_included ?? 0, distanceUnit)}
                          </span>
                        </div>
                        {selectedTrip.kilometers_included && selectedTrip.kilometers_included > 0 && (
                          <>
                            <Progress 
                              value={Math.min(((selectedTrip.kilometers_driven || 0) / selectedTrip.kilometers_included) * 100, 100)} 
                              className="h-2"
                            />
                            {(selectedTrip.kilometers_driven || 0) > selectedTrip.kilometers_included && selectedTrip.overage_rate && (
                              <div className="flex items-center gap-2 text-warning text-sm">
                                <AlertTriangle className="h-4 w-4" />
                                <span>
                                  {formatDistance((selectedTrip.kilometers_driven || 0) - selectedTrip.kilometers_included, distanceUnit)} over @ {formatCurrencyDecimal(selectedTrip.overage_rate || 0, currency)}/{distanceUnit === "miles" ? "mi" : "km"}
                                </span>
                              </div>
                            )}
                          </>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Earnings & Protection */}
                <div className="grid grid-cols-2 gap-4">
                  {selectedTrip.total_earnings != null && (
                    <Card className="rounded-xl bg-success/5 border-success/20">
                      <CardContent className="p-4 space-y-1">
                        <h4 className="text-sm text-muted-foreground flex items-center gap-2">
                          <DollarSign className="h-4 w-4" />
                          Earnings
                        </h4>
                        <p className="text-2xl font-bold text-success">${selectedTrip.total_earnings.toFixed(2)}</p>
                      </CardContent>
                    </Card>
                  )}
                  
                  {selectedTrip.protection_plan && (
                    <Card className="rounded-xl">
                      <CardContent className="p-4 space-y-1">
                        <h4 className="text-sm text-muted-foreground flex items-center gap-2">
                          <Shield className="h-4 w-4" />
                          Protection
                        </h4>
                        <p className="font-semibold">{selectedTrip.protection_plan}</p>
                        {selectedTrip.deductible && (
                          <p className="text-sm text-muted-foreground">Deductible: {selectedTrip.deductible}</p>
                        )}
                      </CardContent>
                    </Card>
                  )}
                </div>

                {/* Cancellation Info */}
                {selectedTrip.cancellation_info && (
                  <Card className="rounded-xl border-destructive/50 bg-destructive/5">
                    <CardContent className="p-4">
                      <h4 className="font-semibold flex items-center gap-2 text-destructive mb-2">
                        <AlertTriangle className="h-4 w-4" />
                        Cancelled
                      </h4>
                      <p className="text-sm">{selectedTrip.cancellation_info}</p>
                      {selectedTrip.cancelled_by && (
                        <p className="text-sm text-muted-foreground mt-1">
                          Cancelled by: <span className="capitalize">{selectedTrip.cancelled_by}</span>
                        </p>
                      )}
                      {selectedTrip.cancelled_date && (
                        <p className="text-sm text-muted-foreground mt-1">
                          Cancelled on: {formatDate(selectedTrip.cancelled_date)}
                        </p>
                      )}
                    </CardContent>
                  </Card>
                )}

                {/* Bouncie Trip Match Section */}
                <Card className="rounded-xl">
                  <CardContent className="p-4 space-y-4">
                    <h4 className="font-semibold flex items-center gap-2">
                      <Route className="h-4 w-4 text-primary" />
                      Bouncie Trip Tracking
                    </h4>
                    
                    {isLoadingMatch ? (
                      <div className="flex items-center justify-center py-8">
                        <Loader2 className="h-6 w-6 animate-spin text-primary" />
                        <span className="ml-2 text-muted-foreground">Loading trip data...</span>
                      </div>
                    ) : tripMatch ? (
                      <div className="space-y-4">
                        {/* Match Statistics */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          <div className="space-y-1">
                            <p className="text-xs text-muted-foreground">Bouncie Trips</p>
                            <p className="text-lg font-bold">{tripMatch.bouncie_trip_count}</p>
                          </div>
                          {tripMatch.aggregated_distance_km != null && (
                            <div className="space-y-1">
                              <p className="text-xs text-muted-foreground">Total Distance</p>
                              <p className="text-lg font-bold">
                                {formatDistance(tripMatch.aggregated_distance_km, distanceUnit)}
                              </p>
                            </div>
                          )}
                          {tripMatch.total_duration_hours != null && (
                            <div className="space-y-1">
                              <p className="text-xs text-muted-foreground">Duration</p>
                              <p className="text-lg font-bold">
                                {tripMatch.total_duration_hours.toFixed(1)} hrs
                              </p>
                            </div>
                          )}
                          {tripMatch.coordinate_count != null && (
                            <div className="space-y-1">
                              <p className="text-xs text-muted-foreground">GPS Points</p>
                              <p className="text-lg font-bold">{tripMatch.coordinate_count.toLocaleString()}</p>
                            </div>
                          )}
                        </div>

                        {/* Map with Trip Navigation */}
                        {individualTrips.length > 0 ? (
                          <div className="space-y-3">
                            {/* Trip Navigation Controls */}
                            <div className="flex items-center justify-between">
                              <div>
                                <p className="text-sm font-medium">
                                  Trip {currentTripIndex + 1} of {individualTrips.length}
                                </p>
                                <p className="text-xs text-muted-foreground mt-0.5">
                                  Swipe left/right or use arrows to navigate
                                </p>
                              </div>
                              <div className="flex items-center gap-2">
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={handlePreviousTrip}
                                  disabled={currentTripIndex === 0}
                                  className="h-8 w-8 p-0"
                                  title="Previous trip"
                                >
                                  <ChevronLeft className="h-4 w-4" />
                                </Button>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={handleNextTrip}
                                  disabled={currentTripIndex === individualTrips.length - 1}
                                  className="h-8 w-8 p-0"
                                  title="Next trip"
                                >
                                  <ChevronRight className="h-4 w-4" />
                                </Button>
                              </div>
                            </div>

                            {/* Current Trip Info */}
                            {individualTrips[currentTripIndex] && (
                              <div className="flex items-center gap-4 text-xs text-muted-foreground">
                                {individualTrips[currentTripIndex].startTime && (
                                  <div>
                                    <span className="font-medium">Start:</span>{" "}
                                    {(() => {
                                      try {
                                        const date = parseISO(individualTrips[currentTripIndex].startTime);
                                        return `${format(date, "MMM d")} ${formatTime(date, timeFormat)}`;
                                      } catch {
                                        return individualTrips[currentTripIndex].startTime;
                                      }
                                    })()}
                                  </div>
                                )}
                                {individualTrips[currentTripIndex].endTime && (
                                  <div>
                                    <span className="font-medium">End:</span>{" "}
                                    {(() => {
                                      try {
                                        const date = parseISO(individualTrips[currentTripIndex].endTime);
                                        return `${format(date, "MMM d")} ${formatTime(date, timeFormat)}`;
                                      } catch {
                                        return individualTrips[currentTripIndex].endTime;
                                      }
                                    })()}
                                  </div>
                                )}
                                {individualTrips[currentTripIndex].distance != null && (
                                  <div>
                                    <span className="font-medium">Distance:</span>{" "}
                                    {formatDistance(individualTrips[currentTripIndex].distance, distanceUnit)}
                                  </div>
                                )}
                                {individualTrips[currentTripIndex].coordinate_count != null && (
                                  <div>
                                    <span className="font-medium">Points:</span>{" "}
                                    {individualTrips[currentTripIndex].coordinate_count.toLocaleString()}
                                  </div>
                                )}
                              </div>
                            )}

                            {/* Map with Swipe Support */}
                            <div 
                              className="w-full h-[400px] rounded-lg border border-border overflow-hidden relative bg-muted/10"
                              onTouchStart={handleTouchStart}
                              onTouchMove={handleTouchMove}
                              onTouchEnd={handleTouchEnd}
                            >
                              {mapError ? (
                                <div className="w-full h-full flex items-center justify-center text-destructive bg-destructive/10">
                                  <div className="text-center p-4">
                                    <AlertTriangle className="h-8 w-8 mx-auto mb-2" />
                                    <p className="font-medium">{mapError}</p>
                                    <p className="text-sm text-muted-foreground mt-2">
                                      The route line may not be visible due to this error.
                                    </p>
                                  </div>
                                </div>
                              ) : individualTrips[currentTripIndex]?.coordinates && individualTrips[currentTripIndex].coordinates.length > 0 ? (
                                <div 
                                  ref={mapContainer} 
                                  className="w-full h-full"
                                />
                              ) : (
                                <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                                  <div className="text-center">
                                    <Route className="h-8 w-8 mx-auto mb-2 opacity-50" />
                                    <p>No GPS data for this trip</p>
                                  </div>
                                </div>
                              )}
                            </div>
                            
                            {/* Overall Tracking Period */}
                            {tripMatch.bouncie_earliest_start && tripMatch.bouncie_latest_end && (
                              <div className="text-xs text-muted-foreground">
                                <span className="font-medium">Overall tracked period:</span>{" "}
                                {(() => {
                                  try {
                                    const startDate = parseISO(tripMatch.bouncie_earliest_start!);
                                    const endDate = parseISO(tripMatch.bouncie_latest_end!);
                                    return `${format(startDate, "MMM d, yyyy")} ${formatTime(startDate, timeFormat)} - ${format(endDate, "MMM d, yyyy")} ${formatTime(endDate, timeFormat)}`;
                                  } catch {
                                    return `${tripMatch.bouncie_earliest_start} - ${tripMatch.bouncie_latest_end}`;
                                  }
                                })()}
                              </div>
                            )}
                          </div>
                        ) : tripMatch?.has_coordinates && tripMatch.coordinates && tripMatch.coordinates.length > 0 ? (
                          <div className="space-y-2">
                            <p className="text-sm text-muted-foreground">Route Map</p>
                            <div 
                              ref={mapContainer} 
                              className="w-full h-[400px] rounded-lg border border-border overflow-hidden"
                            />
                          </div>
                        ) : (
                          <div className="text-center py-8 text-muted-foreground">
                            <Route className="h-8 w-8 mx-auto mb-2 opacity-50" />
                            <p>No GPS coordinates available for this trip</p>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="text-center py-8 text-muted-foreground">
                        <Route className="h-8 w-8 mx-auto mb-2 opacity-50" />
                        <p>No Bouncie trip data found for this trip</p>
                        <p className="text-xs mt-1">Make sure the vehicle is mapped to a Bouncie device</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default TripHistory;