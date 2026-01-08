import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Wrench, Droplet, FileText, Car, Battery, CheckCircle2, Calendar, Clock, AlertTriangle } from "lucide-react";
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { bouncieService } from "@/services/bouncie-service";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";
import { toast } from "@/hooks/use-toast";

interface MaintenanceItem {
  id: string;
  type: "maintenance" | "cleaning" | "insurance" | "service" | "alert";
  vehicle?: string;
  task: string;
  dueDate: string;
  urgency: "high" | "medium" | "low";
  icon: typeof Wrench;
  description?: string;
  estimatedCost?: number;
  lastCompleted?: string;
  completed?: boolean;
}

const initialMaintenanceItems: MaintenanceItem[] = [];

export const UpcomingMaintenanceTimeline = () => {
  const navigate = useNavigate();
  const [maintenanceItems, setMaintenanceItems] = useState(initialMaintenanceItems);
  const [selectedItem, setSelectedItem] = useState<MaintenanceItem | null>(null);
  const [bouncieConnected, setBouncieConnected] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkBouncieConnection = async () => {
      try {
        const status = await bouncieService.getIntegrationStatus();
        setBouncieConnected(status.connected);
      } catch (error) {
        console.error('Failed to check Bouncie connection status:', error);
        setBouncieConnected(false);
      } finally {
        setLoading(false);
      }
    };

    checkBouncieConnection();
  }, []);

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case "high":
        return "destructive";
      case "medium":
        return "default";
      case "low":
        return "secondary";
      default:
        return "default";
    }
  };

  const handleMarkCompleted = () => {
    if (!selectedItem) return;
    
    setMaintenanceItems(items => 
      items.map(item => 
        item.id === selectedItem.id 
          ? { ...item, completed: true }
          : item
      )
    );
    
    toast({
      title: "Marked as completed",
      description: `${selectedItem.task} has been marked as completed.`,
    });
    
    setSelectedItem(null);
  };

  const pendingItems = maintenanceItems.filter(item => !item.completed);
  const completedItems = maintenanceItems.filter(item => item.completed);

  return (
    <>
      <Card className="rounded-2xl shadow-sm border-border/50">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg font-semibold">Upcoming Maintenance</CardTitle>
            {completedItems.length > 0 && (
              <Badge variant="secondary" className="bg-success/10 text-success border-success/20">
                {completedItems.length} completed
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <p className="text-sm text-muted-foreground">Loading...</p>
            </div>
          ) : bouncieConnected === false ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <Wrench className="h-12 w-12 text-muted-foreground mb-4 opacity-50" />
              <p className="text-lg font-semibold text-foreground mb-2">Connect Bouncie to View Maintenance</p>
              <p className="text-sm text-muted-foreground max-w-sm mb-4">
                Connect your Bouncie account to monitor vehicle health, fuel levels, engine alerts, and maintenance needs in real-time.
              </p>
              <Button 
                onClick={() => navigate('/settings?tab=integrations')}
                variant="default" 
                size="sm"
              >
                Connect Bouncie
              </Button>
            </div>
          ) : pendingItems.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <CheckCircle2 className="h-12 w-12 text-success mb-4 opacity-50" />
              <p className="text-lg font-semibold text-foreground mb-2">No Upcoming Maintenance</p>
              <p className="text-sm text-muted-foreground max-w-sm">
                All maintenance items are up to date. Scheduled maintenance and service reminders will appear here.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {pendingItems.map((item) => {
            const Icon = item.icon;
            return (
              <div
                key={item.id}
                className="flex items-start gap-3 p-3 rounded-lg border border-border bg-card hover:bg-accent/50 hover:border-primary/30 transition-colors cursor-pointer"
                onClick={() => setSelectedItem(item)}
              >
                <div className="mt-0.5">
                  <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                    <Icon className="h-4 w-4 text-primary" />
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      {item.vehicle && (
                        <p className="text-sm font-semibold text-foreground">
                          {item.vehicle}
                        </p>
                      )}
                      <p className={`text-sm ${item.vehicle ? 'text-muted-foreground' : 'font-semibold text-foreground'}`}>
                        {item.task}
                      </p>
                    </div>
                    <Badge variant={getUrgencyColor(item.urgency)} className="shrink-0">
                      {item.dueDate}
                    </Badge>
                  </div>
                </div>
              </div>
            );
          })}
            </div>
          )}

          {/* Completed Items */}
          {completedItems.length > 0 && (
            <div className="pt-2 border-t border-border/50">
              <p className="text-xs text-muted-foreground mb-2">Completed</p>
              {completedItems.map((item) => {
                const Icon = item.icon;
                return (
                  <div
                    key={item.id}
                    className="flex items-start gap-3 p-3 rounded-lg border border-success/20 bg-success/5 opacity-60"
                  >
                    <div className="mt-0.5">
                      <div className="h-8 w-8 rounded-full bg-success/10 flex items-center justify-center">
                        <CheckCircle2 className="h-4 w-4 text-success" />
                      </div>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1">
                          {item.vehicle && (
                            <p className="text-sm font-semibold text-foreground line-through">
                              {item.vehicle}
                            </p>
                          )}
                          <p className="text-sm text-muted-foreground line-through">
                            {item.task}
                          </p>
                        </div>
                        <Badge variant="outline" className="shrink-0 bg-success/10 text-success border-success/20">
                          Completed
                        </Badge>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Maintenance Detail Modal */}
      <Dialog open={!!selectedItem} onOpenChange={() => setSelectedItem(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {selectedItem && <selectedItem.icon className="h-5 w-5 text-primary" />}
              Maintenance Details
            </DialogTitle>
          </DialogHeader>
          
          {selectedItem && (
            <div className="space-y-4">
              {/* Header */}
              <div className="bg-muted/30 rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-bold text-lg">{selectedItem.task}</h3>
                    {selectedItem.vehicle && (
                      <div className="flex items-center gap-2 mt-1">
                        <Car className="h-4 w-4 text-primary" />
                        <span className="text-sm font-medium">{selectedItem.vehicle}</span>
                      </div>
                    )}
                  </div>
                  <Badge variant={getUrgencyColor(selectedItem.urgency)}>
                    {selectedItem.urgency} priority
                  </Badge>
                </div>
              </div>

              {/* Due Date */}
              <div className="flex items-center gap-3 text-sm">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">Due:</span>
                <span className="font-semibold">{selectedItem.dueDate}</span>
              </div>

              {selectedItem.lastCompleted && (
                <div className="flex items-center gap-3 text-sm">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Last completed:</span>
                  <span className="font-medium">{selectedItem.lastCompleted}</span>
                </div>
              )}

              <Separator />

              {/* Description */}
              {selectedItem.description && (
                <div className="space-y-2">
                  <h4 className="font-semibold text-sm">Description</h4>
                  <p className="text-sm text-muted-foreground">{selectedItem.description}</p>
                </div>
              )}

              {/* Estimated Cost */}
              {selectedItem.estimatedCost && (
                <div className="bg-primary/5 rounded-lg p-4 border border-primary/10">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Estimated Cost</span>
                    <span className="text-xl font-bold">${selectedItem.estimatedCost}</span>
                  </div>
                </div>
              )}

              {selectedItem.urgency === "high" && (
                <div className="flex items-start gap-2 text-sm bg-destructive/10 text-destructive rounded-lg p-3 border border-destructive/20">
                  <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                  <p>This is a high-priority item that requires immediate attention.</p>
                </div>
              )}
            </div>
          )}

          <DialogFooter className="gap-2 sm:gap-0">
            <Button variant="outline" onClick={() => setSelectedItem(null)}>
              Close
            </Button>
            <Button 
              onClick={handleMarkCompleted}
              className="bg-success hover:bg-success/90"
            >
              <CheckCircle2 className="h-4 w-4 mr-2" />
              Mark as Completed
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};
