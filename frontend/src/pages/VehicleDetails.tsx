import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { 
  Car, 
  Gauge, 
  Fuel, 
  Settings, 
  Calendar, 
  DollarSign, 
  MapPin, 
  Star, 
  TrendingUp,
  Wrench,
  AlertTriangle,
  CheckCircle,
  Clock,
  BarChart3,
  Battery,
  Zap
} from "lucide-react";

interface VehicleData {
  id: string;
  name: string;
  year: number;
  make: string;
  model: string;
  color: string;
  vin: string;
  licensePlate: string;
  type: string;
  status: "on-trip" | "available" | "maintenance";
  image: string;
  specs: {
    mileage: number;
    range: string;
    fuelEconomy: string;
    topSpeed: number;
  };
  performance: {
    totalTrips: number;
    avgRating: number;
    totalReviews: number;
    utilizationRate: number;
  };
  earnings: {
    total: number;
    thisMonth: number;
    lastMonth: number;
    avgPerTrip: number;
  };
  maintenance: {
    healthScore: number;
    lastService: { name: string; date: string; cost: number };
    upcoming: { name: string; date: string; cost: number } | null;
    history: { name: string; date: string; cost: number }[];
  };
  location: string;
}

const vehiclesData: VehicleData[] = [
  {
    id: "tesla-3",
    name: "Tesla Model 3",
    year: 2024,
    make: "Tesla",
    model: "Model 3",
    color: "Pearl White",
    vin: "5YJ3E1EA9MF123456",
    licensePlate: "8ABC123",
    type: "Electric",
    status: "on-trip",
    image: "https://images.unsplash.com/photo-1560958089-b8a1929cea89?w=800",
    specs: {
      mileage: 12500,
      range: "272 miles",
      fuelEconomy: "120 MPGe",
      topSpeed: 85,
    },
    performance: {
      totalTrips: 87,
      avgRating: 4.9,
      totalReviews: 82,
      utilizationRate: 78,
    },
    earnings: {
      total: 8450,
      thisMonth: 1280,
      lastMonth: 1150,
      avgPerTrip: 97,
    },
    maintenance: {
      healthScore: 92,
      lastService: { name: "Tire Rotation", date: "Oct 15, 2024", cost: 80 },
      upcoming: { name: "Brake Inspection", date: "Dec 20, 2024", cost: 120 },
      history: [
        { name: "Tire Rotation", date: "Oct 15, 2024", cost: 80 },
        { name: "Brake Inspection", date: "Sep 8, 2024", cost: 120 },
        { name: "Car Wash & Detail", date: "Nov 1, 2024", cost: 150 },
      ],
    },
    location: "San Francisco, CA",
  },
  {
    id: "bmw-x5",
    name: "BMW X5",
    year: 2023,
    make: "BMW",
    model: "X5",
    color: "Alpine White",
    vin: "5UXCR6C58N9K12345",
    licensePlate: "7DEF456",
    type: "Gas",
    status: "on-trip",
    image: "https://images.unsplash.com/photo-1617469767053-d3b523a0b982?w=800",
    specs: {
      mileage: 28400,
      range: "480 miles",
      fuelEconomy: "24 MPG",
      topSpeed: 78,
    },
    performance: {
      totalTrips: 124,
      avgRating: 4.8,
      totalReviews: 118,
      utilizationRate: 82,
    },
    earnings: {
      total: 15200,
      thisMonth: 1850,
      lastMonth: 1720,
      avgPerTrip: 122,
    },
    maintenance: {
      healthScore: 45,
      lastService: { name: "Oil Change", date: "Nov 5, 2024", cost: 180 },
      upcoming: { name: "Engine Check (Urgent)", date: "Immediate", cost: 450 },
      history: [
        { name: "Oil Change", date: "Nov 5, 2024", cost: 180 },
        { name: "Tire Rotation", date: "Oct 10, 2024", cost: 100 },
        { name: "Brake Pads", date: "Sep 15, 2024", cost: 380 },
      ],
    },
    location: "Los Angeles, CA",
  },
  {
    id: "mercedes-c",
    name: "Mercedes C-Class",
    year: 2024,
    make: "Mercedes",
    model: "C-Class",
    color: "Obsidian Black",
    vin: "W1KWF8DB1NR123456",
    licensePlate: "9GHI789",
    type: "Gas",
    status: "available",
    image: "https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?w=800",
    specs: {
      mileage: 8200,
      range: "520 miles",
      fuelEconomy: "28 MPG",
      topSpeed: 72,
    },
    performance: {
      totalTrips: 45,
      avgRating: 4.95,
      totalReviews: 43,
      utilizationRate: 65,
    },
    earnings: {
      total: 5680,
      thisMonth: 920,
      lastMonth: 1050,
      avgPerTrip: 126,
    },
    maintenance: {
      healthScore: 88,
      lastService: { name: "Full Detail", date: "Nov 10, 2024", cost: 200 },
      upcoming: { name: "Oil Change", date: "Jan 5, 2025", cost: 150 },
      history: [
        { name: "Full Detail", date: "Nov 10, 2024", cost: 200 },
        { name: "Tire Rotation", date: "Oct 20, 2024", cost: 85 },
      ],
    },
    location: "San Diego, CA",
  },
  {
    id: "audi-a4",
    name: "Audi A4",
    year: 2023,
    make: "Audi",
    model: "A4",
    color: "Glacier White",
    vin: "WAUEAAF40NA123456",
    licensePlate: "2JKL012",
    type: "Gas",
    status: "available",
    image: "https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?w=800",
    specs: {
      mileage: 15600,
      range: "460 miles",
      fuelEconomy: "26 MPG",
      topSpeed: 75,
    },
    performance: {
      totalTrips: 68,
      avgRating: 4.7,
      totalReviews: 65,
      utilizationRate: 71,
    },
    earnings: {
      total: 7420,
      thisMonth: 1100,
      lastMonth: 980,
      avgPerTrip: 109,
    },
    maintenance: {
      healthScore: 78,
      lastService: { name: "Brake Pad Replacement", date: "Nov 15, 2024", cost: 420 },
      upcoming: { name: "Fluid Top-up", date: "Dec 3, 2024", cost: 85 },
      history: [
        { name: "Brake Pad Replacement", date: "Nov 15, 2024", cost: 420 },
        { name: "Oil Change", date: "Oct 5, 2024", cost: 120 },
        { name: "Tire Rotation", date: "Sep 1, 2024", cost: 80 },
      ],
    },
    location: "San Jose, CA",
  },
  {
    id: "tesla-y",
    name: "Tesla Model Y",
    year: 2024,
    make: "Tesla",
    model: "Model Y",
    color: "Midnight Silver",
    vin: "7SAYGDEE5PA123456",
    licensePlate: "3MNO345",
    type: "Electric",
    status: "maintenance",
    image: "https://images.unsplash.com/photo-1620891549027-942fdc95d3f5?w=800",
    specs: {
      mileage: 22100,
      range: "310 miles",
      fuelEconomy: "125 MPGe",
      topSpeed: 82,
    },
    performance: {
      totalTrips: 95,
      avgRating: 4.85,
      totalReviews: 92,
      utilizationRate: 75,
    },
    earnings: {
      total: 10850,
      thisMonth: 0,
      lastMonth: 1420,
      avgPerTrip: 114,
    },
    maintenance: {
      healthScore: 88,
      lastService: { name: "Annual Inspection", date: "Nov 18, 2024", cost: 150 },
      upcoming: null,
      history: [
        { name: "Annual Inspection", date: "Nov 18, 2024", cost: 150 },
        { name: "Tire Rotation", date: "Oct 25, 2024", cost: 80 },
        { name: "Software Update", date: "Sep 20, 2024", cost: 0 },
      ],
    },
    location: "Oakland, CA",
  },
];

