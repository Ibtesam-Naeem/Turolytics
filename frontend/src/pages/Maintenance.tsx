import { Wrench, AlertTriangle, CheckCircle, Clock, Calendar, DollarSign, Car, TrendingUp, ChevronRight } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";

const vehicleData = [
  {
    name: "BMW X5",
    status: "urgent",
    maintenanceScore: 45,
    items: [
      { 
        type: "urgent",
        issue: "Engine Light On", 
        details: "Check engine light activated. Vehicle off-road.",
        dueDate: "Immediate",
        cost: 450,
        reported: "Today, 2:30 PM"
      },
      { 
        type: "scheduled",
        issue: "Oil Change Due", 
        details: "Regular oil change scheduled",
        dueDate: "Dec 5, 2025",
        cost: 180,
        reported: "1 week ago"
      },
    ],
    recentService: { service: "Tire Rotation", date: "Nov 10, 2025", cost: 180 },
    totalSpent: 1240,
  },
  {
    name: "Mercedes C-Class",
    status: "urgent",
    maintenanceScore: 52,
    items: [
      { 
        type: "urgent",
        issue: "Brake System Alert", 
        details: "ABS warning light detected. Requires immediate inspection.",
        dueDate: "Immediate",
        cost: 320,
        reported: "Today, 11:15 AM"
      },
      { 
        type: "scheduled",
        issue: "Annual Inspection", 
        details: "Annual safety inspection required",
        dueDate: "Dec 15, 2025",
        cost: 150,
        reported: "2 weeks ago"
      },
    ],
    recentService: { service: "Tire Rotation", date: "Nov 8, 2025", cost: 85 },
    totalSpent: 865,
  },
  {
    name: "Tesla Model 3",
    status: "good",
    maintenanceScore: 92,
    items: [
      { 
        type: "scheduled",
        issue: "Tire Rotation", 
        details: "Regular tire rotation service scheduled",
        dueDate: "Dec 8, 2025",
        cost: 120,
        reported: "3 days ago"
      },
    ],
    recentService: { service: "Software Update", date: "Nov 12, 2025", cost: 0 },
    totalSpent: 320,
  },
  {
    name: "Audi A4",
    status: "scheduled",
    maintenanceScore: 78,
    items: [
      { 
        type: "scheduled",
        issue: "Fluid Top-up", 
        details: "Check and top up all fluids",
        dueDate: "Dec 3, 2025",
        cost: 85,
        reported: "5 days ago"
      },
    ],
    recentService: { service: "Brake Pad Replacement", date: "Nov 15, 2025", cost: 420 },
    totalSpent: 1580,
  },
  {
    name: "Tesla Model Y",
    status: "good",
    maintenanceScore: 88,
    items: [
      { 
        type: "scheduled",
        issue: "Battery Check", 
        details: "Routine battery health inspection",
        dueDate: "Dec 12, 2025",
        cost: 0,
        reported: "1 week ago"
      },
    ],
    recentService: { service: "Annual Inspection", date: "Nov 18, 2025", cost: 150 },
    totalSpent: 450,
  },
];

