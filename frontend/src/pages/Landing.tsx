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
  Sparkles,
  Check,
  Laptop,
  Lock,
  Wallet,
  Activity,
  FileText,
  Link as LinkIcon,
  Gauge,
  CalendarDays
} from "lucide-react";

const Landing = () => {
  const navigate = useNavigate();
  const { loginDemo } = useAuth();

  const handleViewDemo = async () => {
    // Set demo mode in localStorage first
    localStorage.setItem('demo_mode', 'true');
    // Wait for loginDemo to complete
    await loginDemo();
    // Navigate after state is set
    navigate("/dashboard", { replace: true });
  };

  const features = [
    {
      icon: Car,
      title: "Fleet Management",
      description: "Track every vehicle, status, maintenance, and utilization in one place."
    },
    {
      icon: BarChart3,
      title: "Advanced Analytics",
      description: "Understand ROI, margins, and trends across vehicles and time."
    },
    {
      icon: MapPin,
      title: "Live GPS Tracking",
      description: "See location and activity at a glance when connected to telemetry."
    },
    {
      icon: DollarSign,
      title: "Financial Dashboard",
      description: "Bring payouts, expenses, and cashflow together for clarity."
    },
    {
      icon: Shield,
      title: "Document Management",
      description: "Keep registrations, insurance, and receipts organized with reminders."
    },
    {
      icon: Zap,
      title: "Automated Insights",
      description: "Spot problems early and get suggestions that move the needle."
    }
  ];

  const highlights = [
    { value: "Clarity", label: "One dashboard for ops + money", icon: Sparkles },
    { value: "Speed", label: "Less admin, more decisions", icon: Clock },
    { value: "Control", label: "User-controlled data access", icon: Lock },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5 overflow-hidden flex flex-col">
      {/* Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-48 -right-48 w-[560px] h-[560px] bg-primary/15 rounded-full blur-3xl" />
        <div className="absolute top-1/3 -left-48 w-[620px] h-[620px] bg-primary/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-56 right-1/4 w-[560px] h-[560px] bg-primary/10 rounded-full blur-3xl" />
        <div className="absolute inset-0 bg-grid-pattern opacity-[0.04]" />
      </div>

      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-background/70 backdrop-blur-xl border-b border-border/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 group">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center group-hover:scale-105 transition-transform">
              <span className="text-primary-foreground font-bold text-lg">T</span>
            </div>
            <span className="font-bold text-lg tracking-tight">Turolytics</span>
          </Link>
          <div className="flex items-center gap-2 sm:gap-3">
            <div className="hidden md:flex items-center gap-1 text-sm text-muted-foreground">
              <Link to="/faqs" className="px-3 py-2 hover:text-foreground transition-colors">FAQs</Link>
              <Link to="/upcoming-features" className="px-3 py-2 hover:text-foreground transition-colors">Roadmap</Link>
            </div>
            <Button variant="ghost" size="sm" className="text-sm" onClick={handleViewDemo}>
              View Demo
            </Button>
            <Link to="/waitlist">
              <Button size="sm" className="text-sm gap-1.5 group">
                Join Waitlist
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative pt-24 sm:pt-28 pb-10 sm:pb-14 px-4 sm:px-6">
          <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-10 items-center">
            {/* Copy */}
            <div className="lg:col-span-6">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-sm font-medium mb-5">
                <Sparkles className="w-4 h-4" />
                Built for serious Turo hosts
              </div>
              <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight leading-[1.05]">
                Your fleet.
                <span className="block bg-gradient-to-r from-primary via-primary to-primary/70 bg-clip-text text-transparent">
                  Clearly managed.
                </span>
              </h1>
              <p className="mt-5 text-base sm:text-lg text-muted-foreground max-w-xl">
                Turolytics is a modern dashboard for host operations—vehicles, trips, utilization, documents, and financial insights—without
                bouncing between tools.
              </p>

              <div className="mt-7 flex flex-col sm:flex-row gap-3">
                <Button size="lg" className="gap-2 h-11 sm:h-12 px-6 sm:px-8 group" onClick={handleViewDemo}>
                  View Demo
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                </Button>
                <Link to="/waitlist" className="w-full sm:w-auto">
                  <Button variant="outline" size="lg" className="w-full sm:w-auto h-11 sm:h-12 px-6 sm:px-8 bg-background/60 backdrop-blur-sm">
                    Join Waitlist
                  </Button>
                </Link>
              </div>

              <div className="mt-6 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                <div className="inline-flex items-center gap-2 rounded-full border border-border/60 bg-background/50 px-3 py-1">
                  <Check className="w-3.5 h-3.5 text-primary" />
                  No Turo credentials stored
                </div>
                <div className="inline-flex items-center gap-2 rounded-full border border-border/60 bg-background/50 px-3 py-1">
                  <Check className="w-3.5 h-3.5 text-primary" />
                  User-controlled data access
                </div>
                <div className="inline-flex items-center gap-2 rounded-full border border-border/60 bg-background/50 px-3 py-1">
                  <Check className="w-3.5 h-3.5 text-primary" />
                  Built for speed + clarity
                </div>
              </div>
            </div>

            {/* Product preview */}
            <div className="lg:col-span-6">
              <div className="relative rounded-2xl border border-border/60 bg-card/60 backdrop-blur-sm shadow-2xl overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-transparent" />
                <div className="relative p-5 sm:p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <div className="w-9 h-9 rounded-xl bg-primary/10 border border-primary/15 flex items-center justify-center">
                        <Laptop className="w-5 h-5 text-primary" />
                      </div>
                      <div>
                        <div className="text-sm font-semibold">Live dashboard preview</div>
                        <div className="text-xs text-muted-foreground">See analytics, ops, and trends in one view</div>
                      </div>
                    </div>
                    <Link to="/dashboard" className="hidden sm:block">
                      <Button variant="secondary" size="sm" onClick={handleViewDemo}>
                        Open Demo
                      </Button>
                    </Link>
                  </div>

                  <div className="grid grid-cols-2 gap-3 sm:gap-4">
                    {[
                      { icon: TrendingUp, title: "Revenue & ROI", desc: "Track margin drivers" },
                      { icon: Car, title: "Fleet health", desc: "Maintenance timeline" },
                      { icon: Wallet, title: "Cashflow", desc: "Payouts & expenses" },
                      { icon: MapPin, title: "Activity", desc: "Trips + location signals" },
                    ].map((item) => (
                      <div
                        key={item.title}
                        className="rounded-xl border border-border/60 bg-background/40 p-4 sm:p-5"
                      >
                        <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center mb-3">
                          <item.icon className="w-4.5 h-4.5 text-primary" />
                        </div>
                        <div className="text-sm font-semibold">{item.title}</div>
                        <div className="text-xs text-muted-foreground mt-1">{item.desc}</div>
                      </div>
                    ))}
                  </div>

                  <div className="mt-4 text-xs text-muted-foreground">
                    Not affiliated with Turo.{" "}
                    <Link to="/faqs" className="underline hover:text-foreground transition-colors">Learn more</Link>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Highlights row */}
          <div className="mt-10 sm:mt-12 grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
            {highlights.map((h) => (
              <div
                key={h.label}
                className="rounded-xl border border-border/60 bg-card/50 backdrop-blur-sm p-4 sm:p-5 flex items-center gap-3"
              >
                <div className="w-10 h-10 rounded-xl bg-primary/10 border border-primary/15 flex items-center justify-center shrink-0">
                  <h.icon className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <div className="font-semibold">{h.value}</div>
                  <div className="text-xs sm:text-sm text-muted-foreground">{h.label}</div>
                </div>
              </div>
            ))}
          </div>
          </div>
        </section>

        {/* Social proof / quick value */}
        <section className="relative pb-10 sm:pb-14 px-4 sm:px-6">
          <div className="max-w-7xl mx-auto">
            <div className="rounded-3xl border border-border/60 bg-card/50 backdrop-blur-sm p-6 sm:p-8 shadow-sm">
              <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
                <div>
                  <div className="text-sm font-semibold">Built for real operations</div>
                  <p className="text-sm sm:text-base text-muted-foreground mt-1 max-w-2xl">
                    Whether you have 1 car or 50+, Turolytics helps you stay on top of utilization, issues, and earnings—without the spreadsheet chaos.
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  {[
                    { icon: Activity, label: "Operational visibility" },
                    { icon: FileText, label: "Docs & reminders" },
                    { icon: Wallet, label: "Financial clarity" },
                  ].map((item) => (
                    <div
                      key={item.label}
                      className="inline-flex items-center gap-2 rounded-full border border-border/60 bg-background/50 px-3 py-1 text-xs text-muted-foreground"
                    >
                      <item.icon className="w-3.5 h-3.5 text-primary" />
                      {item.label}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

      {/* Features Section */}
      <section className="relative py-12 sm:py-16 px-4 sm:px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-9 sm:mb-12">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold mb-3">Everything you need to run the business</h2>
            <p className="text-muted-foreground text-sm sm:text-base max-w-2xl mx-auto">
              Clean workflows, actionable insights, and the visibility you need to scale.
            </p>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
            {features.map((feature) => (
              <div
                key={feature.title}
                className="group p-5 sm:p-6 rounded-2xl bg-card/60 backdrop-blur-sm border border-border/60 hover:border-primary/30 hover:bg-card/80 transition-all duration-300 shadow-sm"
              >
                <div className="w-11 h-11 rounded-xl bg-primary/10 border border-primary/15 flex items-center justify-center mb-4 group-hover:scale-[1.02] transition-transform">
                  <feature.icon className="w-5 h-5 text-primary" />
                </div>
                <h3 className="font-semibold text-base mb-2">{feature.title}</h3>
                <p className="text-muted-foreground text-sm leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>

          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3 text-sm text-muted-foreground">
            <Link to="/upcoming-features" className="underline hover:text-foreground transition-colors">
              See what’s coming next
            </Link>
            <span className="hidden sm:block text-border">•</span>
            <Link to="/faqs" className="underline hover:text-foreground transition-colors">
              Read FAQs (privacy + integrations)
            </Link>
          </div>
        </div>
      </section>

      {/* Integrations + data access */}
      <section className="relative py-12 sm:py-16 px-4 sm:px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-8 items-start">
            <div className="lg:col-span-5">
              <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold mb-3">Connect what you want. Keep control.</h2>
              <p className="text-muted-foreground text-sm sm:text-base leading-relaxed">
                Turolytics is designed around <span className="font-medium text-foreground">user-controlled</span> access. Optional integrations unlock deeper
                insights—without handing over your credentials.
              </p>
              <div className="mt-5 flex flex-col gap-2 text-sm text-muted-foreground">
                {[
                  { icon: Lock, text: "No Turo credentials stored on our servers" },
                  { icon: LinkIcon, text: "Integrations require explicit authorization" },
                  { icon: Shield, text: "Secrets stay in environment config (never shipped to the client)" },
                ].map((row) => (
                  <div key={row.text} className="flex items-start gap-2">
                    <row.icon className="w-4 h-4 text-primary mt-0.5 shrink-0" />
                    <span>{row.text}</span>
                  </div>
                ))}
              </div>
              <div className="mt-6">
                <Link to="/faqs">
                  <Button variant="secondary" className="gap-2">
                    Read FAQs
                    <ArrowRight className="w-4 h-4" />
                  </Button>
                </Link>
              </div>
            </div>

            <div className="lg:col-span-7 grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
              {[
                {
                  title: "Telemetry (Bouncie)",
                  desc: "Location, trips, utilization, and real-time signals via official API access.",
                  icon: MapPin,
                },
                {
                  title: "Financial insights (Plaid)",
                  desc: "Read-only visibility into payouts, expenses, and balances through Plaid.",
                  icon: Wallet,
                },
                {
                  title: "Operations dashboard",
                  desc: "Trips, tasks, and alerts—built to reduce admin time.",
                  icon: Activity,
                },
                {
                  title: "Performance analytics",
                  desc: "ROI, utilization trends, and vehicle-level profitability snapshots.",
                  icon: Gauge,
                },
              ].map((card) => (
                <div
                  key={card.title}
                  className="rounded-2xl border border-border/60 bg-card/50 backdrop-blur-sm p-6 shadow-sm"
                >
                  <div className="w-11 h-11 rounded-xl bg-primary/10 border border-primary/15 flex items-center justify-center mb-4">
                    <card.icon className="w-5 h-5 text-primary" />
                  </div>
                  <div className="font-semibold">{card.title}</div>
                  <p className="text-sm text-muted-foreground mt-2 leading-relaxed">{card.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="relative py-12 sm:py-16 px-4 sm:px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-9 sm:mb-12">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold mb-3">How it works</h2>
            <p className="text-muted-foreground text-sm sm:text-base max-w-2xl mx-auto">
              Start simple and expand as you grow. Use the demo today, then connect what you want when you’re ready.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 sm:gap-4">
            {[
              {
                title: "Explore the demo",
                desc: "See dashboards, workflows, and insights with safe mock data.",
                icon: Laptop,
              },
              {
                title: "Connect what you choose",
                desc: "Optional integrations for deeper telemetry and financial visibility.",
                icon: PlugIcon,
              },
              {
                title: "Operate with clarity",
                desc: "Make faster decisions with fleet performance and profitability in one place.",
                icon: TrendingUp,
              },
            ].map((step) => (
              <div
                key={step.title}
                className="rounded-2xl border border-border/60 bg-card/50 backdrop-blur-sm p-6 shadow-sm"
              >
                <div className="w-11 h-11 rounded-xl bg-primary/10 border border-primary/15 flex items-center justify-center mb-4">
                  <step.icon className="w-5 h-5 text-primary" />
                </div>
                <div className="font-semibold text-base">{step.title}</div>
                <p className="text-sm text-muted-foreground mt-2 leading-relaxed">{step.desc}</p>
              </div>
            ))}
          </div>

          <div className="mt-7 flex items-center justify-center gap-3">
            <Button variant="secondary" className="gap-2" onClick={handleViewDemo}>
              View Demo
              <ArrowRight className="w-4 h-4" />
            </Button>
            <Link to="/waitlist">
              <Button variant="outline">Join Waitlist</Button>
            </Link>
          </div>
        </div>
      </section>

      {/* FAQ teaser */}
      <section className="relative py-12 sm:py-16 px-4 sm:px-6">
        <div className="max-w-7xl mx-auto">
          <div className="rounded-3xl border border-border/60 bg-card/50 backdrop-blur-sm p-6 sm:p-8 shadow-sm">
            <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
              <div>
                <h3 className="text-xl sm:text-2xl font-bold mb-2">Questions about privacy or how data works?</h3>
                <p className="text-sm sm:text-base text-muted-foreground max-w-2xl">
                  We’re explicit about what we do and don’t store, how integrations work, and what’s user-controlled.
                </p>
              </div>
              <div className="flex flex-col sm:flex-row gap-3 w-full lg:w-auto">
                <Link to="/faqs" className="w-full sm:w-auto">
                  <Button className="w-full sm:w-auto gap-2">
                    View FAQs
                    <ArrowRight className="w-4 h-4" />
                  </Button>
                </Link>
                <Link to="/upcoming-features" className="w-full sm:w-auto">
                  <Button variant="outline" className="w-full sm:w-auto gap-2 bg-background/60 backdrop-blur-sm">
                    View Roadmap
                    <CalendarDays className="w-4 h-4" />
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative py-12 sm:py-16 px-4 sm:px-6">
        <div className="max-w-7xl mx-auto">
          <div className="relative overflow-hidden rounded-3xl border border-primary/20 bg-gradient-to-br from-primary/12 via-primary/6 to-transparent shadow-2xl">
            <div className="absolute inset-0 pointer-events-none">
              <div className="absolute -top-24 -right-24 w-64 h-64 bg-primary/15 rounded-full blur-3xl" />
              <div className="absolute -bottom-24 left-1/3 w-64 h-64 bg-primary/10 rounded-full blur-3xl" />
            </div>
            <div className="relative px-6 py-10 sm:px-10 sm:py-12 text-center">
              <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold mb-3">Get early access</h2>
              <p className="text-muted-foreground text-sm sm:text-base max-w-2xl mx-auto mb-6">
                Join the waitlist to be among the first hosts to use Turolytics. We’ll email you when your invite is ready.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
                <Link to="/waitlist" className="w-full sm:w-auto">
                  <Button size="lg" className="w-full sm:w-auto gap-2 h-11 sm:h-12 px-6 group">
                    Join Waitlist
                    <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                  </Button>
                </Link>
                <Button variant="outline" size="lg" className="w-full sm:w-auto h-11 sm:h-12 px-6 bg-background/60 backdrop-blur-sm" onClick={handleViewDemo}>
                  View Demo
                </Button>
              </div>
              <p className="text-xs text-muted-foreground mt-4">
                Not affiliated with Turo. Privacy details available in the <Link to="/faqs" className="underline hover:text-foreground transition-colors">FAQs</Link>.
              </p>
            </div>
          </div>
        </div>
      </section>
      </main>

      {/* Footer */}
      <footer className="relative mt-auto py-8 px-4 sm:px-6 border-t border-border/50 bg-background/30 backdrop-blur-sm">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-primary flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-xs">T</span>
            </div>
            <span className="font-semibold text-sm">Turolytics</span>
          </div>
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <Link to="/faqs" className="hover:text-foreground transition-colors">
              FAQs
            </Link>
            <Link to="/upcoming-features" className="hover:text-foreground transition-colors">
              Upcoming Features
            </Link>
            <Link to="/waitlist" className="hover:text-foreground transition-colors">
              Waitlist
            </Link>
          </div>
          <p className="text-xs text-muted-foreground">
            © {new Date().getFullYear()} Turolytics. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Landing;

function PlugIcon(props: { className?: string }) {
  // Simple inline icon to avoid importing extra Lucide icon variants.
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className={props.className}
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M9 7v6" />
      <path d="M15 7v6" />
      <path d="M7 12h10" />
      <path d="M12 12v7" />
      <path d="M10 19h4" />
    </svg>
  );
}
