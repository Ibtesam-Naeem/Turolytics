// ========================================
// DEMO DATA - Sample data for demo mode
// ========================================
// This file contains all mock/sample data used when viewing the app in demo mode.
// When authenticated, replace this with real data from your backend.

export const demoKPIs = {
  totalRevenue: "$24,580",
  totalRevenueTrend: "+12.5% from last month",
  activeVehicles: "8",
  activeVehiclesTrend: "2 currently on trips",
  upcomingTrips: "12",
  upcomingTripsTrend: "+3 this week",
  bankBalance: "$42,150",
  bankBalanceTrend: "+8.2% this month",
  averageRating: "4.8",
  averageRatingTrend: "127 total reviews",
};

export const demoUpcomingTrips = [
  { id: "1", vehicleName: "Mercedes C-Class", guestName: "Michael Brown", pickupLocation: "San Diego Airport (SAN)", dropoffLocation: "La Jolla, CA", earnings: 420, kmsAllowed: 350, startDate: "Tomorrow, 9:00 AM" },
  { id: "2", vehicleName: "Tesla Model Y", guestName: "Sarah Johnson", pickupLocation: "Oakland, CA", dropoffLocation: "Napa Valley, CA", earnings: 560, kmsAllowed: 450, startDate: "Nov 21, 2:00 PM" },
  { id: "3", vehicleName: "Audi A4", guestName: "David Lee", pickupLocation: "San Jose, CA", dropoffLocation: "San Francisco Airport (SFO)", earnings: 290, kmsAllowed: 200, startDate: "Nov 23, 11:00 AM" },
  { id: "4", vehicleName: "BMW 5 Series", guestName: "Alex Martinez", pickupLocation: "Los Angeles, CA", dropoffLocation: "Beverly Hills, CA", earnings: 380, kmsAllowed: 300, startDate: "Dec 1, 10:30 AM" },
  { id: "5", vehicleName: "Ford Mustang", guestName: "Jennifer Adams", pickupLocation: "San Francisco, CA", dropoffLocation: "Monterey, CA", earnings: 520, kmsAllowed: 400, startDate: "Dec 3, 1:00 PM" },
  { id: "6", vehicleName: "Range Rover Sport", guestName: "Chris Taylor", pickupLocation: "San Diego, CA", dropoffLocation: "Palm Springs, CA", earnings: 650, kmsAllowed: 350, startDate: "Dec 5, 8:00 AM" },
  { id: "7", vehicleName: "Porsche 911", guestName: "Nicole Kim", pickupLocation: "Oakland, CA", dropoffLocation: "Lake Tahoe, CA", earnings: 890, kmsAllowed: 500, startDate: "Dec 7, 6:00 AM" },
  { id: "8", vehicleName: "Volvo XC90", guestName: "Daniel Park", pickupLocation: "San Jose, CA", dropoffLocation: "Carmel, CA", earnings: 440, kmsAllowed: 280, startDate: "Dec 10, 3:00 PM" },
];

export const demoCurrentTrips = [
  { vehicleName: "Tesla Model 3", year: 2024, guestName: "John Smith", location: "San Francisco, CA", coordinates: "37.7749°N, 122.4194°W", fuelPercent: 85, speed: 45, status: "Moving" as const, kmsDriven: 280, kmsAllowed: 400, earnings: 245, topSpeed: 68, flags: { rapidAcceleration: 3, hardBraking: 1, engineLight: false } },
  { vehicleName: "BMW X5", year: 2023, guestName: "Emma Wilson", location: "Los Angeles, CA", coordinates: "34.0522°N, 118.2437°W", fuelPercent: 62, speed: 0, status: "Parked" as const, kmsDriven: 150, kmsAllowed: 500, earnings: 380, topSpeed: 52, flags: { rapidAcceleration: 0, hardBraking: 0, engineLight: true } },
  { vehicleName: "Audi A6", year: 2024, guestName: "Michael Chen", location: "Seattle, WA", coordinates: "47.6062°N, 122.3321°W", fuelPercent: 78, speed: 55, status: "Moving" as const, kmsDriven: 320, kmsAllowed: 600, earnings: 495, topSpeed: 72, flags: { rapidAcceleration: 2, hardBraking: 0, engineLight: false } },
  { vehicleName: "Mercedes E-Class", year: 2023, guestName: "Sarah Mitchell", location: "Portland, OR", coordinates: "45.5152°N, 122.6784°W", fuelPercent: 45, speed: 0, status: "Parked" as const, kmsDriven: 420, kmsAllowed: 450, earnings: 585, topSpeed: 65, flags: { rapidAcceleration: 1, hardBraking: 2, engineLight: false } },
  { vehicleName: "Toyota Camry", year: 2024, guestName: "James Rodriguez", location: "Phoenix, AZ", coordinates: "33.4484°N, 112.0740°W", fuelPercent: 92, speed: 38, status: "Moving" as const, kmsDriven: 95, kmsAllowed: 350, earnings: 175, topSpeed: 55, flags: { rapidAcceleration: 0, hardBraking: 0, engineLight: false } },
  { vehicleName: "Honda Accord", year: 2023, guestName: "Lisa Wang", location: "Denver, CO", coordinates: "39.7392°N, 104.9903°W", fuelPercent: 68, speed: 48, status: "Moving" as const, kmsDriven: 225, kmsAllowed: 500, earnings: 340, topSpeed: 61, flags: { rapidAcceleration: 4, hardBraking: 3, engineLight: false } },
  { vehicleName: "Lexus RX350", year: 2024, guestName: "Robert Thompson", location: "Austin, TX", coordinates: "30.2672°N, 97.7431°W", fuelPercent: 31, speed: 0, status: "Parked" as const, kmsDriven: 380, kmsAllowed: 400, earnings: 520, topSpeed: 58, flags: { rapidAcceleration: 0, hardBraking: 1, engineLight: true } },
  { vehicleName: "Porsche Cayenne", year: 2024, guestName: "Amanda Foster", location: "Miami, FL", coordinates: "25.7617°N, 80.1918°W", fuelPercent: 88, speed: 62, status: "Moving" as const, kmsDriven: 145, kmsAllowed: 550, earnings: 680, topSpeed: 75, flags: { rapidAcceleration: 5, hardBraking: 2, engineLight: false } },
];

