import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Activity, DollarSign, FileText, Car, Star, Shield, CreditCard, TrendingUp } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { formatRelativeTime } from "@/lib/utils";

interface ActivityItem {
  id: string;
  type: "payment" | "review" | "insurance" | "note" | "expense";
  title: string;
  description: string;
  amount?: number;
  timestamp: string;
  icon: typeof DollarSign;
  color: string;
}

const mockActivities: ActivityItem[] = [
  {
    id: "1",
    type: "payment",
    title: "Turo Payment Received",
    description: "Payment for Tesla Model 3 trip completed",
    amount: 245,
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
    icon: DollarSign,
    color: "text-success",
  },
  {
    id: "2",
    type: "review",
    title: "New Review Received",
    description: "5-star review from John Smith for Tesla Model 3",
    timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(), // 5 hours ago
    icon: Star,
    color: "text-warning",
  },
  {
    id: "3",
    type: "insurance",
    title: "Insurance Payment",
    description: "Monthly insurance payment for fleet - $1,240",
    amount: 1240,
    timestamp: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(), // 1 day ago
    icon: Shield,
    color: "text-primary",
  },
  {
    id: "4",
    type: "note",
    title: "Car Note Payment",
    description: "Monthly payment for BMW X5 - $485",
    amount: 485,
    timestamp: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(), // 1 day ago
    icon: Car,
    color: "text-primary",
  },
  {
    id: "5",
    type: "payment",
    title: "Turo Payment Received",
    description: "Payment for Mercedes-Benz GLE trip completed",
    amount: 520,
    timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(), // 2 days ago
    icon: DollarSign,
    color: "text-success",
  },
  {
    id: "6",
    type: "review",
    title: "New Review Received",
    description: "4-star review from Emma Wilson for BMW X5",
    timestamp: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(), // 3 days ago
    icon: Star,
    color: "text-warning",
  },
  {
    id: "7",
    type: "note",
    title: "Car Note Payment",
    description: "Monthly payment for Porsche Cayenne - $620",
    amount: 620,
    timestamp: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(), // 5 days ago
    icon: Car,
    color: "text-primary",
  },
  {
    id: "8",
    type: "payment",
    title: "Turo Payment Received",
    description: "Payment for Land Rover Defender trip completed",
    amount: 750,
    timestamp: new Date(Date.now() - 6 * 24 * 60 * 60 * 1000).toISOString(), // 6 days ago
    icon: DollarSign,
    color: "text-success",
  },
];

export const ActivityFeed = () => {
  const navigate = useNavigate();

  return (
    <Card className="rounded-2xl shadow-sm border-border/50">
      <CardHeader className="pb-4">
        <CardTitle className="text-lg font-bold flex items-center gap-2">
          <Activity className="h-5 w-5 text-primary" />
          Recent Activity
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[400px]">
          <div className="space-y-3 pr-4">
            {mockActivities.map((activity) => {
            const Icon = activity.icon;
            return (
              <div
                key={activity.id}
                className="flex items-start gap-3 p-3 rounded-lg border border-border bg-card hover:bg-accent/50 hover:border-primary/30 transition-colors"
              >
                <div className="mt-0.5">
                  <div className={`h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center`}>
                    <Icon className={`h-4 w-4 ${activity.color}`} />
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <p className="text-sm font-semibold text-foreground">
                        {activity.title}
                      </p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {activity.description}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {formatRelativeTime(activity.timestamp)}
                      </p>
                    </div>
                    {activity.amount && (
                      <div className="flex flex-col items-end">
                        <p className={`text-sm font-bold ${activity.type === "payment" ? "text-success" : "text-foreground"}`}>
                          {activity.type === "payment" ? "+" : "-"}${activity.amount.toLocaleString()}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
};
