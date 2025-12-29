import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MapPin, DollarSign, Gauge, User, Calendar, ArrowRight, X } from "lucide-react";
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from "@/components/ui/carousel";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";
import { useState } from "react";
import { useRegionalSettings } from "@/contexts/RegionalSettingsContext";
import { formatDistance, formatCurrency, formatCurrencyDecimal, formatTimeString } from "@/lib/regional-utils";

interface UpcomingTrip {
  id: string;
  vehicleName: string;
  guestName: string;
  pickupLocation: string;
  dropoffLocation: string;
  earnings: number;
  kmsAllowed: number;
  startDate: string;
  // Extended pricing details
  days?: number;
  dailyRate?: number;
  kmsPerDay?: number;
  overageRate?: number;
  boostPricing?: number;
  tripTotal?: number;
  turoFees?: number;
  salesTax?: number;
  netEarnings?: number;
}

interface UpcomingTripsCardProps {
  trips: UpcomingTrip[];
  turoConnected?: boolean | null;
  onConnectClick?: () => void;
}

export const UpcomingTripsCard = ({ trips, turoConnected, onConnectClick }: UpcomingTripsCardProps) => {
  const { distanceUnit, currency, timeFormat } = useRegionalSettings();
  const [selectedTrip, setSelectedTrip] = useState<UpcomingTrip | null>(null);

  // Calculate derived values for display
  const getTripDetails = (trip: UpcomingTrip) => {
    const days = trip.days || 1;
    const dailyRate = trip.dailyRate || trip.earnings;
    const kmsPerDay = trip.kmsPerDay || trip.kmsAllowed;
    const overageRate = trip.overageRate || 0.10;
    const boostPricing = trip.boostPricing || 0;
    const tripTotal = trip.tripTotal || (dailyRate * days + boostPricing);
    const turoFees = trip.turoFees || tripTotal * 0.25;
    const salesTax = trip.salesTax || turoFees * 0.13;
    const netEarnings = trip.netEarnings || (tripTotal - turoFees - salesTax);

    return {
      days,
      dailyRate,
      kmsPerDay,
      totalKms: trip.kmsAllowed,
      overageRate,
      boostPricing,
      tripTotal,
      turoFees,
      salesTax,
      netEarnings,
    };
  };

  return (
    <>
      <Carousel
        opts={{
          align: "start",
          loop: false,
        }}
        className="w-full max-w-full"
      >
        <Card className="rounded-2xl shadow-lg border-border/50 overflow-hidden w-full max-w-full">
        <CardHeader className="bg-gradient-to-r from-primary/5 to-transparent border-b border-border/50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <Calendar className="h-5 w-5 text-primary" />
                Upcoming Trips
              </CardTitle>
              <Badge variant="secondary" className="bg-primary/10 text-primary border-primary/20 font-semibold">
                {trips.length} Scheduled
              </Badge>
            </div>
            <div className="flex items-center gap-2">
              <CarouselPrevious className="static translate-y-0 h-8 w-8" />
              <CarouselNext className="static translate-y-0 h-8 w-8" />
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-6">
          {turoConnected === false ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Calendar className="h-12 w-12 text-muted-foreground mb-4 opacity-50" />
              <p className="text-lg font-semibold text-foreground mb-2">Link Turo Account</p>
              <p className="text-sm text-muted-foreground mb-4">Connect your Turo account to view upcoming trips.</p>
              {onConnectClick && (
                <Button onClick={onConnectClick} variant="default" size="sm">
                  Connect Turo Account
                </Button>
              )}
            </div>
          ) : trips.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Calendar className="h-12 w-12 text-muted-foreground mb-4 opacity-50" />
              <p className="text-lg font-semibold text-foreground mb-2">No upcoming trips</p>
              <p className="text-sm text-muted-foreground">You don't have any scheduled trips at the moment.</p>
            </div>
          ) : (
          <CarouselContent className="-ml-4">
            {trips.map((trip) => (
              <CarouselItem key={trip.id} className="pl-4 md:basis-1/2 lg:basis-1/3">
                <div 
                  className="group border-2 border-border/50 rounded-2xl p-5 hover:border-primary/50 hover:shadow-xl transition-all duration-300 bg-gradient-to-br from-card to-card/50 hover:-translate-y-1 h-full cursor-pointer"
                  onClick={() => setSelectedTrip(trip)}
                >
                {/* Header */}
                <div className="mb-4 pb-3 border-b border-border/50">
                  <h4 className="font-bold text-foreground text-lg group-hover:text-primary transition-colors">
                    {trip.vehicleName}
                  </h4>
                  <div className="flex items-center gap-1.5 mt-1">
                    <Calendar className="h-3.5 w-3.5 text-primary" />
                    <p className="text-xs font-semibold text-primary">{trip.startDate}</p>
                  </div>
                </div>
              
                {/* Details */}
                <div className="space-y-3">
                  {/* Guest */}
                  <div className="flex items-center gap-2.5 text-sm bg-muted/30 rounded-lg p-2.5">
                    <User className="h-4 w-4 text-primary flex-shrink-0" />
                    <span className="text-foreground font-semibold">{trip.guestName}</span>
                  </div>
                
                  {/* Locations */}
                  <div className="space-y-2 bg-gradient-to-br from-success/5 to-transparent rounded-lg p-3 border border-success/10">
                    <div className="flex items-start gap-2 text-sm">
                      <MapPin className="h-4 w-4 text-success mt-0.5 flex-shrink-0" />
                      <div className="flex-1">
                        <p className="text-xs text-muted-foreground font-medium mb-0.5">Pickup</p>
                        <p className="text-foreground font-semibold">{trip.pickupLocation}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-center">
                      <ArrowRight className="h-4 w-4 text-muted-foreground" />
                    </div>
                    
                    <div className="flex items-start gap-2 text-sm">
                      <MapPin className="h-4 w-4 text-destructive mt-0.5 flex-shrink-0" />
                      <div className="flex-1">
                        <p className="text-xs text-muted-foreground font-medium mb-0.5">Dropoff</p>
                        <p className="text-foreground font-semibold">{trip.dropoffLocation}</p>
                      </div>
                    </div>
                  </div>
                
                  {/* Earnings & Distance */}
                  <div className="flex items-center justify-between pt-2 gap-3">
                    <div className="flex items-center gap-2 bg-success/10 rounded-lg px-3 py-2 border border-success/20 flex-1">
                      <DollarSign className="h-4 w-4 text-success" />
                      <div>
                        <p className="text-xs text-muted-foreground font-medium">Earnings</p>
                        <span className="font-bold text-success text-base">${trip.earnings}</span>
                      </div>
                    </div>
                  
                    <div className="flex items-center gap-2 bg-primary/10 rounded-lg px-3 py-2 border border-primary/20 flex-1">
                      <Gauge className="h-4 w-4 text-primary" />
                      <div>
                        <p className="text-xs text-muted-foreground font-medium">Limit</p>
                        <span className="font-bold text-foreground text-base">{formatDistance(trip.kmsAllowed, distanceUnit)}</span>
                      </div>
                    </div>
                  </div>
                  </div>
                </div>
              </CarouselItem>
            ))}
          </CarouselContent>
          )}
        </CardContent>
      </Card>
      </Carousel>

      {/* Trip Detail Modal */}
      <Dialog open={!!selectedTrip} onOpenChange={() => setSelectedTrip(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5 text-primary" />
              Trip Details
            </DialogTitle>
          </DialogHeader>
          
          {selectedTrip && (() => {
            const details = getTripDetails(selectedTrip);
            return (
              <div className="space-y-4">
                {/* Trip Header */}
                <div className="bg-muted/30 rounded-lg p-4">
                  <h3 className="font-bold text-lg">{selectedTrip.vehicleName}</h3>
                  <p className="text-sm text-muted-foreground">{selectedTrip.startDate}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <User className="h-4 w-4 text-primary" />
                    <span className="text-sm font-medium">{selectedTrip.guestName}</span>
                  </div>
                </div>

                {/* Locations */}
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm">
                    <MapPin className="h-4 w-4 text-success" />
                    <span className="text-muted-foreground">From:</span>
                    <span className="font-medium">{selectedTrip.pickupLocation}</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <MapPin className="h-4 w-4 text-destructive" />
                    <span className="text-muted-foreground">To:</span>
                    <span className="font-medium">{selectedTrip.dropoffLocation}</span>
                  </div>
                </div>

                <Separator />

                {/* Kilometers Included */}
                <div>
                  <h4 className="font-semibold mb-2">{distanceUnit === "miles" ? "Miles" : "Kilometers"} included</h4>
                  <p className="text-2xl font-bold">{formatDistance(details.totalKms, distanceUnit)}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {selectedTrip.guestName} can be charged {formatCurrencyDecimal(details.overageRate, currency)} for every {distanceUnit === "miles" ? "mile" : "kilometer"} over the total included for the trip.
                  </p>
                </div>

                <Separator />

                {/* Trip Price Breakdown */}
                <div className="space-y-2">
                  <h4 className="font-semibold">Trip price</h4>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">{details.days} day @ {formatCurrencyDecimal(details.dailyRate, currency)}/day</span>
                    <span className="font-medium">{formatCurrencyDecimal(details.days * details.dailyRate, currency)}</span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Distance limited to {formatDistance(details.kmsPerDay, distanceUnit)} per day
                  </p>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">{formatDistance(details.totalKms, distanceUnit)} total</span>
                    <span>{formatCurrencyDecimal(0, currency)}</span>
                  </div>
                  {details.boostPricing > 0 && (
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Last-minute boost pricing</span>
                      <span>{formatCurrencyDecimal(details.boostPricing, currency)}</span>
                    </div>
                  )}
                  <div className="flex justify-between font-semibold pt-2 border-t border-border">
                    <span>Trip total</span>
                    <span>{formatCurrencyDecimal(details.tripTotal, currency)}</span>
                  </div>
                </div>

                <Separator />

                {/* Earnings Breakdown */}
                <div className="space-y-2">
                  <h4 className="font-semibold">Earnings</h4>
                  <div className="flex justify-between text-sm">
                    <div>
                      <span className="text-muted-foreground">Turo fees</span>
                      <p className="text-xs text-muted-foreground">Includes platform fees and protection plan</p>
                    </div>
                    <span className="text-destructive">- {formatCurrencyDecimal(details.turoFees, currency)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <div>
                      <span className="text-muted-foreground">Sales Tax</span>
                      <p className="text-xs text-muted-foreground">Applied to Turo services</p>
                    </div>
                    <span className="text-destructive">- {formatCurrencyDecimal(details.salesTax, currency)}</span>
                  </div>
                  <div className="flex justify-between font-bold text-lg pt-2 border-t border-border bg-success/10 rounded-lg p-3 -mx-1">
                    <span>You earned</span>
                    <span className="text-success">{formatCurrencyDecimal(details.netEarnings, currency)}</span>
                  </div>
                </div>
              </div>
            );
          })()}
        </DialogContent>
      </Dialog>
    </>
  );
};
