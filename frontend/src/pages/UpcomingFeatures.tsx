import { Link } from "react-router-dom";
import { ChevronLeft, Sparkles, Wrench, Camera, BellRing, TrendingUp, BarChart3, MessageSquareText, ArrowRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

type FeatureItem = {
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string[];
};

const features: FeatureItem[] = [
  {
    title: "360° Vehicle Photo Creator & Damage Detection",
    icon: Camera,
    description: [
      "All vehicle photos will be automatically combined into an interactive 360-degree view.",
      "The system will compare current photos against pre-delivery documentation to detect and highlight potential new damage.",
      "For best accuracy, vehicles should be clean when photos are taken to reduce false detections.",
    ],
  },
  {
    title: "Late Return Notifier",
    icon: BellRing,
    description: [
      "Vehicles scheduled for return will be monitored in real time.",
      "The platform will calculate the distance and estimated arrival time to the drop-off location.",
      "You’ll be notified if a vehicle is likely to be late, including an estimated delay.",
    ],
  },
  {
    title: "Auto Vehicle Maximizer",
    icon: TrendingUp,
    description: [
      "Provides profitability insights for each vehicle, including:",
      "• Estimated break-even daily pricing",
      "• Identification of low-performing vehicles",
      "• Actionable suggestions to improve utilization and earnings",
    ],
  },
  {
    title: "Fleet Performance Insights",
    icon: BarChart3,
    description: [
      "Aggregated views of fleet performance over time, including:",
      "• Utilization trends",
      "• Earnings comparisons",
      "• Vehicle-level performance summaries",
      "Designed to help hosts make better pricing, listing, and fleet decisions.",
    ],
  },
  {
    title: "Ongoing Improvements",
    icon: MessageSquareText,
    description: [
      "Additional features and refinements will continue to be added based on:",
      "• Host feedback",
      "• Real-world usage",
      "• Performance and reliability testing",
      "User suggestions play a major role in shaping the roadmap.",
    ],
  },
];

const UpcomingFeatures = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5 overflow-hidden">
      {/* Background treatment */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-[520px] h-[520px] bg-primary/15 rounded-full blur-3xl" />
        <div className="absolute top-1/3 -left-48 w-[560px] h-[560px] bg-primary/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-56 right-1/4 w-[520px] h-[520px] bg-primary/10 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 max-w-6xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
        {/* Back button */}
        <div className="mb-6">
          <Link to="/" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors">
            <ChevronLeft className="w-4 h-4" />
            Back
          </Link>
        </div>

        {/* Header */}
        <div className="text-center mb-10 sm:mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-sm font-medium mb-4">
            <Sparkles className="w-4 h-4" />
            Roadmap
          </div>
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight text-foreground mb-4">
            Upcoming Features
          </h1>
          <p className="text-base sm:text-lg text-muted-foreground max-w-3xl mx-auto">
            The following features are currently in development and are planned to be available by or shortly after release.
            Timelines may adjust based on testing and feedback.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8 items-start">
          {/* Left: Context card */}
          <Card className="lg:sticky lg:top-6 border-primary/15 bg-card/70 backdrop-blur-sm shadow-xl">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2">
                <span className="inline-flex items-center justify-center w-9 h-9 rounded-lg bg-primary/10 border border-primary/15">
                  <Wrench className="w-5 h-5 text-primary" />
                </span>
                What to expect
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground space-y-3">
              <p>
                We build in tight feedback loops. Features may ship incrementally and improve quickly as hosts use them in the real world.
              </p>
              <p className="text-xs text-muted-foreground">
                Have a request? Join the waitlist and reply to the welcome email with your top priorities.
              </p>
              <Link to="/waitlist">
                <Button className="w-full gap-2 group">
                  Join Waitlist
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                </Button>
              </Link>
            </CardContent>
          </Card>

          {/* Right: Feature cards */}
          <div className="lg:col-span-2 space-y-4 sm:space-y-6">
            {features.map((feature) => (
              <Card key={feature.title} className="border-border/50 bg-card/60 backdrop-blur-sm shadow-2xl">
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-3">
                    <span className="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-primary/10 border border-primary/15">
                      <feature.icon className="w-5 h-5 text-primary" />
                    </span>
                    {feature.title}
                  </CardTitle>
                </CardHeader>
                <CardContent className="text-muted-foreground text-sm sm:text-[15px] leading-relaxed">
                  <div className="space-y-2">
                    {feature.description.map((line, idx) => (
                      <p key={idx}>{line}</p>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}

            <div className="pt-2 text-center">
              <Link to="/faqs" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                Want more details on privacy/integrations? View FAQs
              </Link>
            </div>

            <div className="mt-10 pt-6 border-t border-border/30 text-center">
              <p className="text-xs text-muted-foreground">© {new Date().getFullYear()} Turolytics. All rights reserved.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UpcomingFeatures;