const VehicleDetails = () => {
  const getStatusBadge = (status: string) => {
    switch (status) {
      case "on-trip":
        return <Badge className="bg-primary/20 text-primary border-primary/30">On Trip</Badge>;
      case "available":
        return <Badge className="bg-success/20 text-success border-success/30">Available</Badge>;
      case "maintenance":
        return <Badge variant="destructive">In Maintenance</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  const getHealthColor = (score: number) => {
    if (score >= 80) return "text-success";
    if (score >= 60) return "text-warning";
    return "text-destructive";
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value);
  };

  const renderVehicleContent = (vehicle: VehicleData) => (
    <div className="space-y-6 mt-6 animate-fade-in">
      {/* Vehicle Header Card */}
      <Card className="overflow-hidden">
        <div className="grid md:grid-cols-3 gap-0">
          <div className="aspect-video md:aspect-auto md:h-full overflow-hidden bg-muted">
            <img 
              src={vehicle.image} 
              alt={vehicle.name}
              className="w-full h-full object-cover"
            />
          </div>
          <div className="md:col-span-2 p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="text-2xl font-bold text-foreground">{vehicle.year} {vehicle.name}</h2>
                <p className="text-muted-foreground">VIN: {vehicle.vin}</p>
              </div>
              {getStatusBadge(vehicle.status)}
            </div>
            
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6">
              <div className="text-center p-3 rounded-lg bg-muted/50">
                <p className="text-2xl font-bold text-foreground">{vehicle.performance.totalTrips}</p>
                <p className="text-xs text-muted-foreground">Total Trips</p>
              </div>
              <div className="text-center p-3 rounded-lg bg-muted/50">
                <div className="flex items-center justify-center gap-1">
                  <Star className="h-4 w-4 fill-rating text-rating" />
                  <span className="text-2xl font-bold text-foreground">{vehicle.performance.avgRating}</span>
                </div>
                <p className="text-xs text-muted-foreground">{vehicle.performance.totalReviews} reviews</p>
              </div>
              <div className="text-center p-3 rounded-lg bg-muted/50">
                <p className="text-2xl font-bold text-success">{formatCurrency(vehicle.earnings.total)}</p>
                <p className="text-xs text-muted-foreground">Total Earnings</p>
              </div>
              <div className="text-center p-3 rounded-lg bg-muted/50">
                <p className={`text-2xl font-bold ${getHealthColor(vehicle.maintenance.healthScore)}`}>
                  {vehicle.maintenance.healthScore}%
                </p>
                <p className="text-xs text-muted-foreground">Health Score</p>
              </div>
            </div>
          </div>
        </div>
      </Card>

      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
        {/* Specifications */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Settings className="h-5 w-5 text-primary" />
              Specifications
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between py-2 border-b border-border">
              <span className="text-muted-foreground">Make</span>
              <span className="font-semibold">{vehicle.make}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-border">
              <span className="text-muted-foreground">Model</span>
              <span className="font-semibold">{vehicle.model}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-border">
              <span className="text-muted-foreground">Year</span>
              <span className="font-semibold">{vehicle.year}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-border">
              <span className="text-muted-foreground">Color</span>
              <span className="font-semibold">{vehicle.color}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-border">
              <span className="text-muted-foreground">License Plate</span>
              <span className="font-semibold">{vehicle.licensePlate}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-border">
              <span className="text-muted-foreground">Type</span>
              <Badge variant="outline" className="gap-1">
                {vehicle.type === "Electric" ? <Zap className="h-3 w-3" /> : <Fuel className="h-3 w-3" />}
                {vehicle.type}
              </Badge>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-muted-foreground">Location</span>
              <span className="font-semibold flex items-center gap-1">
                <MapPin className="h-3 w-3" />
                {vehicle.location}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Performance Stats */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Gauge className="h-5 w-5 text-primary" />
              Performance
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between py-2 border-b border-border">
              <span className="text-muted-foreground">Total Mileage</span>
              <span className="font-semibold">{vehicle.specs.mileage.toLocaleString()} mi</span>
            </div>
            <div className="flex justify-between py-2 border-b border-border">
              <span className="text-muted-foreground">{vehicle.type === "Electric" ? "Battery Range" : "Fuel Range"}</span>
              <span className="font-semibold">{vehicle.specs.range}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-border">
              <span className="text-muted-foreground">Fuel Economy</span>
              <span className="font-semibold">{vehicle.specs.fuelEconomy}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-border">
              <span className="text-muted-foreground">Top Speed Recorded</span>
              <span className="font-semibold">{vehicle.specs.topSpeed} mph</span>
            </div>
            <div className="pt-2">
              <div className="flex justify-between mb-2">
                <span className="text-muted-foreground">Utilization Rate</span>
                <span className="font-semibold">{vehicle.performance.utilizationRate}%</span>
              </div>
              <Progress value={vehicle.performance.utilizationRate} className="h-2" />
            </div>
          </CardContent>
        </Card>

        {/* Earnings */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <DollarSign className="h-5 w-5 text-primary" />
              Earnings & Revenue
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between py-2 border-b border-border">
              <span className="text-muted-foreground">Total Earnings</span>
              <span className="font-semibold text-success">{formatCurrency(vehicle.earnings.total)}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-border">
              <span className="text-muted-foreground">This Month</span>
              <span className="font-semibold">{formatCurrency(vehicle.earnings.thisMonth)}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-border">
              <span className="text-muted-foreground">Last Month</span>
              <span className="font-semibold">{formatCurrency(vehicle.earnings.lastMonth)}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-border">
              <span className="text-muted-foreground">Avg. Per Trip</span>
              <span className="font-semibold">{formatCurrency(vehicle.earnings.avgPerTrip)}</span>
            </div>
            <div className="pt-3">
              <div className="p-3 rounded-lg bg-success/10 border border-success/20">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-success" />
                  <span className="text-sm font-medium text-success">
                    {vehicle.earnings.thisMonth > vehicle.earnings.lastMonth ? "+" : ""}
                    {((vehicle.earnings.thisMonth - vehicle.earnings.lastMonth) / vehicle.earnings.lastMonth * 100).toFixed(0)}% vs last month
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Maintenance Status */}
        <Card className="md:col-span-2 xl:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Wrench className="h-5 w-5 text-primary" />
              Maintenance
            </CardTitle>
            <CardDescription>Health score and service history</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Health Score */}
            <div className="flex items-center gap-6">
              <div className={`text-4xl font-bold ${getHealthColor(vehicle.maintenance.healthScore)}`}>
                {vehicle.maintenance.healthScore}%
              </div>
              <div className="flex-1">
                <Progress 
                  value={vehicle.maintenance.healthScore} 
                  className="h-3"
                />
                <p className="text-sm text-muted-foreground mt-2">
                  {vehicle.maintenance.healthScore >= 80 
                    ? "Vehicle is in excellent condition" 
                    : vehicle.maintenance.healthScore >= 60 
                    ? "Some maintenance may be needed soon"
                    : "Urgent maintenance required"}
                </p>
              </div>
            </div>

            {/* Upcoming Maintenance */}
            {vehicle.maintenance.upcoming && (
              <div className={`p-4 rounded-lg border-l-4 ${
                vehicle.maintenance.upcoming.date === "Immediate" 
                  ? "border-l-destructive bg-destructive/5" 
                  : "border-l-warning bg-warning/5"
              }`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {vehicle.maintenance.upcoming.date === "Immediate" ? (
                      <AlertTriangle className="h-5 w-5 text-destructive" />
                    ) : (
                      <Clock className="h-5 w-5 text-warning" />
                    )}
                    <div>
                      <p className="font-semibold">{vehicle.maintenance.upcoming.name}</p>
                      <p className="text-sm text-muted-foreground">{vehicle.maintenance.upcoming.date}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold">{formatCurrency(vehicle.maintenance.upcoming.cost)}</p>
                    <Button size="sm" variant={vehicle.maintenance.upcoming.date === "Immediate" ? "destructive" : "outline"} className="mt-2">
                      Schedule
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {/* Service History */}
            <div className="space-y-3">
              <h4 className="font-semibold text-sm text-muted-foreground uppercase tracking-wide">Service History</h4>
              {vehicle.maintenance.history.map((service, idx) => (
                <div key={idx} className="flex items-center justify-between py-3 border-b border-border last:border-0">
                  <div className="flex items-center gap-3">
                    <CheckCircle className="h-4 w-4 text-success" />
                    <div>
                      <p className="font-medium">{service.name}</p>
                      <p className="text-xs text-muted-foreground">{service.date}</p>
                    </div>
                  </div>
                  <span className="text-muted-foreground">
                    {service.cost === 0 ? "Free" : formatCurrency(service.cost)}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Quick Stats */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-primary" />
              Quick Stats
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="p-4 rounded-lg bg-primary/10 text-center">
                <Car className="h-5 w-5 mx-auto text-primary mb-2" />
                <p className="text-xl font-bold">{vehicle.performance.totalTrips}</p>
                <p className="text-xs text-muted-foreground">Trips</p>
              </div>
              <div className="p-4 rounded-lg bg-success/10 text-center">
                <DollarSign className="h-5 w-5 mx-auto text-success mb-2" />
                <p className="text-xl font-bold">{formatCurrency(vehicle.earnings.avgPerTrip)}</p>
                <p className="text-xs text-muted-foreground">Avg/Trip</p>
              </div>
              <div className="p-4 rounded-lg bg-warning/10 text-center">
                <Star className="h-5 w-5 mx-auto text-warning mb-2" />
                <p className="text-xl font-bold">{vehicle.performance.avgRating}</p>
                <p className="text-xs text-muted-foreground">Rating</p>
              </div>
              <div className="p-4 rounded-lg bg-chart-4/10 text-center">
                <Calendar className="h-5 w-5 mx-auto mb-2" style={{ color: 'hsl(var(--chart-4))' }} />
                <p className="text-xl font-bold">{vehicle.performance.utilizationRate}%</p>
                <p className="text-xs text-muted-foreground">Utilization</p>
              </div>
            </div>
            
            <Button className="w-full gap-2 mt-4" variant="outline">
              View Full Report
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="mx-auto max-w-[2000px] space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Vehicle Details</h1>
          <p className="text-sm text-muted-foreground">Detailed specifications and performance data</p>
        </div>

        <Tabs defaultValue="tesla-3" className="w-full">
          <TabsList className="w-full flex flex-wrap h-auto gap-1 p-1 bg-muted/50">
            {vehiclesData.map((vehicle) => (
              <TabsTrigger 
                key={vehicle.id} 
                value={vehicle.id}
                className="flex-1 min-w-[120px] data-[state=active]:bg-background"
              >
                {vehicle.name}
              </TabsTrigger>
            ))}
          </TabsList>

          {vehiclesData.map((vehicle) => (
            <TabsContent key={vehicle.id} value={vehicle.id}>
              {renderVehicleContent(vehicle)}
            </TabsContent>
          ))}
        </Tabs>
      </div>
    </div>
  );
};

export default VehicleDetails;
