import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Calendar, DollarSign, Wrench, Star, Activity, Loader2 } from "lucide-react";
import { useState, useEffect } from "react";
import { tripsService } from "@/services/trips-service";
import { reviewsService } from "@/services/reviews-service";

interface ActivityItem {
  id: string;
  type: "booking" | "payment" | "maintenance" | "review";
  message: string;
  time: string;
  timestamp: Date;
}

const getIcon = (type: ActivityItem["type"]) => {
  switch (type) {
    case "booking":
      return <Calendar className="h-4 w-4" />;
    case "payment":
      return <DollarSign className="h-4 w-4" />;
    case "maintenance":
      return <Wrench className="h-4 w-4" />;
    case "review":
      return <Star className="h-4 w-4" />;
  }
};

const getIconColor = (type: ActivityItem["type"]) => {
  switch (type) {
    case "booking":
      return "bg-gradient-to-br from-primary/20 to-primary/10 text-primary border border-primary/20 shadow-sm shadow-primary/10";
    case "payment":
      return "bg-gradient-to-br from-success/20 to-success/10 text-success border border-success/20 shadow-sm shadow-success/10";
    case "maintenance":
      return "bg-gradient-to-br from-warning/20 to-warning/10 text-warning border border-warning/20 shadow-sm shadow-warning/10";
    case "review":
      return "bg-gradient-to-br from-chart-4/20 to-chart-4/10 text-chart-4 border border-chart-4/20 shadow-sm shadow-chart-4/10";
  }
};

const formatTimeAgo = (date: Date): string => {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins} ${diffMins === 1 ? 'minute' : 'minutes'} ago`;
  if (diffHours < 24) return `${diffHours} ${diffHours === 1 ? 'hour' : 'hours'} ago`;
  if (diffDays < 7) return `${diffDays} ${diffDays === 1 ? 'day' : 'days'} ago`;
  return date.toLocaleDateString();
};

export const ActivityFeed = () => {
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadActivity = async () => {
      try {
        setLoading(true);
        const activityItems: ActivityItem[] = [];

        // Fetch recent trips (bookings and payments)
        const [newBookings, recentTrips, recentReviews] = await Promise.all([
          tripsService.getNewBookingsToday(),
          tripsService.getTrips({ status: 'COMPLETED', limit: 10 }),
          reviewsService.getReviews({ limit: 10 })
        ]);

        // Add new bookings
        newBookings.bookings.forEach((booking) => {
          activityItems.push({
            id: `booking-${booking.id}`,
            type: "booking",
            message: `New booking: ${booking.vehicle_name}`,
            time: formatTimeAgo(new Date(booking.created_at || new Date())),
            timestamp: new Date(booking.created_at || new Date())
          });
        });

        // Add completed trips (payments)
        recentTrips.trips.slice(0, 5).forEach((trip) => {
          if (trip.total_earnings && trip.total_earnings > 0) {
            activityItems.push({
              id: `payment-${trip.id}`,
              type: "payment",
              message: `Payment received: $${trip.total_earnings.toFixed(2)}`,
              time: formatTimeAgo(new Date(trip.updated_at || trip.created_at || new Date())),
              timestamp: new Date(trip.updated_at || trip.created_at || new Date())
            });
          }
        });

        // Add recent reviews
        recentReviews.reviews.slice(0, 5).forEach((review) => {
          activityItems.push({
            id: `review-${review.id}`,
            type: "review",
            message: `New ${review.rating}-star review${review.customer_name ? ` from ${review.customer_name}` : ''}`,
            time: formatTimeAgo(new Date(review.date || review.created_at || new Date())),
            timestamp: new Date(review.date || review.created_at || new Date())
          });
        });

        // Sort by timestamp (most recent first) and limit to 10
        activityItems.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
        setActivities(activityItems.slice(0, 10));
      } catch (error) {
        console.error('Failed to load activity:', error);
        setActivities([]);
      } finally {
        setLoading(false);
      }
    };

    loadActivity();
  }, []);

  return (
    <Card className="rounded-2xl shadow-sm border-border/50">
      <CardHeader className="pb-4">
        <CardTitle className="text-lg font-bold flex items-center gap-2">
          <Activity className="h-5 w-5 text-primary" />
          Recent Activity
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
            <p className="text-sm text-muted-foreground">Loading activity...</p>
          </div>
        ) : activities.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <Activity className="h-12 w-12 text-muted-foreground mb-4 opacity-50" />
            <p className="text-lg font-semibold text-foreground mb-2">No Recent Activity</p>
            <p className="text-sm text-muted-foreground max-w-sm">
              Activity feed will show bookings, payments, maintenance updates, and reviews as they happen.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {activities.map((activity, index) => (
            <div 
              key={activity.id} 
              className="flex items-start gap-3 p-2.5 rounded-lg hover:bg-muted/30 transition-colors group"
              style={{ animationDelay: `${index * 50}ms` }}
            >
              <div className={`rounded-xl p-2.5 ${getIconColor(activity.type)} group-hover:scale-110 transition-transform flex-shrink-0`}>
                {getIcon(activity.type)}
              </div>
              <div className="flex-1 space-y-0.5 min-w-0">
                <p className="text-sm font-semibold text-foreground leading-tight">{activity.message}</p>
                <p className="text-xs text-muted-foreground font-medium">{activity.time}</p>
              </div>
            </div>
          ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
