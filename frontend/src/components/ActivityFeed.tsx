import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Activity } from "lucide-react";
import { useNavigate } from "react-router-dom";

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
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <Activity className="h-12 w-12 text-muted-foreground mb-4 opacity-50" />
          <p className="text-lg font-semibold text-foreground mb-2">Connect Accounts to View Activity</p>
          <p className="text-sm text-muted-foreground max-w-sm mb-4">
            Connect your Turo, Banking, and other accounts to track transactions, trips, earnings, fleet activity and important info in real-time.
          </p>
          <Button 
            onClick={() => navigate('/settings?tab=integrations')}
            variant="default" 
            size="sm"
          >
            Connect Accounts
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};
