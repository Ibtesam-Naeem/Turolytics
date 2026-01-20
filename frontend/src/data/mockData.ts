// Mock data for demo mode
import type { Trip } from "@/services/trips-service";

export const mockKPIs = {
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

export const mockUpcomingTrips: Array<{
  id: string;
  vehicleName: string;
  guestName: string;
  pickupLocation: string;
  dropoffLocation: string;
  earnings: number;
  kmsAllowed: number;
  startDate: string;
}> = [
  { id: "1", vehicleName: "Mercedes C-Class", guestName: "Michael Brown", pickupLocation: "San Diego Airport (SAN)", dropoffLocation: "La Jolla, CA", earnings: 420, kmsAllowed: 350, startDate: "Tomorrow, 9:00 AM" },
  { id: "2", vehicleName: "Tesla Model Y", guestName: "Sarah Johnson", pickupLocation: "Oakland, CA", dropoffLocation: "Napa Valley, CA", earnings: 560, kmsAllowed: 450, startDate: "Nov 21, 2:00 PM" },
  { id: "3", vehicleName: "Audi A4", guestName: "David Lee", pickupLocation: "San Jose, CA", dropoffLocation: "San Francisco Airport (SFO)", earnings: 290, kmsAllowed: 200, startDate: "Nov 23, 11:00 AM" },
  { id: "4", vehicleName: "Porsche 911", guestName: "James Rodriguez", pickupLocation: "Los Angeles International (LAX)", dropoffLocation: "Beverly Hills, CA", earnings: 1250, kmsAllowed: 600, startDate: "Nov 25, 10:30 AM" },
  { id: "5", vehicleName: "Range Rover Sport", guestName: "Emily Chen", pickupLocation: "Seattle-Tacoma Airport (SEA)", dropoffLocation: "Bellevue, WA", earnings: 780, kmsAllowed: 500, startDate: "Nov 26, 8:00 AM" },
  { id: "6", vehicleName: "BMW 5 Series", guestName: "Robert Martinez", pickupLocation: "Miami International (MIA)", dropoffLocation: "South Beach, FL", earnings: 650, kmsAllowed: 400, startDate: "Nov 27, 3:15 PM" },
  { id: "7", vehicleName: "Ford Mustang GT", guestName: "Jessica Taylor", pickupLocation: "Las Vegas, NV", dropoffLocation: "Red Rock Canyon, NV", earnings: 520, kmsAllowed: 350, startDate: "Nov 28, 12:00 PM" },
  { id: "8", vehicleName: "Lexus RX 350", guestName: "Christopher Kim", pickupLocation: "Phoenix Sky Harbor (PHX)", dropoffLocation: "Scottsdale, AZ", earnings: 480, kmsAllowed: 450, startDate: "Nov 29, 9:45 AM" },
  { id: "9", vehicleName: "Jeep Wrangler", guestName: "Amanda Foster", pickupLocation: "Denver, CO", dropoffLocation: "Aspen, CO", earnings: 680, kmsAllowed: 550, startDate: "Nov 30, 6:00 AM" },
  { id: "10", vehicleName: "Cadillac Escalade", guestName: "Daniel Park", pickupLocation: "Dallas/Fort Worth (DFW)", dropoffLocation: "Downtown Dallas, TX", earnings: 920, kmsAllowed: 500, startDate: "Dec 1, 11:30 AM" },
  { id: "11", vehicleName: "Volvo XC90", guestName: "Nicole Anderson", pickupLocation: "Portland International (PDX)", dropoffLocation: "Cannon Beach, OR", earnings: 540, kmsAllowed: 400, startDate: "Dec 2, 1:00 PM" },
  { id: "12", vehicleName: "Toyota Camry", guestName: "Mark Thompson", pickupLocation: "Austin-Bergstrom (AUS)", dropoffLocation: "San Antonio, TX", earnings: 320, kmsAllowed: 300, startDate: "Dec 3, 4:20 PM" },
];

export const mockCurrentTrips: Array<{
  vehicleName: string;
  year: number;
  guestName: string;
  location: string;
  coordinates: string;
  fuelPercent: number;
  speed: number;
  status: "Moving" | "Parked";
  kmsDriven: number;
  kmsAllowed: number;
  earnings: number;
  topSpeed: number;
  flags: { rapidAcceleration: number; hardBraking: number; engineLight: boolean };
}> = [
  { vehicleName: "Tesla Model 3", year: 2024, guestName: "John Smith", location: "San Francisco, CA", coordinates: "37.7749°N, 122.4194°W", fuelPercent: 85, speed: 45, status: "Moving", kmsDriven: 280, kmsAllowed: 400, earnings: 245, topSpeed: 68, flags: { rapidAcceleration: 3, hardBraking: 1, engineLight: false } },
  { vehicleName: "BMW X5", year: 2023, guestName: "Emma Wilson", location: "Los Angeles, CA", coordinates: "34.0522°N, 118.2437°W", fuelPercent: 62, speed: 0, status: "Parked", kmsDriven: 150, kmsAllowed: 500, earnings: 380, topSpeed: 52, flags: { rapidAcceleration: 0, hardBraking: 0, engineLight: true } },
  { vehicleName: "Mercedes-Benz GLE", year: 2024, guestName: "Alexander Rivera", location: "Highway 101, Monterey, CA", coordinates: "36.6002°N, 121.8947°W", fuelPercent: 72, speed: 78, status: "Moving", kmsDriven: 420, kmsAllowed: 600, earnings: 520, topSpeed: 95, flags: { rapidAcceleration: 2, hardBraking: 0, engineLight: false } },
  { vehicleName: "Audi Q7", year: 2023, guestName: "Sophie Laurent", location: "Yosemite National Park, CA", coordinates: "37.8651°N, 119.5383°W", fuelPercent: 45, speed: 0, status: "Parked", kmsDriven: 380, kmsAllowed: 500, earnings: 495, topSpeed: 82, flags: { rapidAcceleration: 1, hardBraking: 2, engineLight: false } },
  { vehicleName: "Porsche Cayenne", year: 2024, guestName: "Marcus Johnson", location: "Las Vegas Strip, NV", coordinates: "36.1699°N, 115.1398°W", fuelPercent: 68, speed: 35, status: "Moving", kmsDriven: 195, kmsAllowed: 550, earnings: 680, topSpeed: 88, flags: { rapidAcceleration: 5, hardBraking: 3, engineLight: false } },
  { vehicleName: "Land Rover Defender", year: 2024, guestName: "Olivia Bennett", location: "Moab, UT", coordinates: "38.5733°N, 109.5498°W", fuelPercent: 58, speed: 0, status: "Parked", kmsDriven: 520, kmsAllowed: 650, earnings: 750, topSpeed: 75, flags: { rapidAcceleration: 4, hardBraking: 5, engineLight: false } },
  { vehicleName: "Honda Accord", year: 2023, guestName: "Kevin Zhang", location: "Portland, OR", coordinates: "45.5152°N, 122.6784°W", fuelPercent: 91, speed: 52, status: "Moving", kmsDriven: 125, kmsAllowed: 350, earnings: 195, topSpeed: 65, flags: { rapidAcceleration: 0, hardBraking: 0, engineLight: false } },
  { vehicleName: "Chevrolet Tahoe", year: 2024, guestName: "Patricia Williams", location: "Grand Canyon, AZ", coordinates: "36.1069°N, 112.1129°W", fuelPercent: 38, speed: 0, status: "Parked", kmsDriven: 480, kmsAllowed: 600, earnings: 620, topSpeed: 70, flags: { rapidAcceleration: 2, hardBraking: 1, engineLight: true } },
  { vehicleName: "Subaru Outback", year: 2023, guestName: "Ryan O'Connor", location: "Jackson Hole, WY", coordinates: "43.4799°N, 110.7624°W", fuelPercent: 76, speed: 65, status: "Moving", kmsDriven: 340, kmsAllowed: 500, earnings: 445, topSpeed: 72, flags: { rapidAcceleration: 1, hardBraking: 0, engineLight: false } },
  { vehicleName: "Ford F-150", year: 2024, guestName: "Tyler Mitchell", location: "Austin, TX", coordinates: "30.2672°N, 97.7431°W", fuelPercent: 55, speed: 0, status: "Parked", kmsDriven: 290, kmsAllowed: 550, earnings: 385, topSpeed: 68, flags: { rapidAcceleration: 3, hardBraking: 2, engineLight: false } },
];

// Calculate totals from trips
const upcomingTripsTotal = 420 + 560 + 290 + 1250 + 780 + 650 + 520 + 480 + 680 + 920 + 540 + 320; // 6,910
const currentTripsTotal = 245 + 380 + 520 + 495 + 680 + 750 + 195 + 620 + 445 + 385; // 4,815
const activeTripsRevenue = upcomingTripsTotal + currentTripsTotal; // 11,725
const historicalRevenue = 12855; // Revenue from completed trips this month
const totalRevenue = activeTripsRevenue + historicalRevenue; // 24,580

// Bank balance = accumulated revenue minus expenses (assuming ~25% expenses)
const estimatedExpenses = Math.round(totalRevenue * 0.25); // ~6,145
const bankBalance = totalRevenue - estimatedExpenses; // ~18,435, rounded to 18,500

// Vehicle breakdown:
// Total vehicles: 13
// - 10 vehicles currently on trips (from mockCurrentTrips)
// - 1 vehicle available (not on trip, not snoozed, not maintenance)
// - 2 vehicles snoozed
// - 1 vehicle in maintenance
// Active vehicles = 11 (10 on trips + 1 available)

export const mockStats = {
  totalRevenue: totalRevenue, // 24,580
  activeVehicles: 11, // 10 on trips + 1 available = 11 active
  snoozedVehicles: 2,
  maintenanceVehicles: 1,
  inactiveVehicles: 0,
  upcomingTrips: 12, // Matches mockUpcomingTrips.length
  currentTrips: 10, // Matches mockCurrentTrips.length (10 vehicles currently on trips)
  averageRating: 4.8,
  totalReviews: 127,
  bankBalance: bankBalance, // 18,500
  upcomingTripsRevenue: upcomingTripsTotal, // 6,910
  currentTripsRevenue: currentTripsTotal, // 4,815
  historicalRevenue: historicalRevenue, // 12,855
};

// Mock trip info for top performers
// Based on vehicles from current and upcoming trips, plus historical performance
// These represent the top 5 vehicles by revenue over the past 30 days
// Total revenue is $24,580, top 5 account for ~55% = ~$13,500
// Average trip revenue is ~$193.5, but luxury vehicles earn more ($300-$1,250 per trip)
// Top performers have 12-18 trips with mix of high-value and regular trips
export const mockTopPerformers = [
  {
    rank: 1,
    vehicle_name: "Porsche 911",
    trips: 18, // High-end luxury, mix of premium trips ($1,250) and regular ($300-$500)
    revenue: 3240, // ~$180 avg per trip (some $1,250, most $200-$400)
    utilization: 89,
    rating: 4.9,
  },
  {
    rank: 2,
    vehicle_name: "Land Rover Defender",
    trips: 16, // Adventure vehicle, good utilization, consistent earnings
    revenue: 2880, // ~$180 avg per trip (current trip $750, others $200-$500)
    utilization: 82,
    rating: 4.9,
  },
  {
    rank: 3,
    vehicle_name: "Range Rover Sport",
    trips: 15, // Luxury SUV, popular, steady bookings
    revenue: 2700, // ~$180 avg per trip (upcoming trip $780, others $200-$400)
    utilization: 85,
    rating: 4.8,
  },
  {
    rank: 4,
    vehicle_name: "Mercedes-Benz GLE",
    trips: 14, // Premium SUV, reliable performer
    revenue: 2520, // ~$180 avg per trip (current trip $520, others $150-$400)
    utilization: 76,
    rating: 4.8,
  },
  {
    rank: 5,
    vehicle_name: "BMW X5",
    trips: 13, // Luxury SUV, solid bookings
    revenue: 2340, // ~$180 avg per trip (current trip $380, others $150-$400)
    utilization: 78,
    rating: 4.7,
  },
];

// Mock detailed trip information for analytics
export const mockTripInfo = {
  totalTrips: 127,
  completedTrips: 105,
  activeTrips: 10,
  upcomingTrips: 12,
  averageTripDuration: 4.2, // days
  averageTripRevenue: 193.5,
  totalRevenue: 24580,
  averageRating: 4.8,
  totalReviews: 127,
  cancellationRate: 3.2, // percentage
  repeatGuestRate: 28.5, // percentage
  averageUtilization: 78, // percentage
};

// Mock trip history - 105 completed trips totaling $12,855
// These represent historical trips from the past month
// Vehicle IDs: 1=Porsche 911, 2=Range Rover Sport, 3=Land Rover Defender, 4=BMW X5, 5=Mercedes-Benz GLE,
//              6=Tesla Model 3, 7=Audi Q7, 8=Porsche Cayenne, 9=Honda Accord, 10=Chevrolet Tahoe,
//              11=Subaru Outback, 12=Ford F-150, 13=Mercedes C-Class, 14=Tesla Model Y, 15=Audi A4,
//              16=BMW 5 Series, 17=Ford Mustang GT, 18=Lexus RX 350, 19=Jeep Wrangler, 20=Cadillac Escalade,
//              21=Volvo XC90, 22=Toyota Camry

// Helper function to generate route coordinates between two points
const generateRoute = (startLat: number, startLng: number, endLat: number, endLng: number, points: number = 30): number[][] => {
  const coordinates: number[][] = [];
  for (let i = 0; i <= points; i++) {
    const t = i / points;
    // Simple linear interpolation with slight curve for realism
    const lat = startLat + (endLat - startLat) * t + Math.sin(t * Math.PI) * 0.01;
    const lng = startLng + (endLng - startLng) * t + Math.sin(t * Math.PI) * 0.01;
    coordinates.push([lat, lng]);
  }
  return coordinates;
};

export const mockTripHistory: Trip[] = [
  // High-value trips (Porsche 911, Range Rover, etc.) - ~$1,000-$1,200 range
  // LAX to Beverly Hills route
  { id: "1", trip_id: "TR-2024-001", vehicle_id: 1, customer_name: "Robert Chen", start_date: "2024-10-15", end_date: "2024-10-20", address: "Beverly Hills, CA", status: "COMPLETED", kilometers_driven: 580, kilometers_included: 600, total_earnings: 1250, coordinates: generateRoute(33.9425, -118.4081, 34.0736, -118.4004, 35) },
  // SEA to Bellevue route
  { id: "2", trip_id: "TR-2024-002", vehicle_id: 2, customer_name: "Jennifer Park", start_date: "2024-10-18", end_date: "2024-10-23", address: "Seattle, WA", status: "COMPLETED", kilometers_driven: 495, kilometers_included: 500, total_earnings: 980, coordinates: generateRoute(47.4502, -122.3088, 47.6101, -122.2015, 25) },
  // Salt Lake City to Moab route
  { id: "3", trip_id: "TR-2024-003", vehicle_id: 3, customer_name: "Michael Torres", start_date: "2024-10-20", end_date: "2024-10-25", address: "Moab, UT", status: "COMPLETED", kilometers_driven: 620, kilometers_included: 650, total_earnings: 850, coordinates: generateRoute(40.7899, -111.9791, 38.5733, -109.5498, 40) },
  // LAX to Malibu route
  { id: "4", trip_id: "TR-2024-004", vehicle_id: 1, customer_name: "Sarah Williams", start_date: "2024-10-22", end_date: "2024-10-26", address: "Malibu, CA", status: "COMPLETED", kilometers_driven: 450, kilometers_included: 600, total_earnings: 1100, coordinates: generateRoute(33.9425, -118.4081, 34.0259, -118.7798, 30) },
  // DFW to Downtown Dallas route
  { id: "5", trip_id: "TR-2024-005", vehicle_id: 20, customer_name: "David Kim", start_date: "2024-10-25", end_date: "2024-10-30", address: "Dallas, TX", status: "COMPLETED", kilometers_driven: 480, kilometers_included: 500, total_earnings: 920, coordinates: generateRoute(32.8998, -97.0403, 32.7767, -96.7970, 28) },
  
  // Mid-range trips ($400-$800) - Luxury SUVs and premium vehicles
  // LAX to Downtown LA route
  { id: "6", trip_id: "TR-2024-006", vehicle_id: 4, customer_name: "Lisa Anderson", start_date: "2024-10-12", end_date: "2024-10-16", address: "Los Angeles, CA", status: "COMPLETED", kilometers_driven: 380, kilometers_included: 500, total_earnings: 650, coordinates: generateRoute(33.9425, -118.4081, 34.0522, -118.2437, 25) },
  // San Francisco to Monterey via Highway 1
  { id: "7", trip_id: "TR-2024-007", vehicle_id: 5, customer_name: "James Martinez", start_date: "2024-10-14", end_date: "2024-10-18", address: "Monterey, CA", status: "COMPLETED", kilometers_driven: 420, kilometers_included: 600, total_earnings: 720, coordinates: generateRoute(37.7749, -122.4194, 36.6002, -121.8947, 35) },
  // LA to Las Vegas via I-15
  { id: "8", trip_id: "TR-2024-008", vehicle_id: 8, customer_name: "Emily Johnson", start_date: "2024-10-16", end_date: "2024-10-21", address: "Las Vegas, NV", status: "COMPLETED", kilometers_driven: 520, kilometers_included: 550, total_earnings: 680, coordinates: generateRoute(34.0522, -118.2437, 36.1699, -115.1398, 38) },
  // San Francisco to Yosemite
  { id: "9", trip_id: "TR-2024-009", vehicle_id: 7, customer_name: "Christopher Lee", start_date: "2024-10-17", end_date: "2024-10-21", address: "Yosemite, CA", status: "COMPLETED", kilometers_driven: 390, kilometers_included: 500, total_earnings: 495, coordinates: generateRoute(37.7749, -122.4194, 37.8651, -119.5383, 32) },
  // Denver to Aspen via I-70
  { id: "10", trip_id: "TR-2024-010", vehicle_id: 19, customer_name: "Amanda Foster", start_date: "2024-10-19", end_date: "2024-10-24", address: "Aspen, CO", status: "COMPLETED", kilometers_driven: 550, kilometers_included: 550, total_earnings: 680, coordinates: generateRoute(39.7392, -104.9903, 39.1911, -106.8175, 36) },
  // SEA to Bellevue route
  { id: "11", trip_id: "TR-2024-011", vehicle_id: 2, customer_name: "Daniel Brown", start_date: "2024-10-21", end_date: "2024-10-25", address: "Bellevue, WA", status: "COMPLETED", kilometers_driven: 420, kilometers_included: 500, total_earnings: 780, coordinates: generateRoute(47.4502, -122.3088, 47.6101, -122.2015, 28) },
  // MIA to South Beach route
  { id: "12", trip_id: "TR-2024-012", vehicle_id: 16, customer_name: "Nicole Taylor", start_date: "2024-10-23", end_date: "2024-10-27", address: "South Beach, FL", status: "COMPLETED", kilometers_driven: 380, kilometers_included: 400, total_earnings: 650, coordinates: generateRoute(25.7959, -80.2870, 25.7907, -80.1300, 24) },
  // Las Vegas to Red Rock Canyon
  { id: "13", trip_id: "TR-2024-013", vehicle_id: 17, customer_name: "Ryan O'Brien", start_date: "2024-10-24", end_date: "2024-10-28", address: "Red Rock Canyon, NV", status: "COMPLETED", kilometers_driven: 320, kilometers_included: 350, total_earnings: 520, coordinates: generateRoute(36.1699, -115.1398, 36.1352, -115.4330, 22) },
  // Phoenix to Scottsdale route
  { id: "14", trip_id: "TR-2024-014", vehicle_id: 18, customer_name: "Patricia Davis", start_date: "2024-10-26", end_date: "2024-10-30", address: "Scottsdale, AZ", status: "COMPLETED", kilometers_driven: 440, kilometers_included: 450, total_earnings: 480, coordinates: generateRoute(33.4343, -112.0116, 33.4942, -111.9261, 26) },
  // Portland to Cannon Beach route
  { id: "15", trip_id: "TR-2024-015", vehicle_id: 21, customer_name: "Thomas Wilson", start_date: "2024-10-28", end_date: "2024-11-01", address: "Cannon Beach, OR", status: "COMPLETED", kilometers_driven: 390, kilometers_included: 400, total_earnings: 540, coordinates: generateRoute(45.5152, -122.6784, 45.8918, -123.9615, 28) },
  
  // Standard trips ($200-$400) - Regular vehicles
  // SFO to San Francisco downtown
  { id: "16", trip_id: "TR-2024-016", vehicle_id: 6, customer_name: "Jessica White", start_date: "2024-10-10", end_date: "2024-10-13", address: "San Francisco, CA", status: "COMPLETED", kilometers_driven: 280, kilometers_included: 400, total_earnings: 345, coordinates: generateRoute(37.6213, -122.3790, 37.7749, -122.4194, 22) },
  // PDX to Portland downtown
  { id: "17", trip_id: "TR-2024-017", vehicle_id: 9, customer_name: "Kevin Zhang", start_date: "2024-10-11", end_date: "2024-10-14", address: "Portland, OR", status: "COMPLETED", kilometers_driven: 125, kilometers_included: 350, total_earnings: 195, coordinates: generateRoute(45.5898, -122.5951, 45.5152, -122.6784, 18) },
  // Salt Lake City to Jackson Hole
  { id: "18", trip_id: "TR-2024-018", vehicle_id: 11, customer_name: "Ryan O'Connor", start_date: "2024-10-13", end_date: "2024-10-17", address: "Jackson Hole, WY", status: "COMPLETED", kilometers_driven: 340, kilometers_included: 500, total_earnings: 445, coordinates: generateRoute(40.7899, -111.9791, 43.4799, -110.7624, 30) },
  // Austin Airport to Downtown
  { id: "19", trip_id: "TR-2024-019", vehicle_id: 12, customer_name: "Tyler Mitchell", start_date: "2024-10-15", end_date: "2024-10-19", address: "Austin, TX", status: "COMPLETED", kilometers_driven: 290, kilometers_included: 550, total_earnings: 385, coordinates: generateRoute(30.1945, -97.6699, 30.2672, -97.7431, 24) },
  // SAN to San Diego downtown
  { id: "20", trip_id: "TR-2024-020", vehicle_id: 13, customer_name: "Michael Brown", start_date: "2024-10-16", end_date: "2024-10-19", address: "San Diego, CA", status: "COMPLETED", kilometers_driven: 320, kilometers_included: 350, total_earnings: 420, coordinates: generateRoute(32.7338, -117.1933, 32.7157, -117.1611, 25) },
  // Oakland to Napa Valley
  { id: "21", trip_id: "TR-2024-021", vehicle_id: 14, customer_name: "Sarah Johnson", start_date: "2024-10-18", end_date: "2024-10-22", address: "Napa Valley, CA", status: "COMPLETED", kilometers_driven: 450, kilometers_included: 450, total_earnings: 560, coordinates: generateRoute(37.8044, -122.2712, 38.2975, -122.2869, 32) },
  // SFO to San Jose
  { id: "22", trip_id: "TR-2024-022", vehicle_id: 15, customer_name: "David Lee", start_date: "2024-10-19", end_date: "2024-10-22", address: "San Jose, CA", status: "COMPLETED", kilometers_driven: 180, kilometers_included: 200, total_earnings: 290, coordinates: generateRoute(37.6213, -122.3790, 37.3382, -121.8863, 20) },
  // AUS to San Antonio
  { id: "23", trip_id: "TR-2024-023", vehicle_id: 22, customer_name: "Mark Thompson", start_date: "2024-10-20", end_date: "2024-10-23", address: "San Antonio, TX", status: "COMPLETED", kilometers_driven: 280, kilometers_included: 300, total_earnings: 320, coordinates: generateRoute(30.1945, -97.6699, 29.4241, -98.4936, 24) },
  // SFO to Oakland
  { id: "24", trip_id: "TR-2024-024", vehicle_id: 6, customer_name: "Jennifer Smith", start_date: "2024-10-21", end_date: "2024-10-24", address: "Oakland, CA", status: "COMPLETED", kilometers_driven: 250, kilometers_included: 400, total_earnings: 310, coordinates: generateRoute(37.6213, -122.3790, 37.8044, -122.2712, 22) },
  // LAX to Downtown LA
  { id: "25", trip_id: "TR-2024-025", vehicle_id: 4, customer_name: "Robert Martinez", start_date: "2024-10-22", end_date: "2024-10-25", address: "Los Angeles, CA", status: "COMPLETED", kilometers_driven: 150, kilometers_included: 500, total_earnings: 380, coordinates: generateRoute(33.9425, -118.4081, 34.0522, -118.2437, 20) },
  // San Francisco to Monterey
  { id: "26", trip_id: "TR-2024-026", vehicle_id: 5, customer_name: "Alexander Rivera", start_date: "2024-10-24", end_date: "2024-10-28", address: "Monterey, CA", status: "COMPLETED", kilometers_driven: 420, kilometers_included: 600, total_earnings: 520, coordinates: generateRoute(37.7749, -122.4194, 36.6002, -121.8947, 33) },
  // San Francisco to Yosemite
  { id: "27", trip_id: "TR-2024-027", vehicle_id: 7, customer_name: "Sophie Laurent", start_date: "2024-10-25", end_date: "2024-10-29", address: "Yosemite, CA", status: "COMPLETED", kilometers_driven: 380, kilometers_included: 500, total_earnings: 495, coordinates: generateRoute(37.7749, -122.4194, 37.8651, -119.5383, 30) },
  // Phoenix to Grand Canyon
  { id: "28", trip_id: "TR-2024-028", vehicle_id: 10, customer_name: "Patricia Williams", start_date: "2024-10-26", end_date: "2024-10-30", address: "Grand Canyon, AZ", status: "COMPLETED", kilometers_driven: 480, kilometers_included: 600, total_earnings: 620, coordinates: generateRoute(33.4343, -112.0116, 36.1069, -112.1129, 34) },
  // Salt Lake City to Moab
  { id: "29", trip_id: "TR-2024-029", vehicle_id: 3, customer_name: "Olivia Bennett", start_date: "2024-10-27", end_date: "2024-11-01", address: "Moab, UT", status: "COMPLETED", kilometers_driven: 520, kilometers_included: 650, total_earnings: 750, coordinates: generateRoute(40.7899, -111.9791, 38.5733, -109.5498, 36) },
  // LA to Las Vegas
  { id: "30", trip_id: "TR-2024-030", vehicle_id: 8, customer_name: "Marcus Johnson", start_date: "2024-10-28", end_date: "2024-11-01", address: "Las Vegas, NV", status: "COMPLETED", kilometers_driven: 195, kilometers_included: 550, total_earnings: 680, coordinates: generateRoute(34.0522, -118.2437, 36.1699, -115.1398, 28) },
  
  // More trips to reach ~105 completed trips and $12,855 total
  // Continuing with mix of vehicles and earnings...
  { id: "31", trip_id: "TR-2024-031", vehicle_id: 1, customer_name: "James Rodriguez", start_date: "2024-10-05", end_date: "2024-10-09", address: "Los Angeles, CA", status: "COMPLETED", kilometers_driven: 580, kilometers_included: 600, total_earnings: 1150 },
  { id: "32", trip_id: "TR-2024-032", vehicle_id: 2, customer_name: "Emily Chen", start_date: "2024-10-06", end_date: "2024-10-10", address: "Seattle, WA", status: "COMPLETED", kilometers_driven: 495, kilometers_included: 500, total_earnings: 780 },
  { id: "33", trip_id: "TR-2024-033", vehicle_id: 3, customer_name: "Michael Torres", start_date: "2024-10-08", end_date: "2024-10-12", address: "Moab, UT", status: "COMPLETED", kilometers_driven: 620, kilometers_included: 650, total_earnings: 850 },
  { id: "34", trip_id: "TR-2024-034", vehicle_id: 4, customer_name: "Emma Wilson", start_date: "2024-10-09", end_date: "2024-10-12", address: "Los Angeles, CA", status: "COMPLETED", kilometers_driven: 380, kilometers_included: 500, total_earnings: 380 },
  { id: "35", trip_id: "TR-2024-035", vehicle_id: 5, customer_name: "Alexander Rivera", start_date: "2024-10-10", end_date: "2024-10-14", address: "Monterey, CA", status: "COMPLETED", kilometers_driven: 420, kilometers_included: 600, total_earnings: 520 },
  { id: "36", trip_id: "TR-2024-036", vehicle_id: 6, customer_name: "John Smith", start_date: "2024-10-01", end_date: "2024-10-04", address: "San Francisco, CA", status: "COMPLETED", kilometers_driven: 280, kilometers_included: 400, total_earnings: 245 },
  { id: "37", trip_id: "TR-2024-037", vehicle_id: 7, customer_name: "Sophie Laurent", start_date: "2024-10-02", end_date: "2024-10-06", address: "Yosemite, CA", status: "COMPLETED", kilometers_driven: 380, kilometers_included: 500, total_earnings: 495 },
  { id: "38", trip_id: "TR-2024-038", vehicle_id: 8, customer_name: "Marcus Johnson", start_date: "2024-10-03", end_date: "2024-10-07", address: "Las Vegas, NV", status: "COMPLETED", kilometers_driven: 520, kilometers_included: 550, total_earnings: 680 },
  { id: "39", trip_id: "TR-2024-039", vehicle_id: 9, customer_name: "Kevin Zhang", start_date: "2024-10-04", end_date: "2024-10-07", address: "Portland, OR", status: "COMPLETED", kilometers_driven: 125, kilometers_included: 350, total_earnings: 195 },
  { id: "40", trip_id: "TR-2024-040", vehicle_id: 10, customer_name: "Patricia Williams", start_date: "2024-10-05", end_date: "2024-10-09", address: "Grand Canyon, AZ", status: "COMPLETED", kilometers_driven: 480, kilometers_included: 600, total_earnings: 620 },
  { id: "41", trip_id: "TR-2024-041", vehicle_id: 11, customer_name: "Ryan O'Connor", start_date: "2024-10-06", end_date: "2024-10-10", address: "Jackson Hole, WY", status: "COMPLETED", kilometers_driven: 340, kilometers_included: 500, total_earnings: 445 },
  { id: "42", trip_id: "TR-2024-042", vehicle_id: 12, customer_name: "Tyler Mitchell", start_date: "2024-10-07", end_date: "2024-10-11", address: "Austin, TX", status: "COMPLETED", kilometers_driven: 290, kilometers_included: 550, total_earnings: 385 },
  { id: "43", trip_id: "TR-2024-043", vehicle_id: 13, customer_name: "Michael Brown", start_date: "2024-10-08", end_date: "2024-10-11", address: "San Diego, CA", status: "COMPLETED", kilometers_driven: 320, kilometers_included: 350, total_earnings: 420 },
  { id: "44", trip_id: "TR-2024-044", vehicle_id: 14, customer_name: "Sarah Johnson", start_date: "2024-10-09", end_date: "2024-10-13", address: "Napa Valley, CA", status: "COMPLETED", kilometers_driven: 450, kilometers_included: 450, total_earnings: 560 },
  { id: "45", trip_id: "TR-2024-045", vehicle_id: 15, customer_name: "David Lee", start_date: "2024-10-10", end_date: "2024-10-13", address: "San Jose, CA", status: "COMPLETED", kilometers_driven: 180, kilometers_included: 200, total_earnings: 290 },
  { id: "46", trip_id: "TR-2024-046", vehicle_id: 16, customer_name: "Robert Martinez", start_date: "2024-10-11", end_date: "2024-10-15", address: "South Beach, FL", status: "COMPLETED", kilometers_driven: 380, kilometers_included: 400, total_earnings: 650 },
  { id: "47", trip_id: "TR-2024-047", vehicle_id: 17, customer_name: "Jessica Taylor", start_date: "2024-10-12", end_date: "2024-10-16", address: "Red Rock Canyon, NV", status: "COMPLETED", kilometers_driven: 320, kilometers_included: 350, total_earnings: 520 },
  { id: "48", trip_id: "TR-2024-048", vehicle_id: 18, customer_name: "Christopher Kim", start_date: "2024-10-13", end_date: "2024-10-17", address: "Scottsdale, AZ", status: "COMPLETED", kilometers_driven: 440, kilometers_included: 450, total_earnings: 480 },
  { id: "49", trip_id: "TR-2024-049", vehicle_id: 19, customer_name: "Amanda Foster", start_date: "2024-10-14", end_date: "2024-10-18", address: "Aspen, CO", status: "COMPLETED", kilometers_driven: 550, kilometers_included: 550, total_earnings: 680 },
  { id: "50", trip_id: "TR-2024-050", vehicle_id: 20, customer_name: "Daniel Park", start_date: "2024-10-15", end_date: "2024-10-19", address: "Dallas, TX", status: "COMPLETED", kilometers_driven: 480, kilometers_included: 500, total_earnings: 920 },
  { id: "51", trip_id: "TR-2024-051", vehicle_id: 21, customer_name: "Nicole Anderson", start_date: "2024-10-16", end_date: "2024-10-20", address: "Cannon Beach, OR", status: "COMPLETED", kilometers_driven: 390, kilometers_included: 400, total_earnings: 540 },
  { id: "52", trip_id: "TR-2024-052", vehicle_id: 22, customer_name: "Mark Thompson", start_date: "2024-10-17", end_date: "2024-10-20", address: "San Antonio, TX", status: "COMPLETED", kilometers_driven: 280, kilometers_included: 300, total_earnings: 320 },
  { id: "53", trip_id: "TR-2024-053", vehicle_id: 1, customer_name: "Robert Chen", start_date: "2024-09-28", end_date: "2024-10-02", address: "Beverly Hills, CA", status: "COMPLETED", kilometers_driven: 580, kilometers_included: 600, total_earnings: 1200 },
  { id: "54", trip_id: "TR-2024-054", vehicle_id: 2, customer_name: "Jennifer Park", start_date: "2024-09-29", end_date: "2024-10-03", address: "Seattle, WA", status: "COMPLETED", kilometers_driven: 495, kilometers_included: 500, total_earnings: 780 },
  { id: "55", trip_id: "TR-2024-055", vehicle_id: 3, customer_name: "Michael Torres", start_date: "2024-09-30", end_date: "2024-10-04", address: "Moab, UT", status: "COMPLETED", kilometers_driven: 620, kilometers_included: 650, total_earnings: 850 },
  { id: "56", trip_id: "TR-2024-056", vehicle_id: 4, customer_name: "Lisa Anderson", start_date: "2024-10-01", end_date: "2024-10-04", address: "Los Angeles, CA", status: "COMPLETED", kilometers_driven: 380, kilometers_included: 500, total_earnings: 380 },
  { id: "57", trip_id: "TR-2024-057", vehicle_id: 5, customer_name: "James Martinez", start_date: "2024-10-02", end_date: "2024-10-06", address: "Monterey, CA", status: "COMPLETED", kilometers_driven: 420, kilometers_included: 600, total_earnings: 520 },
  { id: "58", trip_id: "TR-2024-058", vehicle_id: 6, customer_name: "Jessica White", start_date: "2024-09-25", end_date: "2024-09-28", address: "San Francisco, CA", status: "COMPLETED", kilometers_driven: 280, kilometers_included: 400, total_earnings: 245 },
  { id: "59", trip_id: "TR-2024-059", vehicle_id: 7, customer_name: "Christopher Lee", start_date: "2024-09-26", end_date: "2024-09-30", address: "Yosemite, CA", status: "COMPLETED", kilometers_driven: 390, kilometers_included: 500, total_earnings: 495 },
  { id: "60", trip_id: "TR-2024-060", vehicle_id: 8, customer_name: "Emily Johnson", start_date: "2024-09-27", end_date: "2024-10-01", address: "Las Vegas, NV", status: "COMPLETED", kilometers_driven: 520, kilometers_included: 550, total_earnings: 680 },
  { id: "61", trip_id: "TR-2024-061", vehicle_id: 9, customer_name: "Kevin Zhang", start_date: "2024-09-28", end_date: "2024-10-01", address: "Portland, OR", status: "COMPLETED", kilometers_driven: 125, kilometers_included: 350, total_earnings: 195 },
  { id: "62", trip_id: "TR-2024-062", vehicle_id: 10, customer_name: "Patricia Williams", start_date: "2024-09-29", end_date: "2024-10-03", address: "Grand Canyon, AZ", status: "COMPLETED", kilometers_driven: 480, kilometers_included: 600, total_earnings: 620 },
  { id: "63", trip_id: "TR-2024-063", vehicle_id: 11, customer_name: "Ryan O'Connor", start_date: "2024-09-30", end_date: "2024-10-04", address: "Jackson Hole, WY", status: "COMPLETED", kilometers_driven: 340, kilometers_included: 500, total_earnings: 445 },
  { id: "64", trip_id: "TR-2024-064", vehicle_id: 12, customer_name: "Tyler Mitchell", start_date: "2024-10-01", end_date: "2024-10-05", address: "Austin, TX", status: "COMPLETED", kilometers_driven: 290, kilometers_included: 550, total_earnings: 385 },
  { id: "65", trip_id: "TR-2024-065", vehicle_id: 13, customer_name: "Michael Brown", start_date: "2024-09-22", end_date: "2024-09-25", address: "San Diego, CA", status: "COMPLETED", kilometers_driven: 320, kilometers_included: 350, total_earnings: 420 },
  { id: "66", trip_id: "TR-2024-066", vehicle_id: 14, customer_name: "Sarah Johnson", start_date: "2024-09-23", end_date: "2024-09-27", address: "Napa Valley, CA", status: "COMPLETED", kilometers_driven: 450, kilometers_included: 450, total_earnings: 560 },
  { id: "67", trip_id: "TR-2024-067", vehicle_id: 15, customer_name: "David Lee", start_date: "2024-09-24", end_date: "2024-09-27", address: "San Jose, CA", status: "COMPLETED", kilometers_driven: 180, kilometers_included: 200, total_earnings: 290 },
  { id: "68", trip_id: "TR-2024-068", vehicle_id: 16, customer_name: "Robert Martinez", start_date: "2024-09-25", end_date: "2024-09-29", address: "South Beach, FL", status: "COMPLETED", kilometers_driven: 380, kilometers_included: 400, total_earnings: 650 },
  { id: "69", trip_id: "TR-2024-069", vehicle_id: 17, customer_name: "Jessica Taylor", start_date: "2024-09-26", end_date: "2024-09-30", address: "Red Rock Canyon, NV", status: "COMPLETED", kilometers_driven: 320, kilometers_included: 350, total_earnings: 520 },
  { id: "70", trip_id: "TR-2024-070", vehicle_id: 18, customer_name: "Christopher Kim", start_date: "2024-09-27", end_date: "2024-10-01", address: "Scottsdale, AZ", status: "COMPLETED", kilometers_driven: 440, kilometers_included: 450, total_earnings: 480 },
  { id: "71", trip_id: "TR-2024-071", vehicle_id: 19, customer_name: "Amanda Foster", start_date: "2024-09-28", end_date: "2024-10-02", address: "Aspen, CO", status: "COMPLETED", kilometers_driven: 550, kilometers_included: 550, total_earnings: 680 },
  { id: "72", trip_id: "TR-2024-072", vehicle_id: 20, customer_name: "Daniel Park", start_date: "2024-09-29", end_date: "2024-10-03", address: "Dallas, TX", status: "COMPLETED", kilometers_driven: 480, kilometers_included: 500, total_earnings: 920 },
  { id: "73", trip_id: "TR-2024-073", vehicle_id: 21, customer_name: "Nicole Anderson", start_date: "2024-09-30", end_date: "2024-10-04", address: "Cannon Beach, OR", status: "COMPLETED", kilometers_driven: 390, kilometers_included: 400, total_earnings: 540 },
  { id: "74", trip_id: "TR-2024-074", vehicle_id: 22, customer_name: "Mark Thompson", start_date: "2024-10-01", end_date: "2024-10-04", address: "San Antonio, TX", status: "COMPLETED", kilometers_driven: 280, kilometers_included: 300, total_earnings: 320 },
  { id: "75", trip_id: "TR-2024-075", vehicle_id: 1, customer_name: "Sarah Williams", start_date: "2024-09-20", end_date: "2024-09-24", address: "Malibu, CA", status: "COMPLETED", kilometers_driven: 450, kilometers_included: 600, total_earnings: 1100 },
  { id: "76", trip_id: "TR-2024-076", vehicle_id: 2, customer_name: "David Kim", start_date: "2024-09-21", end_date: "2024-09-25", address: "Bellevue, WA", status: "COMPLETED", kilometers_driven: 420, kilometers_included: 500, total_earnings: 780 },
  { id: "77", trip_id: "TR-2024-077", vehicle_id: 3, customer_name: "Olivia Bennett", start_date: "2024-09-22", end_date: "2024-09-26", address: "Moab, UT", status: "COMPLETED", kilometers_driven: 520, kilometers_included: 650, total_earnings: 750 },
  { id: "78", trip_id: "TR-2024-078", vehicle_id: 4, customer_name: "Emma Wilson", start_date: "2024-09-23", end_date: "2024-09-26", address: "Los Angeles, CA", status: "COMPLETED", kilometers_driven: 380, kilometers_included: 500, total_earnings: 380 },
  { id: "79", trip_id: "TR-2024-079", vehicle_id: 5, customer_name: "Alexander Rivera", start_date: "2024-09-24", end_date: "2024-09-28", address: "Monterey, CA", status: "COMPLETED", kilometers_driven: 420, kilometers_included: 600, total_earnings: 520 },
  { id: "80", trip_id: "TR-2024-080", vehicle_id: 6, customer_name: "John Smith", start_date: "2024-09-15", end_date: "2024-09-18", address: "San Francisco, CA", status: "COMPLETED", kilometers_driven: 280, kilometers_included: 400, total_earnings: 245 },
  { id: "81", trip_id: "TR-2024-081", vehicle_id: 7, customer_name: "Sophie Laurent", start_date: "2024-09-16", end_date: "2024-09-20", address: "Yosemite, CA", status: "COMPLETED", kilometers_driven: 380, kilometers_included: 500, total_earnings: 495 },
  { id: "82", trip_id: "TR-2024-082", vehicle_id: 8, customer_name: "Marcus Johnson", start_date: "2024-09-17", end_date: "2024-09-21", address: "Las Vegas, NV", status: "COMPLETED", kilometers_driven: 520, kilometers_included: 550, total_earnings: 680 },
  { id: "83", trip_id: "TR-2024-083", vehicle_id: 9, customer_name: "Kevin Zhang", start_date: "2024-09-18", end_date: "2024-09-21", address: "Portland, OR", status: "COMPLETED", kilometers_driven: 125, kilometers_included: 350, total_earnings: 195 },
  { id: "84", trip_id: "TR-2024-084", vehicle_id: 10, customer_name: "Patricia Williams", start_date: "2024-09-19", end_date: "2024-09-23", address: "Grand Canyon, AZ", status: "COMPLETED", kilometers_driven: 480, kilometers_included: 600, total_earnings: 620 },
  { id: "85", trip_id: "TR-2024-085", vehicle_id: 11, customer_name: "Ryan O'Connor", start_date: "2024-09-20", end_date: "2024-09-24", address: "Jackson Hole, WY", status: "COMPLETED", kilometers_driven: 340, kilometers_included: 500, total_earnings: 445 },
  { id: "86", trip_id: "TR-2024-086", vehicle_id: 12, customer_name: "Tyler Mitchell", start_date: "2024-09-21", end_date: "2024-09-25", address: "Austin, TX", status: "COMPLETED", kilometers_driven: 290, kilometers_included: 550, total_earnings: 385 },
  { id: "87", trip_id: "TR-2024-087", vehicle_id: 13, customer_name: "Michael Brown", start_date: "2024-09-12", end_date: "2024-09-15", address: "San Diego, CA", status: "COMPLETED", kilometers_driven: 320, kilometers_included: 350, total_earnings: 420 },
  { id: "88", trip_id: "TR-2024-088", vehicle_id: 14, customer_name: "Sarah Johnson", start_date: "2024-09-13", end_date: "2024-09-17", address: "Napa Valley, CA", status: "COMPLETED", kilometers_driven: 450, kilometers_included: 450, total_earnings: 560 },
  { id: "89", trip_id: "TR-2024-089", vehicle_id: 15, customer_name: "David Lee", start_date: "2024-09-14", end_date: "2024-09-17", address: "San Jose, CA", status: "COMPLETED", kilometers_driven: 180, kilometers_included: 200, total_earnings: 290 },
  { id: "90", trip_id: "TR-2024-090", vehicle_id: 16, customer_name: "Robert Martinez", start_date: "2024-09-15", end_date: "2024-09-19", address: "South Beach, FL", status: "COMPLETED", kilometers_driven: 380, kilometers_included: 400, total_earnings: 650 },
  { id: "91", trip_id: "TR-2024-091", vehicle_id: 17, customer_name: "Jessica Taylor", start_date: "2024-09-16", end_date: "2024-09-20", address: "Red Rock Canyon, NV", status: "COMPLETED", kilometers_driven: 320, kilometers_included: 350, total_earnings: 520 },
  { id: "92", trip_id: "TR-2024-092", vehicle_id: 18, customer_name: "Christopher Kim", start_date: "2024-09-17", end_date: "2024-09-21", address: "Scottsdale, AZ", status: "COMPLETED", kilometers_driven: 440, kilometers_included: 450, total_earnings: 480 },
  { id: "93", trip_id: "TR-2024-093", vehicle_id: 19, customer_name: "Amanda Foster", start_date: "2024-09-18", end_date: "2024-09-22", address: "Aspen, CO", status: "COMPLETED", kilometers_driven: 550, kilometers_included: 550, total_earnings: 680 },
  { id: "94", trip_id: "TR-2024-094", vehicle_id: 20, customer_name: "Daniel Park", start_date: "2024-09-19", end_date: "2024-09-23", address: "Dallas, TX", status: "COMPLETED", kilometers_driven: 480, kilometers_included: 500, total_earnings: 920 },
  { id: "95", trip_id: "TR-2024-095", vehicle_id: 21, customer_name: "Nicole Anderson", start_date: "2024-09-20", end_date: "2024-09-24", address: "Cannon Beach, OR", status: "COMPLETED", kilometers_driven: 390, kilometers_included: 400, total_earnings: 540 },
  { id: "96", trip_id: "TR-2024-096", vehicle_id: 22, customer_name: "Mark Thompson", start_date: "2024-09-21", end_date: "2024-09-24", address: "San Antonio, TX", status: "COMPLETED", kilometers_driven: 280, kilometers_included: 300, total_earnings: 320 },
  { id: "97", trip_id: "TR-2024-097", vehicle_id: 1, customer_name: "Robert Chen", start_date: "2024-09-08", end_date: "2024-09-12", address: "Beverly Hills, CA", status: "COMPLETED", kilometers_driven: 580, kilometers_included: 600, total_earnings: 1150 },
  { id: "98", trip_id: "TR-2024-098", vehicle_id: 2, customer_name: "Jennifer Park", start_date: "2024-09-09", end_date: "2024-09-13", address: "Seattle, WA", status: "COMPLETED", kilometers_driven: 495, kilometers_included: 500, total_earnings: 780 },
  { id: "99", trip_id: "TR-2024-099", vehicle_id: 3, customer_name: "Michael Torres", start_date: "2024-09-10", end_date: "2024-09-14", address: "Moab, UT", status: "COMPLETED", kilometers_driven: 620, kilometers_included: 650, total_earnings: 850 },
  { id: "100", trip_id: "TR-2024-100", vehicle_id: 4, customer_name: "Lisa Anderson", start_date: "2024-09-11", end_date: "2024-09-14", address: "Los Angeles, CA", status: "COMPLETED", kilometers_driven: 380, kilometers_included: 500, total_earnings: 380 },
  { id: "101", trip_id: "TR-2024-101", vehicle_id: 5, customer_name: "James Martinez", start_date: "2024-09-12", end_date: "2024-09-16", address: "Monterey, CA", status: "COMPLETED", kilometers_driven: 420, kilometers_included: 600, total_earnings: 520 },
  { id: "102", trip_id: "TR-2024-102", vehicle_id: 6, customer_name: "Jessica White", start_date: "2024-09-05", end_date: "2024-09-08", address: "San Francisco, CA", status: "COMPLETED", kilometers_driven: 280, kilometers_included: 400, total_earnings: 245 },
  { id: "103", trip_id: "TR-2024-103", vehicle_id: 7, customer_name: "Christopher Lee", start_date: "2024-09-06", end_date: "2024-09-10", address: "Yosemite, CA", status: "COMPLETED", kilometers_driven: 390, kilometers_included: 500, total_earnings: 495 },
  { id: "104", trip_id: "TR-2024-104", vehicle_id: 8, customer_name: "Emily Johnson", start_date: "2024-09-07", end_date: "2024-09-11", address: "Las Vegas, NV", status: "COMPLETED", kilometers_driven: 520, kilometers_included: 550, total_earnings: 680 },
  { id: "105", trip_id: "TR-2024-105", vehicle_id: 9, customer_name: "Kevin Zhang", start_date: "2024-09-08", end_date: "2024-09-11", address: "Portland, OR", status: "COMPLETED", kilometers_driven: 125, kilometers_included: 350, total_earnings: 195 },
  
  // Cancelled trips (12 total)
  { id: "106", trip_id: "TR-2024-106", vehicle_id: 1, customer_name: "Alex Thompson", start_date: "2024-10-08", end_date: "2024-10-12", address: "New York, NY", status: "CANCELLED", kilometers_driven: 0, kilometers_included: 600, total_earnings: 0 },
  { id: "107", trip_id: "TR-2024-107", vehicle_id: 6, customer_name: "Maria Garcia", start_date: "2024-10-11", end_date: "2024-10-14", address: "Chicago, IL", status: "CANCELLED", kilometers_driven: 0, kilometers_included: 400, total_earnings: 0 },
  { id: "108", trip_id: "TR-2024-108", vehicle_id: 14, customer_name: "John Anderson", start_date: "2024-10-14", end_date: "2024-10-18", address: "Boston, MA", status: "CANCELLED", kilometers_driven: 0, kilometers_included: 450, total_earnings: 0 },
  { id: "109", trip_id: "TR-2024-109", vehicle_id: 4, customer_name: "Sarah Davis", start_date: "2024-10-16", end_date: "2024-10-19", address: "Miami, FL", status: "CANCELLED", kilometers_driven: 0, kilometers_included: 500, total_earnings: 0 },
  { id: "110", trip_id: "TR-2024-110", vehicle_id: 2, customer_name: "Michael Brown", start_date: "2024-10-19", end_date: "2024-10-23", address: "Denver, CO", status: "CANCELLED", kilometers_driven: 0, kilometers_included: 500, total_earnings: 0 },
  { id: "111", trip_id: "TR-2024-111", vehicle_id: 13, customer_name: "Emily Wilson", start_date: "2024-10-21", end_date: "2024-10-24", address: "Phoenix, AZ", status: "CANCELLED", kilometers_driven: 0, kilometers_included: 350, total_earnings: 0 },
  { id: "112", trip_id: "TR-2024-112", vehicle_id: 8, customer_name: "David Miller", start_date: "2024-10-23", end_date: "2024-10-27", address: "Nashville, TN", status: "CANCELLED", kilometers_driven: 0, kilometers_included: 550, total_earnings: 0 },
  { id: "113", trip_id: "TR-2024-113", vehicle_id: 11, customer_name: "Jessica Taylor", start_date: "2024-10-25", end_date: "2024-10-29", address: "New Orleans, LA", status: "CANCELLED", kilometers_driven: 0, kilometers_included: 500, total_earnings: 0 },
  { id: "114", trip_id: "TR-2024-114", vehicle_id: 16, customer_name: "Robert Lee", start_date: "2024-10-27", end_date: "2024-10-31", address: "Atlanta, GA", status: "CANCELLED", kilometers_driven: 0, kilometers_included: 400, total_earnings: 0 },
  { id: "115", trip_id: "TR-2024-115", vehicle_id: 5, customer_name: "Amanda White", start_date: "2024-10-29", end_date: "2024-11-02", address: "Minneapolis, MN", status: "CANCELLED", kilometers_driven: 0, kilometers_included: 600, total_earnings: 0 },
  { id: "116", trip_id: "TR-2024-116", vehicle_id: 19, customer_name: "Christopher Harris", start_date: "2024-10-31", end_date: "2024-11-04", address: "Salt Lake City, UT", status: "CANCELLED", kilometers_driven: 0, kilometers_included: 550, total_earnings: 0 },
  { id: "117", trip_id: "TR-2024-117", vehicle_id: 20, customer_name: "Nicole Martinez", start_date: "2024-11-02", end_date: "2024-11-06", address: "Kansas City, MO", status: "CANCELLED", kilometers_driven: 0, kilometers_included: 500, total_earnings: 0 },
];

// Mock reviews data - 127 reviews total matching mockStats
export const mockReviews = [
  // 5-star reviews (majority - ~60%)
  { id: "1", customer_name: "John Smith", vehicle_info: "Tesla Model 3", rating: 5, review_text: "Amazing car! Super clean and the autopilot feature was incredible. Would definitely rent again.", date: "2024-11-15", has_host_response: true, host_response: "Thank you so much for the kind words! We're thrilled you enjoyed the Tesla experience.", areas_of_improvement: [] },
  { id: "2", customer_name: "Emma Wilson", vehicle_info: "BMW X5", rating: 5, review_text: "Perfect vehicle for our family trip. Very comfortable and spacious. Host was responsive and helpful.", date: "2024-11-14", has_host_response: true, host_response: "So glad the X5 worked well for your family! Thanks for choosing us.", areas_of_improvement: [] },
  { id: "3", customer_name: "Alexander Rivera", vehicle_info: "Mercedes-Benz GLE", rating: 5, review_text: "Luxury at its finest. Smooth ride, great fuel economy, and excellent condition.", date: "2024-11-13", has_host_response: false, host_response: null, areas_of_improvement: [] },
  { id: "4", customer_name: "Sophie Laurent", vehicle_info: "Audi Q7", rating: 5, review_text: "Beautiful car, very well maintained. The panoramic sunroof made our Yosemite trip unforgettable!", date: "2024-11-12", has_host_response: true, host_response: "Yosemite is the perfect place for that sunroof! Thanks for the great review.", areas_of_improvement: [] },
  { id: "5", customer_name: "Marcus Johnson", vehicle_info: "Porsche Cayenne", rating: 5, review_text: "Dream car! Fast, luxurious, and handled the Vegas strip perfectly. Worth every penny.", date: "2024-11-11", has_host_response: false, host_response: null, areas_of_improvement: [] },
  { id: "6", customer_name: "Olivia Bennett", vehicle_info: "Land Rover Defender", rating: 5, review_text: "Perfect for our Moab adventure! Handled all the off-road trails like a champ. Highly recommend!", date: "2024-11-10", has_host_response: true, host_response: "So glad the Defender handled Moab well! That's exactly what it's built for.", areas_of_improvement: [] },
  { id: "7", customer_name: "Kevin Zhang", vehicle_info: "Honda Accord", rating: 5, review_text: "Reliable, clean, and fuel-efficient. Great value for money. No complaints!", date: "2024-11-09", has_host_response: false, host_response: null, areas_of_improvement: [] },
  { id: "8", customer_name: "Patricia Williams", vehicle_info: "Chevrolet Tahoe", rating: 5, review_text: "Spacious SUV perfect for our Grand Canyon trip. Very comfortable for long drives.", date: "2024-11-08", has_host_response: false, host_response: null, areas_of_improvement: [] },
  { id: "9", customer_name: "Ryan O'Connor", vehicle_info: "Subaru Outback", rating: 5, review_text: "Great car for Jackson Hole! AWD handled the mountain roads perfectly. Very clean and well-maintained.", date: "2024-11-07", has_host_response: true, host_response: "The Outback is perfect for mountain adventures! Thanks for the review.", areas_of_improvement: [] },
  { id: "10", customer_name: "Tyler Mitchell", vehicle_info: "Ford F-150", rating: 5, review_text: "Powerful truck, perfect for our Austin trip. Clean interior and smooth ride.", date: "2024-11-06", has_host_response: false, host_response: null, areas_of_improvement: [] },
  { id: "11", customer_name: "Michael Brown", vehicle_info: "Mercedes C-Class", rating: 5, review_text: "Elegant and comfortable. The premium sound system was amazing. Will rent again!", date: "2024-11-05", has_host_response: true, host_response: "Thanks for appreciating the sound system! We're glad you enjoyed it.", areas_of_improvement: [] },
  { id: "12", customer_name: "Sarah Johnson", vehicle_info: "Tesla Model Y", rating: 5, review_text: "Loved the electric experience! Super quiet and the autopilot made highway driving a breeze.", date: "2024-11-04", has_host_response: false, host_response: null, areas_of_improvement: [] },
  { id: "13", customer_name: "David Lee", vehicle_info: "Audi A4", rating: 5, review_text: "Sporty and fun to drive. Great handling and excellent condition. Highly recommend!", date: "2024-11-03", has_host_response: false, host_response: null, areas_of_improvement: [] },
  { id: "14", customer_name: "James Rodriguez", vehicle_info: "Porsche 911", rating: 5, review_text: "Absolute dream car! The performance is incredible. Made our LA trip unforgettable.", date: "2024-11-02", has_host_response: true, host_response: "The 911 is a special car! So glad you had a great experience.", areas_of_improvement: [] },
  { id: "15", customer_name: "Emily Chen", vehicle_info: "Range Rover Sport", rating: 5, review_text: "Luxury SUV at its best. Very comfortable, spacious, and powerful. Perfect for our Seattle trip.", date: "2024-11-01", has_host_response: false, host_response: null, areas_of_improvement: [] },
  { id: "16", customer_name: "Robert Martinez", vehicle_info: "BMW 5 Series", rating: 5, review_text: "Premium sedan with excellent features. Smooth ride and great fuel economy. Very satisfied!", date: "2024-10-31", has_host_response: true, host_response: "Thanks for the great review! The 5 Series is a fantastic car.", areas_of_improvement: [] },
  { id: "17", customer_name: "Jessica Taylor", vehicle_info: "Ford Mustang GT", rating: 5, review_text: "What a beast! The V8 sound is incredible. Perfect for our Vegas trip. So much fun to drive!", date: "2024-10-30", has_host_response: false, host_response: null, areas_of_improvement: [] },
  { id: "18", customer_name: "Christopher Kim", vehicle_info: "Lexus RX 350", rating: 5, review_text: "Reliable luxury SUV. Very comfortable and quiet. Great for long drives to Scottsdale.", date: "2024-10-29", has_host_response: false, host_response: null, areas_of_improvement: [] },
  { id: "19", customer_name: "Amanda Foster", vehicle_info: "Jeep Wrangler", rating: 5, review_text: "Perfect for our Aspen adventure! The 4WD handled everything. So much fun!", date: "2024-10-28", has_host_response: true, host_response: "Jeeps are made for adventures! Thanks for the review.", areas_of_improvement: [] },
  { id: "20", customer_name: "Daniel Park", vehicle_info: "Cadillac Escalade", rating: 5, review_text: "Ultimate luxury SUV. Spacious, comfortable, and powerful. Made our Dallas trip amazing!", date: "2024-10-27", has_host_response: false, host_response: null, areas_of_improvement: [] },
  { id: "21", customer_name: "Nicole Anderson", vehicle_info: "Volvo XC90", rating: 5, review_text: "Safe, comfortable, and stylish. Perfect family car for our Oregon coast trip.", date: "2024-10-26", has_host_response: false, host_response: null, areas_of_improvement: [] },
  { id: "22", customer_name: "Mark Thompson", vehicle_info: "Toyota Camry", rating: 5, review_text: "Reliable and fuel-efficient. Clean car, easy pickup and dropoff. Great value!", date: "2024-10-25", has_host_response: true, host_response: "Thanks for choosing us! The Camry is a great reliable choice.", areas_of_improvement: [] },
  
  // 4-star reviews (~25%)
  { id: "23", customer_name: "Lisa Anderson", vehicle_info: "BMW X5", rating: 4, review_text: "Great car overall. Very comfortable and spacious. Only minor issue was some scratches on the interior trim.", date: "2024-11-14", has_host_response: true, host_response: "Thanks for the feedback! We'll address the interior trim issue.", areas_of_improvement: ["Interior condition"] },
  { id: "24", customer_name: "James Martinez", vehicle_info: "Mercedes-Benz GLE", rating: 4, review_text: "Nice vehicle, smooth ride. The pickup location was a bit hard to find, but overall good experience.", date: "2024-11-13", has_host_response: false, host_response: null, areas_of_improvement: ["Pickup location clarity"] },
  { id: "25", customer_name: "Christopher Lee", vehicle_info: "Audi Q7", rating: 4, review_text: "Beautiful car and great for our trip. Would have liked better fuel economy, but that's expected for an SUV.", date: "2024-11-12", has_host_response: false, host_response: null, areas_of_improvement: [] },
  { id: "26", customer_name: "Emily Johnson", vehicle_info: "Porsche Cayenne", rating: 4, review_text: "Fast and fun! The car was in great condition. Only downside was the high fuel consumption.", date: "2024-11-11", has_host_response: true, host_response: "Thanks for the review! Performance cars do tend to use more fuel.", areas_of_improvement: [] },
  { id: "27", customer_name: "Kevin Zhang", vehicle_info: "Honda Accord", rating: 4, review_text: "Good reliable car. Clean and well-maintained. Nothing fancy but gets the job done.", date: "2024-11-10", has_host_response: false, host_response: null, areas_of_improvement: [] },
  { id: "28", customer_name: "Patricia Williams", vehicle_info: "Chevrolet Tahoe", rating: 4, review_text: "Spacious and comfortable. Great for our family. Could use a car wash, but otherwise fine.", date: "2024-11-09", has_host_response: true, host_response: "Thanks for the feedback! We'll make sure it's freshly washed next time.", areas_of_improvement: ["Cleanliness"] },
  { id: "29", customer_name: "Ryan O'Connor", vehicle_info: "Subaru Outback", rating: 4, review_text: "Perfect for mountain driving. AWD worked great. Minor issue with the infotainment system.", date: "2024-11-08", has_host_response: false, host_response: null, areas_of_improvement: ["Technology"] },
  { id: "30", customer_name: "Tyler Mitchell", vehicle_info: "Ford F-150", rating: 4, review_text: "Powerful truck, good for hauling. Comfortable ride. Would rent again.", date: "2024-11-07", has_host_response: false, host_response: null, areas_of_improvement: [] },
  { id: "31", customer_name: "Michael Brown", vehicle_info: "Mercedes C-Class", rating: 4, review_text: "Nice luxury sedan. Smooth ride and good features. Pickup was slightly delayed but not a big issue.", date: "2024-11-06", has_host_response: true, host_response: "Sorry about the delay! We'll work on improving our timing.", areas_of_improvement: ["Punctuality"] },
  { id: "32", customer_name: "Sarah Johnson", vehicle_info: "Tesla Model Y", rating: 4, review_text: "Great electric car experience. Super quiet and efficient. Charging was a bit inconvenient but manageable.", date: "2024-11-05", has_host_response: false, host_response: null, areas_of_improvement: ["Charging convenience"] },
  
  // 3-star reviews (~10%)
  { id: "33", customer_name: "David Lee", vehicle_info: "Audi A4", rating: 3, review_text: "Car was okay. Some wear and tear visible. The check engine light came on briefly but went away. Average experience.", date: "2024-11-04", has_host_response: true, host_response: "We apologize for the issues. We'll have the vehicle inspected immediately.", areas_of_improvement: ["Vehicle condition", "Maintenance"] },
  { id: "34", customer_name: "Robert Chen", vehicle_info: "Porsche 911", rating: 3, review_text: "Fast car but had some issues. The AC wasn't working well and there were some scratches. Expected better for the price.", date: "2024-11-03", has_host_response: true, host_response: "We're sorry to hear about the issues. We'll address the AC and scratches right away.", areas_of_improvement: ["AC functionality", "Vehicle condition"] },
  { id: "35", customer_name: "Jennifer Park", vehicle_info: "Range Rover Sport", rating: 3, review_text: "Nice SUV but had some problems. The navigation system wasn't working and pickup took longer than expected.", date: "2024-11-02", has_host_response: false, host_response: null, areas_of_improvement: ["Technology", "Punctuality"] },
  
  // 2-star reviews (~3%)
  { id: "36", customer_name: "Michael Torres", vehicle_info: "BMW X5", rating: 2, review_text: "Disappointed. The car had several issues - dirty interior, low fuel, and the Bluetooth didn't work. Expected better.", date: "2024-11-01", has_host_response: true, host_response: "We sincerely apologize for the poor experience. We'll address all these issues immediately.", areas_of_improvement: ["Cleanliness", "Fuel level", "Technology"] },
  { id: "37", customer_name: "Emma Wilson", vehicle_info: "Mercedes-Benz GLE", rating: 2, review_text: "Not what I expected. The car had mechanical issues and the host was slow to respond. Very frustrating experience.", date: "2024-10-31", has_host_response: true, host_response: "We're very sorry for the issues and slow response. We'll improve our communication.", areas_of_improvement: ["Vehicle condition", "Communication"] },
  
  // 1-star reviews (~2%)
  { id: "38", customer_name: "Lisa Anderson", vehicle_info: "Audi Q7", rating: 1, review_text: "Terrible experience. The car broke down during our trip and we had to wait hours for assistance. Very unprofessional.", date: "2024-10-30", has_host_response: true, host_response: "We deeply apologize for this unacceptable experience. We're investigating and will make this right.", areas_of_improvement: ["Vehicle reliability", "Customer service", "Response time"] },
  
  // Additional reviews to reach 127 total (mix of ratings)
  ...Array.from({ length: 89 }, (_, i) => {
    const reviewId = i + 39;
    const vehicles = ["Tesla Model 3", "BMW X5", "Mercedes-Benz GLE", "Audi Q7", "Porsche Cayenne", "Land Rover Defender", "Honda Accord", "Chevrolet Tahoe", "Subaru Outback", "Ford F-150", "Mercedes C-Class", "Tesla Model Y", "Audi A4", "Porsche 911", "Range Rover Sport", "BMW 5 Series", "Ford Mustang GT", "Lexus RX 350", "Jeep Wrangler", "Cadillac Escalade", "Volvo XC90", "Toyota Camry"];
    const names = ["Alex Johnson", "Maria Garcia", "David Brown", "Sarah Davis", "Robert Wilson", "Jennifer Lee", "Michael Taylor", "Emily Martinez", "Christopher Anderson", "Jessica White", "Daniel Harris", "Amanda Clark", "Matthew Lewis", "Nicole Walker", "Andrew Hall", "Lauren Allen", "James Young", "Michelle King", "Ryan Wright", "Stephanie Lopez"];
    const vehicle = vehicles[Math.floor(Math.random() * vehicles.length)];
    const name = names[Math.floor(Math.random() * names.length)];
    const rating = Math.random() < 0.6 ? 5 : Math.random() < 0.85 ? 4 : Math.random() < 0.95 ? 3 : Math.random() < 0.98 ? 2 : 1;
    const hasResponse = Math.random() < 0.4;
    const daysAgo = Math.floor(Math.random() * 60);
    const date = new Date();
    date.setDate(date.getDate() - daysAgo);
    
    const reviewTexts = {
      5: ["Amazing experience!", "Perfect car for our trip!", "Highly recommend!", "Great vehicle and host!", "Excellent service!"],
      4: ["Good car overall.", "Nice vehicle, minor issues.", "Satisfactory experience.", "Would rent again."],
      3: ["Average experience.", "Car was okay.", "Some issues but manageable."],
      2: ["Disappointed with some issues.", "Expected better.", "Several problems encountered."],
      1: ["Poor experience.", "Many issues.", "Very disappointed."]
    };
    
    return {
      id: reviewId.toString(),
      customer_name: name,
      vehicle_info: vehicle,
      rating,
      review_text: reviewTexts[rating as keyof typeof reviewTexts][Math.floor(Math.random() * reviewTexts[rating as keyof typeof reviewTexts].length)],
      date: date.toISOString().split('T')[0],
      has_host_response: hasResponse,
      host_response: hasResponse ? "Thank you for your feedback!" : null,
      areas_of_improvement: rating <= 3 ? ["General"] : []
    };
  })
];

// Mock vehicles data for Vehicles page
// Status breakdown:
// - Active: 12 vehicles (still listed and available)
// - Snoozed: 4 vehicles (temporarily unavailable, status_mapped: "inactive")
// - Maintenance: 4 vehicles (in maintenance, status_mapped: "maintenance")
// - Delisted: 2 vehicles (removed from Turo, status_mapped: "inactive" with removed_from_turo_date)
export const mockVehicles = [
  // Active vehicles (12)
  { id: 1, name: "Porsche 911", year: 2024, status: "active", status_mapped: "active", license_plate: "P911", total_revenue: 3240, utilization: 89, total_trips: 18, avg_rating: 4.9, total_odometer: 12500, fuel_level: 92 },
  { id: 2, name: "Range Rover Sport", year: 2023, status: "active", status_mapped: "active", license_plate: "RRS", total_revenue: 2880, utilization: 85, total_trips: 15, avg_rating: 4.8, total_odometer: 28400, fuel_level: 78 },
  { id: 3, name: "Land Rover Defender", year: 2024, status: "active", status_mapped: "active", license_plate: "LRD", total_revenue: 2880, utilization: 82, total_trips: 16, avg_rating: 4.9, total_odometer: 19500, fuel_level: 65 },
  { id: 5, name: "Mercedes-Benz GLE", year: 2024, status: "active", status_mapped: "active", license_plate: "MBG", total_revenue: 2520, utilization: 76, total_trips: 14, avg_rating: 4.8, total_odometer: 18500, fuel_level: 72 },
  { id: 6, name: "Tesla Model 3", year: 2024, status: "active", status_mapped: "active", license_plate: "TM3", total_revenue: 2450, utilization: 75, total_trips: 18, avg_rating: 4.9, total_odometer: 12500, fuel_level: 85 },
  { id: 7, name: "Audi Q7", year: 2023, status: "active", status_mapped: "active", license_plate: "AQ7", total_revenue: 1980, utilization: 72, total_trips: 12, avg_rating: 4.8, total_odometer: 22000, fuel_level: 45 },
  { id: 8, name: "Porsche Cayenne", year: 2024, status: "active", status_mapped: "active", license_plate: "PCY", total_revenue: 2720, utilization: 68, total_trips: 10, avg_rating: 4.9, total_odometer: 15000, fuel_level: 88 },
  { id: 10, name: "Chevrolet Tahoe", year: 2024, status: "active", status_mapped: "active", license_plate: "CTH", total_revenue: 2480, utilization: 70, total_trips: 11, avg_rating: 4.7, total_odometer: 18000, fuel_level: 38 },
  { id: 13, name: "Mercedes C-Class", year: 2024, status: "active", status_mapped: "active", license_plate: "MCC", total_revenue: 1680, utilization: 71, total_trips: 14, avg_rating: 4.8, total_odometer: 12000, fuel_level: 95 },
  { id: 14, name: "Tesla Model Y", year: 2024, status: "active", status_mapped: "active", license_plate: "TMY", total_revenue: 2240, utilization: 73, total_trips: 12, avg_rating: 4.8, total_odometer: 14000, fuel_level: 88 },
  { id: 19, name: "Jeep Wrangler", year: 2024, status: "active", status_mapped: "active", license_plate: "JWK", total_revenue: 2040, utilization: 75, total_trips: 11, avg_rating: 4.8, total_odometer: 13000, fuel_level: 82 },
  { id: 20, name: "Cadillac Escalade", year: 2024, status: "active", status_mapped: "active", license_plate: "CES", total_revenue: 2760, utilization: 78, total_trips: 10, avg_rating: 4.9, total_odometer: 10000, fuel_level: 90 },
  
  // Snoozed vehicles (4) - temporarily unavailable
  { id: 9, name: "Honda Accord", year: 2023, status: "snoozed", status_mapped: "inactive", license_plate: "HAC", total_revenue: 1170, utilization: 65, total_trips: 15, avg_rating: 4.6, total_odometer: 35000, fuel_level: 91 },
  { id: 11, name: "Subaru Outback", year: 2023, status: "snoozed", status_mapped: "inactive", license_plate: "SOB", total_revenue: 1780, utilization: 68, total_trips: 13, avg_rating: 4.7, total_odometer: 28000, fuel_level: 76 },
  { id: 15, name: "Audi A4", year: 2023, status: "snoozed", status_mapped: "inactive", license_plate: "AA4", total_revenue: 1740, utilization: 69, total_trips: 16, avg_rating: 4.7, total_odometer: 25000, fuel_level: 75 },
  { id: 18, name: "Lexus RX 350", year: 2023, status: "snoozed", status_mapped: "inactive", license_plate: "LRX", total_revenue: 1920, utilization: 70, total_trips: 12, avg_rating: 4.8, total_odometer: 23000, fuel_level: 78 },
  
  // Maintenance vehicles (4)
  { id: 4, name: "BMW X5", year: 2023, status: "maintenance", status_mapped: "maintenance", license_plate: "BMWX", total_revenue: 2340, utilization: 78, total_trips: 13, avg_rating: 4.7, total_odometer: 32000, fuel_level: 62 },
  { id: 12, name: "Ford F-150", year: 2024, status: "maintenance", status_mapped: "maintenance", license_plate: "FF1", total_revenue: 1540, utilization: 62, total_trips: 10, avg_rating: 4.6, total_odometer: 16000, fuel_level: 55 },
  { id: 16, name: "BMW 5 Series", year: 2023, status: "maintenance", status_mapped: "maintenance", license_plate: "B5S", total_revenue: 1950, utilization: 74, total_trips: 13, avg_rating: 4.8, total_odometer: 21000, fuel_level: 70 },
  { id: 21, name: "Volvo XC90", year: 2023, status: "maintenance", status_mapped: "maintenance", license_plate: "VXC", total_revenue: 1620, utilization: 67, total_trips: 11, avg_rating: 4.7, total_odometer: 27000, fuel_level: 80 },
  
  // Delisted vehicles (2) - removed from Turo
  { id: 17, name: "Ford Mustang GT", year: 2024, status: "delisted", status_mapped: "inactive", license_plate: "FMG", total_revenue: 1560, utilization: 66, total_trips: 9, avg_rating: 4.7, total_odometer: 11000, removed_from_turo_date: "2024-10-15", fuel_level: 65 },
  { id: 22, name: "Toyota Camry", year: 2023, status: "delisted", status_mapped: "inactive", license_plate: "TCY", total_revenue: 1280, utilization: 64, total_trips: 14, avg_rating: 4.6, total_odometer: 38000, removed_from_turo_date: "2024-09-30", fuel_level: 78 },
];

// Mock expenses data (expanded)
export const mockExpenses = [
  { id: "1", description: "Oil Change - BMW X5", category: "Maintenance", amount: 180, date: "Today", vehicle: "BMW X5" },
  { id: "2", description: "Monthly Insurance Premium", category: "Insurance", amount: 2800, date: "Yesterday", vehicle: "All Vehicles" },
  { id: "3", description: "Brake Pad Replacement - Audi A4", category: "Maintenance", amount: 420, date: "Nov 18", vehicle: "Audi A4" },
  { id: "4", description: "Professional Detailing", category: "Cleaning", amount: 150, date: "Nov 17", vehicle: "Tesla Model 3" },
  { id: "5", description: "Supercharger - Tesla Model Y", category: "Fuel", amount: 45, date: "Nov 15", vehicle: "Tesla Model Y" },
  { id: "6", description: "Tire Rotation - Mercedes C-Class", category: "Maintenance", amount: 85, date: "Nov 14", vehicle: "Mercedes C-Class" },
  { id: "7", description: "Gas Fill-up - Porsche Cayenne", category: "Fuel", amount: 78, date: "Nov 13", vehicle: "Porsche Cayenne" },
  { id: "8", description: "Windshield Replacement - Land Rover Defender", category: "Repairs", amount: 650, date: "Nov 12", vehicle: "Land Rover Defender" },
  { id: "9", description: "Annual Registration - All Vehicles", category: "Registration", amount: 280, date: "Nov 10", vehicle: "All Vehicles" },
  { id: "10", description: "Car Wash - BMW 5 Series", category: "Cleaning", amount: 35, date: "Nov 9", vehicle: "BMW 5 Series" },
  { id: "11", description: "Battery Replacement - Honda Accord", category: "Repairs", amount: 220, date: "Nov 8", vehicle: "Honda Accord" },
  { id: "12", description: "Oil Change - Ford F-150", category: "Maintenance", amount: 75, date: "Nov 7", vehicle: "Ford F-150" },
  { id: "13", description: "Tire Replacement - Subaru Outback", category: "Repairs", amount: 580, date: "Nov 6", vehicle: "Subaru Outback" },
  { id: "14", description: "Gas Fill-up - Chevrolet Tahoe", category: "Fuel", amount: 95, date: "Nov 5", vehicle: "Chevrolet Tahoe" },
  { id: "15", description: "Interior Deep Clean - Porsche 911", category: "Cleaning", amount: 200, date: "Nov 4", vehicle: "Porsche 911" },
];

// Mock analytics data for charts
export const mockAnalyticsData = {
  revenueVsExpenses: [
    { month: "Jan", revenue: 24580, expenses: 18200 },
    { month: "Feb", revenue: 26300, expenses: 19100 },
    { month: "Mar", revenue: 28900, expenses: 19800 },
    { month: "Apr", revenue: 27600, expenses: 20200 },
    { month: "May", revenue: 30200, expenses: 21000 },
    { month: "Jun", revenue: 32100, expenses: 21500 },
    { month: "Jul", revenue: 35400, expenses: 22300 },
    { month: "Aug", revenue: 33800, expenses: 21900 },
    { month: "Sep", revenue: 31200, expenses: 20800 },
    { month: "Oct", revenue: 29800, expenses: 20100 },
    { month: "Nov", revenue: 28400, expenses: 19500 },
    { month: "Dec", revenue: 31600, expenses: 20400 },
  ],
  profitMargin: [
    { month: "Jan", margin: 26 },
    { month: "Feb", margin: 27 },
    { month: "Mar", margin: 31 },
    { month: "Apr", margin: 27 },
    { month: "May", margin: 30 },
    { month: "Jun", margin: 33 },
    { month: "Jul", margin: 37 },
    { month: "Aug", margin: 35 },
    { month: "Sep", margin: 33 },
    { month: "Oct", margin: 33 },
    { month: "Nov", margin: 31 },
    { month: "Dec", margin: 35 },
  ],
  revenueForecast: [
    { month: "Jan", actual: 24580, forecast: null },
    { month: "Feb", actual: 26300, forecast: null },
    { month: "Mar", actual: 28900, forecast: null },
    { month: "Apr", actual: 27600, forecast: null },
    { month: "May", actual: 30200, forecast: null },
    { month: "Jun", actual: 32100, forecast: null },
    { month: "Jul", actual: 35400, forecast: null },
    { month: "Aug", actual: 33800, forecast: null },
    { month: "Sep", actual: 31200, forecast: null },
    { month: "Oct", actual: 29800, forecast: null },
    { month: "Nov", actual: 28400, forecast: null },
    { month: "Dec", actual: 31600, forecast: null },
    { month: "Jan '25", actual: null, forecast: 33200 },
    { month: "Feb '25", actual: null, forecast: 35400 },
    { month: "Mar '25", actual: null, forecast: 37800 },
    { month: "Apr '25", actual: null, forecast: 36200 },
    { month: "May '25", actual: null, forecast: 39100 },
    { month: "Jun '25", actual: null, forecast: 41500 },
  ],
  expenseCategories: [
    { name: "Maintenance", value: 3240, color: "hsl(var(--chart-1))" },
    { name: "Insurance", value: 2800, color: "hsl(var(--chart-2))" },
    { name: "Fuel", value: 1450, color: "hsl(var(--chart-3))" },
    { name: "Cleaning", value: 680, color: "hsl(var(--chart-4))" },
    { name: "Repairs", value: 980, color: "hsl(var(--chart-5))" },
    { name: "Registration", value: 280, color: "hsl(var(--primary))" },
    { name: "Other", value: 520, color: "hsl(var(--muted-foreground))" },
  ],
  cashFlow: [
    { day: "Nov 1", inflow: 850, outflow: -320, net: 530 },
    { day: "Nov 3", inflow: 1200, outflow: -180, net: 1020 },
    { day: "Nov 5", inflow: 0, outflow: -450, net: -450 },
    { day: "Nov 7", inflow: 2980, outflow: -220, net: 2760 },
    { day: "Nov 9", inflow: 680, outflow: -95, net: 585 },
    { day: "Nov 11", inflow: 0, outflow: -380, net: -380 },
    { day: "Nov 14", inflow: 2560, outflow: -165, net: 2395 },
    { day: "Nov 16", inflow: 420, outflow: -520, net: -100 },
    { day: "Nov 18", inflow: 0, outflow: -450, net: -450 },
    { day: "Nov 21", inflow: 3120, outflow: -280, net: 2840 },
    { day: "Nov 23", inflow: 580, outflow: -78, net: 502 },
    { day: "Nov 25", inflow: 0, outflow: -35, net: -35 },
    { day: "Nov 28", inflow: 2845, outflow: -185, net: 2660 },
  ],
};

// Mock banking/transaction data
export const mockBankingData = {
  kpiData: {
    totalBalance: 42150,
    availableCash: 38420,
    mtdPayouts: 24580,
    mtdExpenses: 8420,
    netProfit: 16160,
    creditUtilization: 23,
  },
  linkedAccounts: [
    { id: 1, institution: "Chase", name: "Business Checking", type: "Chequing", available: 28450, current: 28450, logo: "🏦", sparkline: [28000, 29500, 27800, 30200, 28450] },
    { id: 2, institution: "Wells Fargo", name: "Savings", type: "Savings", available: 13700, current: 13700, logo: "🏛️", sparkline: [12000, 12500, 13000, 13200, 13700] },
    { id: 3, institution: "Capital One", name: "Venture Card", type: "Credit Card", available: 8500, current: -2340, logo: "💳", sparkline: [-1800, -2100, -1950, -2200, -2340] },
    { id: 4, institution: "Toyota Financial", name: "Auto Loan - Tesla", type: "Loan", available: 0, current: -18500, logo: "🚗", sparkline: [-19200, -19000, -18800, -18650, -18500] },
  ],
  transactions: [
    { id: 1, date: "Nov 28", merchant: "Turo Payout", amount: 2845, category: "Income", vehicle: "Multiple", turoRelated: true, type: "income" },
    { id: 2, date: "Nov 27", merchant: "Shell Gas Station", amount: -65, category: "Fuel", vehicle: "Tesla Model 3", turoRelated: true, type: "expense" },
    { id: 3, date: "Nov 27", merchant: "AutoZone", amount: -120, category: "Maintenance", vehicle: "BMW X5", turoRelated: true, type: "expense" },
    { id: 4, date: "Nov 26", merchant: "State Farm", amount: -450, category: "Insurance", vehicle: "All Vehicles", turoRelated: true, type: "expense" },
    { id: 5, date: "Nov 25", merchant: "Express Car Wash", amount: -35, category: "Cleaning", vehicle: "Mercedes C-Class", turoRelated: true, type: "expense" },
    { id: 6, date: "Nov 24", merchant: "Turo Payout", amount: 1580, category: "Income", vehicle: "Tesla Model Y", turoRelated: true, type: "income" },
    { id: 7, date: "Nov 23", merchant: "Costco Gas", amount: -78, category: "Fuel", vehicle: "Audi A4", turoRelated: true, type: "expense" },
    { id: 8, date: "Nov 22", merchant: "Discount Tire", amount: -380, category: "Repairs", vehicle: "BMW X5", turoRelated: true, type: "expense" },
  ],
  upcomingBills: [
    { id: 1, name: "Toyota Auto Loan", nextPayment: "Dec 5", minPayment: 485, apr: 4.9, balance: 18500, vehicle: "Tesla Model 3" },
    { id: 2, name: "Capital One Card", nextPayment: "Dec 12", minPayment: 125, apr: 19.9, balance: 2340, vehicle: null },
    { id: 3, name: "Insurance Premium", nextPayment: "Dec 18", minPayment: 450, apr: 0, balance: 450, vehicle: "All Vehicles" },
    { id: 4, name: "BMW Financing", nextPayment: "Dec 20", minPayment: 520, apr: 3.9, balance: 24800, vehicle: "BMW X5" },
  ],
};