const Maintenance = () => {
  const totalUrgent = vehicleData.filter(v => v.status === "urgent").length;
  const totalScheduled = vehicleData.reduce((sum, v) => sum + v.items.filter(i => i.type === "scheduled").length, 0);
  const totalSpent = vehicleData.reduce((sum, v) => sum + v.totalSpent, 0);
  const avgMaintenanceScore = Math.round(vehicleData.reduce((sum, v) => sum + v.maintenanceScore, 0) / vehicleData.length);

  const getStatusColor = (status: string) => {
    switch(status) {
      case "urgent": return "text-destructive";
      case "scheduled": return "text-warning";
      case "good": return "text-success";
      default: return "text-muted-foreground";
    }
  };

  const getStatusBadge = (status: string) => {
    switch(status) {
      case "urgent": return <Badge variant="destructive">Urgent</Badge>;
      case "scheduled": return <Badge variant="secondary" className="bg-warning/20 text-warning border-warning/30">Scheduled</Badge>;
      case "good": return <Badge variant="outline" className="border-success text-success">Good</Badge>;
      default: return <Badge variant="outline">Unknown</Badge>;
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-success";
    if (score >= 60) return "text-warning";
    return "text-destructive";
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="mx-auto max-w-[2000px] space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Fleet Maintenance</h1>
            <p className="text-sm text-muted-foreground mt-1">Vehicle health and service schedules</p>
          </div>
          <Button className="gap-2">
            <Wrench className="h-4 w-4" />
            Schedule Service
          </Button>
        </div>

        {/* KPI Cards */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base font-medium text-muted-foreground">
                <AlertTriangle className="h-4 w-4" />
                Urgent Issues
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-foreground">{totalUrgent}</p>
              <p className="text-xs text-muted-foreground mt-1">Vehicles need attention</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base font-medium text-muted-foreground">
                <Clock className="h-4 w-4" />
                Scheduled Services
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-foreground">{totalScheduled}</p>
              <p className="text-xs text-muted-foreground mt-1">Next 30 days</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base font-medium text-muted-foreground">
                <TrendingUp className="h-4 w-4" />
                Fleet Health
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className={`text-3xl font-bold ${getScoreColor(avgMaintenanceScore)}`}>{avgMaintenanceScore}%</p>
              <p className="text-xs text-muted-foreground mt-1">Average score</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base font-medium text-muted-foreground">
                <DollarSign className="h-4 w-4" />
                Total Spent
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-foreground">${totalSpent}</p>
              <p className="text-xs text-muted-foreground mt-1">All time maintenance</p>
            </CardContent>
          </Card>
        </div>

        {/* Vehicle Cards */}
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-foreground">Vehicle Status</h2>
          
          {vehicleData.map((vehicle, idx) => (
            <Card key={idx} className="overflow-hidden hover:shadow-md transition-shadow">
              <CardHeader className="bg-muted/30">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-background rounded-lg">
                      <Car className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">{vehicle.name}</CardTitle>
                      <CardDescription className="flex items-center gap-2 mt-1">
                        {getStatusBadge(vehicle.status)}
                        <span className="text-xs">•</span>
                        <span className="text-xs">Total spent: ${vehicle.totalSpent}</span>
                      </CardDescription>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-muted-foreground">Health Score</p>
                    <p className={`text-2xl font-bold ${getScoreColor(vehicle.maintenanceScore)}`}>
                      {vehicle.maintenanceScore}%
                    </p>
                  </div>
                </div>
              </CardHeader>

              <CardContent className="pt-6">
                {/* Maintenance Items */}
                <div className="space-y-3 mb-6">
                  {vehicle.items.map((item, itemIdx) => (
                    <div 
                      key={itemIdx} 
                      className={`p-4 rounded-lg border-l-4 ${
                        item.type === "urgent" 
                          ? "border-l-destructive bg-destructive/5" 
                          : "border-l-warning bg-muted/50"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            {item.type === "urgent" ? (
                              <AlertTriangle className="h-4 w-4 text-destructive" />
                            ) : (
                              <Clock className="h-4 w-4 text-warning" />
                            )}
                            <p className="font-semibold text-foreground">{item.issue}</p>
                            {item.type === "urgent" && (
                              <Badge variant="destructive" className="text-xs">URGENT</Badge>
                            )}
                          </div>
                          <p className="text-sm text-muted-foreground mb-2">{item.details}</p>
                          <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            <span className="flex items-center gap-1">
                              <Calendar className="h-3 w-3" />
                              {item.dueDate}
                            </span>
                            <span>•</span>
                            <span className="font-medium text-foreground">
                              {item.cost === 0 ? "Free" : `$${item.cost}`}
                            </span>
                            <span>•</span>
                            <span>Reported {item.reported}</span>
                          </div>
                        </div>
                        <Button 
                          variant={item.type === "urgent" ? "destructive" : "outline"} 
                          size="sm"
                        >
                          {item.type === "urgent" ? "Schedule Now" : "View"}
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Recent Service */}
                <div className="pt-4 border-t border-border">
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <CheckCircle className="h-4 w-4 text-success" />
                      <span>Last Service: {vehicle.recentService.service}</span>
                    </div>
                    <div className="flex items-center gap-3 text-muted-foreground">
                      <span>{vehicle.recentService.date}</span>
                      <span>•</span>
                      <span className="font-medium text-foreground">
                        {vehicle.recentService.cost === 0 ? "Free" : `$${vehicle.recentService.cost}`}
                      </span>
                      <Button variant="ghost" size="sm" className="gap-1 h-8">
                        View History
                        <ChevronRight className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Maintenance;
