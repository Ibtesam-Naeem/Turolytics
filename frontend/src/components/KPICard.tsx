import { Card, CardContent } from "@/components/ui/card";
import { LucideIcon, TrendingUp, TrendingDown } from "lucide-react";

interface KPICardProps {
  title: string;
  value: string;
  trend?: string;
  trendPositive?: boolean;
  icon: LucideIcon;
}

export const KPICard = ({ title, value, trend, trendPositive, icon: Icon }: KPICardProps) => {
  const isRatingCard = title === "Average Rating";
  
  return (
    <Card className="rounded-2xl shadow-sm hover:shadow-lg transition-all duration-300 overflow-hidden group border-border/50 hover:border-primary/30 animate-fade-in">
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
      <CardContent className="p-6 relative">
        <div className="flex items-start justify-between">
          <div className="space-y-2 flex-1">
            <p className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
              {title}
            </p>
            <p className="text-4xl font-bold text-foreground tracking-tight">
              {value}
            </p>
            {trend && (
              <div className="flex items-center gap-1.5">
                {!isRatingCard && (
                  trendPositive ? (
                    <TrendingUp className="h-3.5 w-3.5 text-success" />
                  ) : (
                    <TrendingDown className="h-3.5 w-3.5 text-destructive" />
                  )
                )}
                <p className={`text-xs font-semibold ${
                  isRatingCard 
                    ? 'text-rating' 
                    : trendPositive 
                      ? 'text-success' 
                      : 'text-destructive'
                }`}>
                  {trend}
                </p>
              </div>
            )}
          </div>
          <div className={`rounded-xl p-3.5 transition-all duration-300 group-hover:scale-110 ${
            isRatingCard 
              ? 'bg-gradient-to-br from-rating/30 to-rating/15 shadow-lg shadow-rating/30 ring-1 ring-rating/20' 
              : 'bg-gradient-to-br from-primary/20 to-primary/10 shadow-lg shadow-primary/20'
          }`}>
            <Icon className={`transition-all duration-300 ${
              isRatingCard 
                ? 'h-7 w-7 text-rating stroke-[2.5] filter drop-shadow-[0_0_8px_rgba(251,191,36,0.6)]' 
                : 'h-6 w-6 text-primary'
            }`} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
