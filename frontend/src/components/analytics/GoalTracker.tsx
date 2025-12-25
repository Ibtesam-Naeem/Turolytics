import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Target } from "lucide-react";

const goals = [
  { label: "Monthly Revenue Goal", current: 31600, target: 35000, unit: "$" },
  { label: "Fleet Utilization Goal", current: 68, target: 75, unit: "%" },
  { label: "Monthly Trips Goal", current: 75, target: 90, unit: "" },
  { label: "Customer Rating Goal", current: 4.7, target: 4.8, unit: "★" },
];

export const GoalTracker = () => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Target className="h-5 w-5 text-primary" />
          Goal Tracker
        </CardTitle>
        <CardDescription>Monthly targets and progress</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {goals.map((goal, idx) => {
            const progress = (goal.current / goal.target) * 100;
            const achieved = progress >= 100;
            
            return (
              <div key={idx}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-foreground">{goal.label}</span>
                  <span className="text-sm text-muted-foreground">
                    {goal.unit === "$" ? "$" : ""}{goal.current.toLocaleString()}{goal.unit !== "$" ? goal.unit : ""} / {goal.unit === "$" ? "$" : ""}{goal.target.toLocaleString()}{goal.unit !== "$" ? goal.unit : ""}
                  </span>
                </div>
                <Progress 
                  value={Math.min(progress, 100)} 
                  className="h-2"
                />
                <p className={`text-xs mt-1 ${achieved ? "text-success" : "text-muted-foreground"}`}>
                  {achieved ? "✓ Goal achieved!" : `${(100 - progress).toFixed(0)}% to go`}
                </p>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};