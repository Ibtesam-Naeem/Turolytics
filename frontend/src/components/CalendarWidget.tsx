import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Calendar } from "@/components/ui/calendar";
import { useState } from "react";

export const CalendarWidget = () => {
  const [date, setDate] = useState<Date | undefined>(new Date());

  return (
    <Card className="rounded-xl shadow-sm w-full max-w-full">
      <CardContent className="pt-4 w-full">
        <Calendar
          mode="single"
          selected={date}
          onSelect={setDate}
          className="rounded-md"
        />
      </CardContent>
    </Card>
  );
};
