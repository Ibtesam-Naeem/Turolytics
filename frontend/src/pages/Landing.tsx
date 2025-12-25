import { Button } from "@/components/ui/button";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { 
  Car, 
  BarChart3, 
  MapPin, 
  DollarSign, 
  Shield, 
  Zap,
  ArrowRight,
  TrendingUp,
  Clock,
  Sparkles
} from "lucide-react";

const Landing = () => {
  const navigate = useNavigate();
  const { loginDemo } = useAuth();

  const handleViewDemo = async () => {
    await loginDemo();
    navigate("/dashboard");
  };

  const features = [
    {
      icon: Car,
      title: "Fleet Management",
      description: "Track all your vehicles in one place"
    },
    {
      icon: BarChart3,
      title: "Advanced Analytics",
      description: "Deep insights into performance"
    },
    {
      icon: MapPin,
      title: "Live GPS Tracking",
      description: "Real-time vehicle locations"
    },
    {
      icon: DollarSign,
      title: "Financial Dashboard",
      description: "Track earnings effortlessly"
    },
    {
      icon: Shield,
      title: "Document Management",
      description: "Organized with expiry alerts"
    },
    {
      icon: Zap,
      title: "Automated Insights",
      description: "Maximize your ROI"
    }
  ];

  const stats = [
    { value: "40%", label: "Revenue Increase", icon: TrendingUp },
    { value: "10hrs", label: "Saved Weekly", icon: Clock },
    { value: "99.9%", label: "Uptime", icon: Sparkles },
  ];

  return (
    <div className="min-h-screen bg-background overflow-hidden">
      {/* Gradient Orbs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary/20 rounded-full blur-3xl" />
        <div className="absolute top-1/2 -left-40 w-96 h-96 bg-primary/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 right-1/3 w-72 h-72 bg-primary/15 rounded-full blur-3xl" />
      </div>

      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-background/60 backdrop-blur-xl border-b border-border/50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 group">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center group-hover:scale-105 transition-transform">
              <span className="text-primary-foreground font-bold text-lg">T</span>
            </div>
            <span className="font-bold text-lg tracking-tight">Turolytics</span>
          </Link>
          <div className="flex items-center gap-2 sm:gap-3">
            <Link to="/auth">
              <Button variant="ghost" size="sm" className="text-sm">Sign In</Button>
            </Link>
            <Link to="/auth?mode=signup">
              <Button size="sm" className="text-sm gap-1.5 group">
                Get Started
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-24 sm:pt-28 pb-12 sm:pb-16 px-4 sm:px-6">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight leading-[1.1] mb-4 sm:mb-6">
            Your Turo Fleet,
            <span className="block bg-gradient-to-r from-primary via-primary to-primary/70 bg-clip-text text-transparent">
              Supercharged
            </span>
          </h1>
          <p className="text-base sm:text-lg md:text-xl text-muted-foreground max-w-xl mx-auto mb-6 sm:mb-8">
            The command center for serious Turo hosts. Track, analyze, and scale your rental business.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 mb-8 sm:mb-12">
            <Link to="/auth?mode=signup" className="w-full sm:w-auto">
              <Button size="lg" className="w-full sm:w-auto gap-2 h-11 sm:h-12 px-6 sm:px-8 text-sm sm:text-base group">
                Start Free Trial
                <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
              </Button>
            </Link>
            <Button 
              variant="outline" 
              size="lg" 
              className="w-full sm:w-auto h-11 sm:h-12 px-6 sm:px-8 text-sm sm:text-base bg-background/50 backdrop-blur-sm"
              onClick={handleViewDemo}
            >
              View Demo
            </Button>
          </div>
          
          {/* Stats Row */}
          <div className="flex flex-wrap items-center justify-center gap-6 sm:gap-10">
            {stats.map((stat) => (
              <div key={stat.label} className="flex items-center gap-2 sm:gap-3">
                <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                  <stat.icon className="w-4 h-4 sm:w-5 sm:h-5 text-primary" />
                </div>
                <div className="text-left">
                  <div className="text-lg sm:text-xl font-bold">{stat.value}</div>
                  <div className="text-xs sm:text-sm text-muted-foreground">{stat.label}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="relative py-12 sm:py-16 px-4 sm:px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-8 sm:mb-10">
            <h2 className="text-2xl sm:text-3xl font-bold mb-2">
              Everything in One Place
            </h2>
            <p className="text-muted-foreground text-sm sm:text-base">
              Built for hosts who want to scale
            </p>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4">
            {features.map((feature) => (
              <div
                key={feature.title}
                className="group p-4 sm:p-5 rounded-xl bg-card/50 backdrop-blur-sm border border-border/50 hover:border-primary/30 hover:bg-card/80 transition-all duration-300"
              >
                <div className="w-10 h-10 sm:w-11 sm:h-11 rounded-lg bg-primary/10 flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
                  <feature.icon className="w-5 h-5 text-primary" />
                </div>
                <h3 className="font-semibold text-sm sm:text-base mb-1">{feature.title}</h3>
                <p className="text-muted-foreground text-xs sm:text-sm">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative py-12 sm:py-16 px-4 sm:px-6">
        <div className="max-w-2xl mx-auto">
          <div className="relative p-6 sm:p-8 rounded-2xl bg-gradient-to-br from-primary/10 via-primary/5 to-transparent border border-primary/20 text-center">
            <h2 className="text-xl sm:text-2xl font-bold mb-2">
              Ready to Scale Your Fleet?
            </h2>
            <p className="text-muted-foreground text-sm sm:text-base mb-5">
              Join hosts who are maximizing their earnings
            </p>
            <Link to="/auth?mode=signup">
              <Button size="lg" className="gap-2 h-11 px-6 group">
                Get Started Free
                <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
              </Button>
            </Link>
            <p className="text-xs text-muted-foreground mt-3">
              No credit card required
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative py-6 px-4 sm:px-6 border-t border-border/50">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-primary flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-xs">T</span>
            </div>
            <span className="font-semibold text-sm">Turolytics</span>
          </div>
          <p className="text-xs text-muted-foreground">
            © 2025 Turolytics. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
