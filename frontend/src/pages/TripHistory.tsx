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
} from "lucide-react";
import { useState, useEffect } from "react";
import { tripsService, Trip } from "@/services/trips-service";
import { vehiclesService, Vehicle } from "@/services/vehicles-service";
import { format, parseISO } from "date-fns";

const TripHistory = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [sortBy, setSortBy] = useState("recent");
  const [vehicleFilter, setVehicleFilter] = useState<string>("all");
  const [selectedTrip, setSelectedTrip] = useState<Trip | null>(null);
  const [trips, setTrips] = useState<Trip[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalTrips, setTotalTrips] = useState(0);
  const [limit] = useState(50);
  const [offset, setOffset] = useState(0);
  const [vehiclesMap, setVehiclesMap] = useState<Map<number, Vehicle>>(new Map());
  const [allVehicles, setAllVehicles] = useState<Vehicle[]>([]);

  // Fetch trips and vehicles from API
  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const [tripsResponse, vehiclesResponse] = await Promise.all([
          tripsService.getTrips({
            status: statusFilter !== "all" ? statusFilter.toUpperCase() : undefined,
            trip_type: "trip_history", // Filter for trip history
            limit,
            offset: 0, // Reset to 0 when filters change
          }),
          vehiclesService.getVehicles({ limit: 1000 }), // Get all vehicles
        ]);

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

  // Filter and sort trips
  const filteredTrips = trips
    .filter(trip => {
      const matchesSearch = 
        trip.customer_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        trip.trip_id.toLowerCase().includes(searchQuery.toLowerCase());
      
      const matchesVehicle = vehicleFilter === "all" || 
        (trip.vehicle_id && vehicleFilter === trip.vehicle_id.toString());
      
      return matchesSearch && matchesVehicle;
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
      // Most recent by start_date or created_at
      const dateA = a.start_date ? new Date(a.start_date).getTime() : (a.created_at ? new Date(a.created_at).getTime() : 0);
      const dateB = b.start_date ? new Date(b.start_date).getTime() : (b.created_at ? new Date(b.created_at).getTime() : 0);
      return dateB - dateA;
    });

  const loadMoreTrips = async () => {
    try {
      const newOffset = offset + limit;
      const response = await tripsService.getTrips({
        status: statusFilter !== "all" ? statusFilter.toUpperCase() : undefined,
        trip_type: "trip_history",
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
    return timeString;
  };


  const handleCloseModal = () => {
    setSelectedTrip(null);
  };

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

  const totalEarnings = filteredTrips.reduce((sum, t) => sum + (t.total_earnings || 0), 0);
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
                <p className="text-xl font-bold">${totalEarnings.toLocaleString()}</p>
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
                <p className="text-xl font-bold">{totalDistance.toLocaleString()} km</p>
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
              <Select value={sortBy} onValueChange={setSortBy}>
                <SelectTrigger className="w-[160px]">
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="recent">Most Recent</SelectItem>
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
                            <p className="text-lg font-bold">{trip.kilometers_driven} km</p>
                            {trip.kilometers_included && (
                              <p className="text-xs text-muted-foreground">/ {trip.kilometers_included}</p>
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
                            <p className="text-lg font-bold text-success">${trip.total_earnings.toFixed(2)}</p>
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
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
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
                            {selectedTrip.kilometers_driven ?? 0} / {selectedTrip.kilometers_included ?? 0} km
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
                                  {(selectedTrip.kilometers_driven || 0) - selectedTrip.kilometers_included} km over @ ${selectedTrip.overage_rate}/km
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
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default TripHistory;