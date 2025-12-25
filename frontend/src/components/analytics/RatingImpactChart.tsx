import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Scatter, ScatterChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis, ZAxis } from "recharts";
import { Star } from "lucide-react";

const data = [
  { rating: 4.9, bookings: 18, revenue: 5240, vehicle: "Tesla Model 3" },
  { rating: 4.8, bookings: 15, revenue: 5700, vehicle: "BMW X5" },
  { rating: 4.7, bookings: 14, revenue: 4680, vehicle: "Mercedes C-Class" },
  { rating: 4.6, bookings: 12, revenue: 4320, vehicle: "Tesla Model Y" },
  { rating: 4.5, bookings: 16, revenue: 4640, vehicle: "Audi A4" },
  { rating: 4.3, bookings: 10, revenue: 3200, vehicle: "Honda Civic" },
  { rating: 4.2, bookings: 8, revenue: 2800, vehicle: "Toyota Camry" },
];

export const RatingImpactChart = () => {
  const avgRating = (data.reduce((sum, item) => sum + item.rating, 0) / data.length).toFixed(2);
  const correlation = "Strong positive correlation";

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Star className="h-5 w-5 text-rating fill-rating" />
          Rating vs Performance
        </CardTitle>
        <CardDescription>
          Avg Rating: {avgRating} ★ • {correlation}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={350}>
          <ScatterChart
            margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis
              type="number"
              dataKey="rating"
              name="Rating"
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
              domain={[4.0, 5.0]}
              tickFormatter={(value) => `${value}★`}
            />
            <YAxis
              type="number"
              dataKey="bookings"
              name="Bookings"
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
            />
            <ZAxis
              type="number"
              dataKey="revenue"
              range={[100, 1000]}
              name="Revenue"
            />
            <Tooltip
              cursor={{ strokeDasharray: "3 3" }}
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "8px",
              }}
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="p-3 space-y-1">
                      <p className="font-medium text-foreground">{data.vehicle}</p>
                      <p className="text-sm text-muted-foreground">Rating: {data.rating} ★</p>
                      <p className="text-sm text-muted-foreground">Bookings: {data.bookings}</p>
                      <p className="text-sm text-muted-foreground">Revenue: ${data.revenue.toLocaleString()}</p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Scatter
              name="Vehicles"
              data={data}
              fill="hsl(var(--chart-1))"
              fillOpacity={0.6}
            />
          </ScatterChart>
        </ResponsiveContainer>

        {/* Insights */}
        <div className="mt-4 space-y-2">
          <div className="p-3 bg-success/10 border border-success/20 rounded-lg">
            <p className="text-sm font-medium text-success">📈 Key Finding</p>
            <p className="text-xs text-muted-foreground mt-1">
              Vehicles with 4.8+ ratings receive 40% more bookings on average
            </p>
          </div>
          <div className="p-3 bg-muted/30 rounded-lg">
            <p className="text-xs font-medium text-foreground mb-2">💡 Recommendations</p>
            <ul className="text-xs text-muted-foreground space-y-1">
              <li>• Focus on improving ratings for vehicles below 4.5★</li>
              <li>• Premium service for high-rated vehicles increases revenue</li>
            </ul>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};