// Demo data for Live Operations Strip
export const demoLiveOperations = {
  tripsToday: 5,
  milesDrivenToday: 342,
  paymentsReceivedToday: 1250,
  newBookingsToday: 3,
  checkoutsToday: 2,
};

// Demo data for charts
export const demoRevenueData = [
  { month: "Jan", revenue: 12500 },
  { month: "Feb", revenue: 14200 },
  { month: "Mar", revenue: 13800 },
  { month: "Apr", revenue: 15600 },
  { month: "May", revenue: 17200 },
  { month: "Jun", revenue: 16800 },
  { month: "Jul", revenue: 19500 },
  { month: "Aug", revenue: 21200 },
  { month: "Sep", revenue: 20100 },
  { month: "Oct", revenue: 22800 },
  { month: "Nov", revenue: 24580 },
  { month: "Dec", revenue: 23500 },
];

export const demoUtilizationData = [
  { month: "Jan", utilization: 72 },
  { month: "Feb", utilization: 78 },
  { month: "Mar", utilization: 75 },
  { month: "Apr", utilization: 82 },
  { month: "May", utilization: 88 },
  { month: "Jun", utilization: 85 },
  { month: "Jul", utilization: 92 },
  { month: "Aug", utilization: 95 },
  { month: "Sep", utilization: 89 },
  { month: "Oct", utilization: 91 },
  { month: "Nov", utilization: 87 },
  { month: "Dec", utilization: 84 },
];

// Demo data for Fleet Health
export const demoFleetHealth = {
  maintenanceRequired: [
    { vehicleName: "BMW X5", issue: "Oil change overdue", severity: "warning" as const },
    { vehicleName: "Lexus RX350", issue: "Engine light on", severity: "error" as const },
  ],
  lowFuel: [
    { vehicleName: "Lexus RX350", fuelPercent: 31 },
    { vehicleName: "Mercedes E-Class", fuelPercent: 45 },
  ],
  lateReturns: [],
};

// Demo data for Upcoming Maintenance
export const demoUpcomingMaintenance = [
  { id: "1", vehicleName: "Tesla Model 3", maintenanceType: "Tire Rotation", dueDate: "In 3 days" },
  { id: "2", vehicleName: "BMW X5", maintenanceType: "Oil Change", dueDate: "In 5 days" },
  { id: "3", vehicleName: "Audi A6", maintenanceType: "Brake Inspection", dueDate: "In 1 week" },
  { id: "4", vehicleName: "Fleet", maintenanceType: "Insurance Renewal", dueDate: "In 2 weeks" },
];

// Demo data for Activity Feed
export const demoActivityFeed = [
  { id: "1", type: "trip_started" as const, message: "Tesla Model 3 trip started", time: "2 min ago" },
  { id: "2", type: "payment_received" as const, message: "Payment of $245 received", time: "15 min ago" },
  { id: "3", type: "booking_confirmed" as const, message: "New booking for Mercedes C-Class", time: "1 hour ago" },
  { id: "4", type: "trip_ended" as const, message: "Honda Accord trip completed", time: "2 hours ago" },
  { id: "5", type: "review_received" as const, message: "5-star review from John Smith", time: "3 hours ago" },
];

// Demo data for Performance Leaderboard
export const demoPerformanceLeaderboard = [
  { rank: 1, vehicleName: "Porsche Cayenne", revenue: 4250, trips: 12 },
  { rank: 2, vehicleName: "Tesla Model 3", revenue: 3890, trips: 15 },
  { rank: 3, vehicleName: "BMW X5", revenue: 3450, trips: 10 },
  { rank: 4, vehicleName: "Mercedes E-Class", revenue: 3200, trips: 11 },
  { rank: 5, vehicleName: "Audi A6", revenue: 2980, trips: 9 },
];

// Demo data for Calendar events
export const demoCalendarEvents = [
  { date: new Date(2024, 11, 15), title: "Tesla Model 3 - Trip Start", type: "trip" as const },
  { date: new Date(2024, 11, 17), title: "BMW X5 - Maintenance", type: "maintenance" as const },
  { date: new Date(2024, 11, 20), title: "Mercedes - Trip End", type: "trip" as const },
  { date: new Date(2024, 11, 22), title: "Insurance Renewal", type: "important" as const },
];
