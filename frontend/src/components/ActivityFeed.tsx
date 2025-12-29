import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity } from "lucide-react";

export const ActivityFeed = () => {
  return (
    <Card className="rounded-2xl shadow-sm border-border/50">
      <CardHeader className="pb-4">
        <CardTitle className="text-lg font-bold flex items-center gap-2">
          <Activity className="h-5 w-5 text-primary" />
          Recent Activity
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <Activity className="h-12 w-12 text-muted-foreground mb-4 opacity-50" />
          <p className="text-lg font-semibold text-foreground mb-2">COMING SOON</p>
        </div>
      </CardContent>
    </Card>
  );
};
