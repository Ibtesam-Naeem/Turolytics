import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ChevronDown, ChevronLeft, Shield, ArrowRight, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface FAQItem {
  question: string;
  answer: string | string[];
}

const faqs: FAQItem[] = [
  {
    question: "What is Turolytics?",
    answer:
      "Turolytics is a fleet and business management dashboard built for Turo hosts. It helps you track vehicle performance, utilization, operations, and financial insights—without living in spreadsheets.",
  },
  {
    question: "Is this officially affiliated with Turo?",
    answer:
      "No. Turolytics is an independent third-party product and is not affiliated with, endorsed by, or partnered with Turo.",
  },
  {
    question: "How does the platform access my Turo data?",
    answer: [
      "Data is collected in user-controlled ways only:",
      "• A Chrome extension that runs locally in your browser",
      "• User-initiated imports from your device/session",
      "We do not perform automated server-side scraping of user accounts.",
    ],
  },
  {
    question: "Do you store my Turo login credentials?",
    answer:
      "No. Your Turo credentials are never stored on our servers. Authentication and data access happen on your side, and your sensitive credentials remain under your control.",
  },
  {
    question: "What data do you store?",
    answer: [
      "We store only what's needed to power the dashboard features you use, such as:",
      "• Vehicle and performance metrics",
      "• Trip summaries and aggregates",
      "• Financial aggregates (if you connect a financial integration)",
      "• Telemetry data (if you connect a telemetry integration)",
      "We avoid collecting unnecessary personal information.",
    ],
  },
  {
    question: "How does Plaid work?",
    answer: [
      "If you choose to connect Plaid:",
      "• Plaid handles bank authentication directly",
      "• We never see or store your banking login details",
      "• We use Plaid for read-only insights (payouts, expenses, balances)",
    ],
  },
  {
    question: "How does the Bouncie integration work?",
    answer:
      "If you connect Bouncie, vehicle telemetry (location, trips, utilization) is pulled via the official Bouncie API based on what you authorize. You can disconnect at any time.",
  },
  {
    question: "Is my data secure?",
    answer: [
      "We take security seriously:",
      "• Integrations require explicit user authorization",
      "• Secrets are kept in environment configuration (never shipped to the client)",
      "• Access is scoped and controlled",
      "If you need more detail on specific controls, contact us and we'll share what we can.",
    ],
  },
  {
    question: "Why does the demo data look strange or unrealistic?",
    answer:
      "The demo uses mock data to showcase features safely. Some numbers won't align perfectly by design. Real data appears only when a user connects their own accounts and integrations.",
  },
];

const FAQAccordion = ({
  item,
  isOpen,
  onToggle,
}: {
  item: FAQItem;
  isOpen: boolean;
  onToggle: () => void;
}) => (
  <div className="border-b border-border/50 last:border-b-0">
    <button onClick={onToggle} className="w-full flex items-center justify-between py-5 text-left group">
      <span className="font-medium text-base sm:text-[15px] text-foreground group-hover:text-primary transition-colors pr-4">
        {item.question}
      </span>
      <ChevronDown
        className={`w-5 h-5 text-muted-foreground shrink-0 transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`}
      />
    </button>
    <div className={`overflow-hidden transition-all duration-200 ${isOpen ? "max-h-96 pb-5" : "max-h-0"}`}>
      <div className="text-muted-foreground text-sm sm:text-[15px] leading-relaxed">
        {Array.isArray(item.answer) ? (
          <div className="space-y-2">
            {item.answer.map((line, i) => (
              <p key={i}>{line}</p>
            ))}
          </div>
        ) : (
          <p>{item.answer}</p>
        )}
      </div>
    </div>
  </div>
);

const FAQs = () => {
  const allIndexes = useMemo(() => faqs.map((_, i) => i), []);
  const [openIndexes, setOpenIndexes] = useState<number[]>(allIndexes);

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
            FAQs
          </div>
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight text-foreground mb-4">
            Frequently Asked Questions
          </h1>
          <p className="text-base sm:text-lg text-muted-foreground max-w-2xl mx-auto">
            Quick answers about how Turolytics works, privacy, and integrations.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8 items-start">
          {/* Left: Trust card */}
          <Card className="lg:sticky lg:top-6 border-primary/15 bg-card/70 backdrop-blur-sm shadow-xl">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2">
                <span className="inline-flex items-center justify-center w-9 h-9 rounded-lg bg-primary/10 border border-primary/15">
                  <Shield className="w-5 h-5 text-primary" />
                </span>
                Trust & Transparency
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground space-y-3">
              <p>Not affiliated with Turo. We focus on user-controlled data access and practical security.</p>
              <div className="flex flex-col gap-2">
                <Button variant="secondary" onClick={() => setOpenIndexes(allIndexes)} className="justify-between">
                  Expand all
                  <ChevronDown className="w-4 h-4" />
                </Button>
                <Button variant="ghost" onClick={() => setOpenIndexes([])} className="justify-between">
                  Collapse all
                  <ChevronDown className="w-4 h-4 rotate-180" />
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Right: FAQ list */}
          <div className="lg:col-span-2">
            <Card className="border-border/50 bg-card/60 backdrop-blur-sm shadow-2xl">
              <CardContent className="p-4 sm:p-6">
                {faqs.map((faq, index) => (
                  <FAQAccordion
                    key={index}
                    item={faq}
                    isOpen={openIndexes.includes(index)}
                    onToggle={() =>
                      setOpenIndexes((prev) =>
                        prev.includes(index) ? prev.filter((i) => i !== index) : [...prev, index],
                      )
                    }
                  />
                ))}
              </CardContent>
            </Card>

            {/* CTA Section */}
            <div className="mt-6 sm:mt-8">
              <Card className="border-primary/20 bg-gradient-to-br from-primary/10 via-primary/5 to-transparent shadow-xl">
                <CardContent className="p-6 sm:p-8 text-center">
                  <p className="text-muted-foreground mb-5">
                    Still have questions? Join the waitlist and we'll follow up with details.
                  </p>
                  <Link to="/waitlist">
                    <Button size="lg" className="gap-2 group">
                      Join Waitlist
                      <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            </div>

            {/* Footer */}
            <div className="mt-10 pt-6 border-t border-border/30 text-center">
              <p className="text-xs text-muted-foreground">© {new Date().getFullYear()} Turolytics. All rights reserved.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FAQs;

