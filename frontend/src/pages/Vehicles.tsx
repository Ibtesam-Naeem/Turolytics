import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";
import { Label } from "@/components/ui/label";
import { 
  Car, 
  Fuel, 
  DollarSign, 
  Gauge,
  Star,
  FileText,
  Hash,
  CreditCard,
  Route,
  TrendingUp,
  Loader2,
  Search,
  Settings,
  Calendar as CalendarIcon
} from "lucide-react";
import { format } from "date-fns";
import { cn } from "@/lib/utils";
import { useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { vehiclesService, Vehicle } from "@/services/vehicles-service";
import { useToast } from "@/hooks/use-toast";
import { useBouncieLiveData } from "@/hooks/useBouncieLiveData";
import { bouncieService } from "@/services/bouncie-service";

const Vehicles = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [searchQuery, setSearchQuery] = useState("");
  
  // Add Bouncie live data hook
  const { liveVehicles, bouncieConnected } = useBouncieLiveData();
  
  // Add state for vehicle mappings (vehicle_id -> imei)
  const [vehicleMappings, setVehicleMappings] = useState<Map<number, string>>(new Map());
  
  // Config dialog state
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [selectedVehicle, setSelectedVehicle] = useState<Vehicle | null>(null);
  const [listedDate, setListedDate] = useState<Date | undefined>(undefined);
  const [removedDate, setRemovedDate] = useState<Date | undefined>(undefined);
  const [utilizationGoal, setUtilizationGoal] = useState<string>("");
  const [datePickerOpen, setDatePickerOpen] = useState(false);
  const [removedDatePickerOpen, setRemovedDatePickerOpen] = useState(false);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    const loadVehicles = async () => {
      try {
        setLoading(true);
        const response = await vehiclesService.getVehicles({ 
          include_stats: true,
          limit: 1000 
        });
        // Debug: Log odometer values from API
        console.log('Vehicles from API:', response.vehicles.map(v => ({
          id: v.id,
          name: v.name,
          total_odometer: v.total_odometer
        })));
        setVehicles(response.vehicles);
        setTotal(response.total);
      } catch (error) {
        console.error('Failed to load vehicles:', error);
        toast({
          title: "Error",
          description: "Failed to load vehicles. Please try again.",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };
    loadVehicles();
  }, [toast]);

  // Fetch vehicle mappings to match Turo vehicles with Bouncie IMEIs
  useEffect(() => {
    const loadMappings = async () => {
      if (!bouncieConnected) return;
      
      try {
        const mappingsResponse = await bouncieService.getVehicleMappings(100, 0);
        const mappings = new Map<number, string>();
        mappingsResponse.mappings.forEach(m => {
          if (m.vehicle_id) {
            mappings.set(m.vehicle_id, m.imei);
          }
        });
        setVehicleMappings(mappings);
      } catch (err) {
        console.error('Failed to load vehicle mappings:', err);
      }
    };
    
    loadMappings();
  }, [bouncieConnected]);

  const getStatusConfig = (status?: string) => {
    const statusMapped = status === "active" || status === "maintenance" || status === "inactive" 
      ? status 
      : (status?.toLowerCase().includes("listed") || status?.toLowerCase().includes("active") ? "active" : "inactive");
    
    switch (statusMapped) {
      case "active":
        return { 
          bg: "bg-success/20", 
          text: "text-success", 
          border: "border-success/30",
          label: "Active"
        };
      case "maintenance":
        return { 
          bg: "bg-warning/20", 
          text: "text-warning", 
          border: "border-warning/30",
          label: "Maintenance"
        };
      case "inactive":
        return { 
          bg: "bg-destructive/20", 
          text: "text-destructive", 
          border: "border-destructive/30",
          label: "Inactive"
        };
      default:
        return { 
          bg: "bg-muted/20", 
          text: "text-muted-foreground", 
          border: "border-muted/30",
          label: status || "Unknown"
        };
    }
  };

  const getFuelConfig = (level?: number) => {
    if (!level) return { color: "text-muted-foreground", bg: "bg-muted" };
    if (level < 25) return { color: "text-destructive", bg: "bg-destructive" };
    if (level < 50) return { color: "text-warning", bg: "bg-warning" };
    return { color: "text-success", bg: "bg-success" };
  };

  // Filter vehicles based on search query
  const filteredVehicles = vehicles.filter((vehicle) => {
    if (!searchQuery.trim()) return true;
    
    const query = searchQuery.toLowerCase();
    const name = vehicle.name?.toLowerCase() || "";
    const licensePlate = vehicle.license_plate?.toLowerCase() || "";
    const year = vehicle.year?.toString() || "";
    const status = vehicle.status?.toLowerCase() || "";
    const statusMapped = vehicle.status_mapped?.toLowerCase() || "";
    
    return (
      name.includes(query) ||
      licensePlate.includes(query) ||
      year.includes(query) ||
      status.includes(query) ||
      statusMapped.includes(query)
    );
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <p className="text-muted-foreground">Loading vehicles...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="w-full px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Vehicles</h1>
            <p className="text-sm text-muted-foreground">Manage your fleet</p>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="outline" className="text-sm px-3 py-1">
              {searchQuery ? `${filteredVehicles.length} of ${total}` : total} Vehicles
            </Badge>
          </div>
        </div>

        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by name, license plate, year, or status..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 w-full max-w-md"
          />
        </div>

        {/* Vehicle Grid */}
        {vehicles.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Car className="w-16 h-16 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold text-foreground mb-2">No vehicles found</h3>
            <p className="text-sm text-muted-foreground">
              Connect your Turo account and scrape data to see your vehicles here.
            </p>
          </div>
        ) : filteredVehicles.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Search className="w-16 h-16 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold text-foreground mb-2">No vehicles match your search</h3>
            <p className="text-sm text-muted-foreground">
              Try adjusting your search query.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
            {filteredVehicles.map((vehicle) => {
              const statusConfig = getStatusConfig(vehicle.status_mapped || vehicle.status);
              
              // Get fuel level from Bouncie live data, or fallback to vehicle's fuel_level
              const imei = vehicleMappings.get(vehicle.id);
              const liveData = imei ? liveVehicles.find(v => v.imei === imei) : undefined;
              const fuelLevel = liveData?.fuelLevel !== undefined 
                ? Math.round(liveData.fuelLevel) 
                : (vehicle.fuel_level !== undefined ? Math.round(vehicle.fuel_level) : undefined);
              const fuelConfig = getFuelConfig(fuelLevel);
            
            return (
              <Card 
                key={vehicle.id} 
                className="group relative overflow-hidden border-2 hover:border-primary/40 transition-all duration-300 bg-gradient-to-br from-card to-card/80"
              >
                {/* Status indicator line */}
                <div className={`absolute top-0 left-0 right-0 h-1 ${statusConfig.bg.replace('/20', '')}`} />
                
                <CardContent className="p-5 pt-6">
                  {/* Header: Name + Status + Image */}
                  <div className="flex items-start justify-between mb-5">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center border border-primary/20">
                        <Car className="w-6 h-6 text-primary" />
                      </div>
                      <div>
                        <h3 className="font-bold text-lg text-foreground group-hover:text-primary transition-colors">
                          {vehicle.name}
                        </h3>
                        <Badge 
                          variant="outline" 
                          className={`text-xs mt-1 ${statusConfig.bg} ${statusConfig.text} ${statusConfig.border}`}
                        >
                          {statusConfig.label}
                        </Badge>
                      </div>
                    </div>
                    {/* Small car image placeholder */}
                    <div className="w-16 h-12 rounded-lg overflow-hidden border border-border/50 shadow-sm bg-muted/50 flex items-center justify-center">
                      <Car className="w-5 h-5 text-muted-foreground" />
                    </div>
                  </div>

                  {/* License Plate & Year */}
                  <div className="space-y-2.5 mb-5 pb-5 border-b border-border/60">
                    {vehicle.license_plate && (
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded-lg bg-muted/50 flex items-center justify-center">
                          <CreditCard className="w-3.5 h-3.5 text-muted-foreground" />
                        </div>
                        <span className="text-sm text-muted-foreground">Plate:</span>
                        <span className="text-sm text-foreground font-bold tracking-wide">{vehicle.license_plate}</span>
                      </div>
                    )}
                    {vehicle.year && (
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded-lg bg-muted/50 flex items-center justify-center">
                          <Hash className="w-3.5 h-3.5 text-muted-foreground" />
                        </div>
                        <span className="text-sm text-muted-foreground">Year:</span>
                        <span className="text-sm text-foreground font-mono tracking-tight">{vehicle.year}</span>
                      </div>
                    )}
                  </div>

                  {/* Stats Grid */}
                  <div className="grid grid-cols-2 gap-3 mb-5">
                    {/* Revenue */}
                    <div className="p-3 rounded-xl bg-gradient-to-br from-success/10 to-success/5 border border-success/20">
                      <div className="flex items-center gap-1.5 mb-1">
                        <DollarSign className="w-3.5 h-3.5 text-success" />
                        <span className="text-xs text-muted-foreground font-medium">Revenue</span>
                      </div>
                      <p className="text-base font-bold text-success">
                        ${(vehicle.total_revenue || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </p>
                    </div>
                    
                    {/* Utilization */}
                    <div className="p-3 rounded-xl bg-gradient-to-br from-chart-3/10 to-chart-3/5 border border-chart-3/20">
                      <div className="flex items-center gap-1.5 mb-1">
                        <TrendingUp className="w-3.5 h-3.5 text-chart-3" />
                        <span className="text-xs text-muted-foreground font-medium">Utilization</span>
                      </div>
                      <div className="space-y-1">
                        <p className="text-base font-bold text-chart-3">
                          {vehicle.utilization !== undefined ? `${vehicle.utilization.toFixed(1)}%` : "N/A"}
                        </p>
                        {vehicle.utilization !== undefined && (
                          <Progress 
                            value={vehicle.utilization} 
                            className="h-1.5"
                          />
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Secondary Stats Grid */}
                  <div className="grid grid-cols-2 gap-3 mb-5">
                    {/* Odometer */}
                    <div className="p-3 rounded-xl bg-gradient-to-br from-primary/10 to-primary/5 border border-primary/20">
                      <div className="flex items-center gap-1.5 mb-1">
                        <Gauge className="w-3.5 h-3.5 text-primary" />
                        <span className="text-xs text-muted-foreground font-medium">Odometer</span>
                      </div>
                      <p className="text-base font-bold text-foreground">
                        {(vehicle.total_odometer || 0).toLocaleString()} km
                      </p>
                    </div>
                    
                    {/* Fuel */}
                    <div className={`p-3 rounded-xl bg-gradient-to-br ${fuelConfig.color === 'text-success' ? 'from-success/10 to-success/5 border-success/20' : fuelConfig.color === 'text-warning' ? 'from-warning/10 to-warning/5 border-warning/20' : 'from-destructive/10 to-destructive/5 border-destructive/20'} border`}>
                      <div className="flex items-center gap-1.5 mb-1">
                        <Fuel className={`w-3.5 h-3.5 ${fuelConfig.color}`} />
                        <span className="text-xs text-muted-foreground font-medium">Fuel</span>
                      </div>
                      <div className="space-y-1">
                        <p className={`text-base font-bold ${fuelConfig.color}`}>
                          {fuelLevel ? `${fuelLevel}%` : "N/A"}
                        </p>
                        {fuelLevel !== undefined && (
                          <Progress 
                            value={fuelLevel} 
                            className="h-1.5"
                          />
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Trips & Rating Row */}
                  <div className="grid grid-cols-2 gap-3 mb-5">
                    <div className="p-3 rounded-xl bg-muted/30 border border-border/50">
                      <div className="flex items-center gap-1.5 mb-1">
                        <Route className="w-3.5 h-3.5 text-chart-1" />
                        <span className="text-xs text-muted-foreground font-medium">Total Trips</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <p className="text-xl font-bold text-foreground">{vehicle.total_trips || vehicle.trip_count || 0}</p>
                        <TrendingUp className="w-4 h-4 text-success" />
                      </div>
                    </div>
                    
                    <div className="p-3 rounded-xl bg-muted/30 border border-border/50">
                      <div className="flex items-center gap-1.5 mb-1">
                        <Star className="w-3.5 h-3.5 text-rating fill-rating" />
                        <span className="text-xs text-muted-foreground font-medium">Avg Rating</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <p className="text-xl font-bold text-foreground">{vehicle.avg_rating || vehicle.rating || 0}</p>
                        <div className="flex">
                          {[...Array(5)].map((_, i) => {
                            const rating = vehicle.avg_rating || vehicle.rating || 0;
                            return (
                              <Star 
                                key={i} 
                                className={`w-3 h-3 ${i < Math.floor(rating) ? 'text-rating fill-rating' : 'text-muted-foreground/30'}`} 
                              />
                            );
                          })}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-2">
                    <Button 
                      className="flex-1 gap-2 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 hover:border-primary/40"
                      variant="ghost"
                      onClick={() => navigate(`/documents?vehicle=${encodeURIComponent(vehicle.name || '')}`)}
                    >
                      <FileText className="w-4 h-4" />
                      Documents
                    </Button>
                    <Button 
                      className="gap-2 bg-muted hover:bg-muted/80 text-foreground border border-border"
                      variant="ghost"
                      size="icon"
                      onClick={() => {
                        setSelectedVehicle(vehicle);
                        // Parse the date string properly - handle both ISO format and date-only format
                        if (vehicle.listed_on_turo_date) {
                          try {
                            // The date comes as ISO string from backend, parse it
                            const date = new Date(vehicle.listed_on_turo_date);
                            // Check if date is valid
                            if (!isNaN(date.getTime())) {
                              setListedDate(date);
                            } else {
                              console.warn('Invalid date:', vehicle.listed_on_turo_date);
                              setListedDate(undefined);
                            }
                          } catch (e) {
                            console.error('Error parsing listed_on_turo_date:', e, vehicle.listed_on_turo_date);
                            setListedDate(undefined);
                          }
                        } else {
                          setListedDate(undefined);
                        }
                        // Parse removed date
                        if (vehicle.removed_from_turo_date) {
                          try {
                            const date = new Date(vehicle.removed_from_turo_date);
                            if (!isNaN(date.getTime())) {
                              setRemovedDate(date);
                            } else {
                              setRemovedDate(undefined);
                            }
                          } catch (e) {
                            console.error('Error parsing removed_from_turo_date:', e);
                            setRemovedDate(undefined);
                          }
                        } else {
                          setRemovedDate(undefined);
                        }
                        // Set utilization goal
                        setUtilizationGoal(vehicle.utilization_goal?.toString() || "");
                        setConfigDialogOpen(true);
                      }}
                      title="Vehicle Configuration"
                    >
                      <Settings className="w-4 h-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
          </div>
        )}
      </div>

      {/* Vehicle Config Dialog */}
      <Dialog open={configDialogOpen} onOpenChange={setConfigDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Vehicle Configuration</DialogTitle>
            <DialogDescription>
              Configure settings for {selectedVehicle?.name}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>First Listed on Turo</Label>
              <Popover open={datePickerOpen} onOpenChange={setDatePickerOpen}>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "w-full justify-start text-left font-normal",
                      !listedDate && "text-muted-foreground"
                    )}
                    disabled={updating}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {listedDate ? format(listedDate, "PPP") : <span>Pick a date</span>}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    mode="single"
                    selected={listedDate}
                    onSelect={(date) => {
                      setListedDate(date);
                      setDatePickerOpen(false);
                    }}
                    initialFocus
                  />
                </PopoverContent>
              </Popover>
              {listedDate && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 text-xs text-muted-foreground hover:text-destructive"
                  onClick={() => setListedDate(undefined)}
                  disabled={updating}
                >
                  Clear date
                </Button>
              )}
              <p className="text-xs text-muted-foreground">
                The date this vehicle was first posted on Turo. This is used to calculate accurate utilization (months before this date will be excluded).
              </p>
            </div>
            <div className="space-y-2">
              <Label>Date Removed from Turo</Label>
              <Popover open={removedDatePickerOpen} onOpenChange={setRemovedDatePickerOpen}>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "w-full justify-start text-left font-normal",
                      !removedDate && "text-muted-foreground"
                    )}
                    disabled={updating}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {removedDate ? format(removedDate, "PPP") : <span>Not removed (still active)</span>}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    mode="single"
                    selected={removedDate}
                    onSelect={(date) => {
                      setRemovedDate(date);
                      setRemovedDatePickerOpen(false);
                    }}
                    initialFocus
                  />
                </PopoverContent>
              </Popover>
              {removedDate && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 text-xs text-muted-foreground hover:text-destructive"
                  onClick={() => setRemovedDate(undefined)}
                  disabled={updating}
                >
                  Clear date (mark as active)
                </Button>
              )}
              <p className="text-xs text-muted-foreground">
                The date this vehicle was removed from Turo. Leave empty if the vehicle is still active (standard).
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="utilization-goal">Utilization Goal (%)</Label>
              <Input
                id="utilization-goal"
                type="number"
                min="0"
                max="100"
                step="0.1"
                value={utilizationGoal}
                onChange={(e) => setUtilizationGoal(e.target.value)}
                placeholder="e.g., 75.0"
                disabled={updating}
              />
              <p className="text-xs text-muted-foreground">
                Target utilization percentage for this vehicle (0-100). Leave empty to remove the goal.
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setConfigDialogOpen(false);
                setSelectedVehicle(null);
                setListedDate(undefined);
                setRemovedDate(undefined);
                setUtilizationGoal("");
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={async () => {
                if (!selectedVehicle) return;
                
                // Validate utilization goal if provided
                if (utilizationGoal && utilizationGoal.trim() !== "") {
                  const goalValue = parseFloat(utilizationGoal);
                  if (isNaN(goalValue) || goalValue < 0 || goalValue > 100) {
                    toast({
                      title: "Invalid Goal",
                      description: "Utilization goal must be a number between 0 and 100.",
                      variant: "destructive",
                    });
                    return;
                  }
                }
                
                try {
                  setUpdating(true);
                  await vehiclesService.updateVehicle(selectedVehicle.id, {
                    listed_on_turo_date: listedDate ? listedDate.toISOString().split('T')[0] : undefined,
                    removed_from_turo_date: removedDate ? removedDate.toISOString().split('T')[0] : undefined,
                    utilization_goal: utilizationGoal && utilizationGoal.trim() !== "" ? parseFloat(utilizationGoal) : undefined,
                  });
                  toast({
                    title: "Vehicle Updated",
                    description: "Vehicle configuration has been saved.",
                  });
                  // Reload vehicles to get updated data
                  const response = await vehiclesService.getVehicles({ 
                    include_stats: true,
                    limit: 1000 
                  });
                  setVehicles(response.vehicles);
                  
                  // Debug: Log the updated vehicle to verify the date is there
                  const updatedVehicle = response.vehicles.find(v => v.id === selectedVehicle.id);
                  if (updatedVehicle) {
                    console.log('Updated vehicle after save:', {
                      id: updatedVehicle.id,
                      name: updatedVehicle.name,
                      listed_on_turo_date: updatedVehicle.listed_on_turo_date,
                      removed_from_turo_date: updatedVehicle.removed_from_turo_date,
                      utilization_goal: updatedVehicle.utilization_goal,
                      dateType: typeof updatedVehicle.listed_on_turo_date
                    });
                  }
                  
                  setConfigDialogOpen(false);
                  setSelectedVehicle(null);
                  setListedDate(undefined);
                  setRemovedDate(undefined);
                  setUtilizationGoal("");
                } catch (error) {
                  console.error('Failed to update vehicle:', error);
                  toast({
                    title: "Error",
                    description: error instanceof Error ? error.message : "Failed to update vehicle configuration.",
                    variant: "destructive",
                  });
                } finally {
                  setUpdating(false);
                }
              }}
              disabled={updating}
            >
              {updating ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                "Save"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Vehicles;
