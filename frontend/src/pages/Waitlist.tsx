import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Bell, Car, DollarSign, MessageSquare, Radio, Sparkles, CheckCircle2, ArrowRight, ChevronLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { waitlistService } from "@/services/waitlist-service";

const Waitlist = () => {
  const navigate = useNavigate();
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [position, setPosition] = useState<number | null>(null);
  const [total, setTotal] = useState<number | null>(null);
  const [formData, setFormData] = useState({
    email: "",
    vehicleCount: "",
    trackingProduct: "",
    trackingProductOther: "",
    wouldUse: "",
    priceWilling: "",
    feedback: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.email || !formData.email.includes("@")) {
      toast.error("Please enter a valid email address");
      return;
    }

    setIsLoading(true);
    
    try {
      const result = await waitlistService.joinWaitlist({
        email: formData.email,
        vehicleCount: formData.vehicleCount || null,
        trackingProduct: formData.trackingProduct || null,
        trackingProductOther: formData.trackingProductOther || null,
        wouldUse: formData.wouldUse || null,
        priceWilling: formData.priceWilling || null,
        feedback: formData.feedback || null,
      });

      if (result.error) {
        toast.error(result.error);
        setIsLoading(false);
        return;
      }

      setPosition(result.position || null);
      setTotal(result.total || null);
      setIsSubmitted(true);
      toast.success("You're on the list! We'll notify you when we launch.");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "An unexpected error occurred");
      setIsLoading(false);
    }
  };

  if (isSubmitted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5 flex items-center justify-center p-4">
        {/* Back Button */}
        <div className="absolute top-4 left-4 z-10">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate(-1)}
            className="gap-2 text-muted-foreground hover:text-foreground"
          >
            <ChevronLeft className="w-4 h-4" />
            Back
          </Button>
        </div>

        <Card className="w-full max-w-md text-center border-primary/20 shadow-2xl">
          <CardContent className="pt-12 pb-8 px-8">
            <div className="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle2 className="w-10 h-10 text-primary" />
            </div>
            <h2 className="text-2xl font-bold mb-3">You're on the list!</h2>
            {position && (
              <div className="mb-4 p-4 bg-primary/10 border border-primary/20 rounded-lg">
                <p className="text-lg font-semibold text-primary">
                  You're #{position}{total ? ` of ${total} people` : ''} on the waitlist
                </p>
              </div>
            )}
            <p className="text-muted-foreground mb-6">
              Thanks for your interest! We'll send you an email as soon as we launch.
            </p>
            <div className="p-4 bg-muted/50 rounded-lg mb-6">
              <p className="text-sm text-muted-foreground">
                Signed up as: <span className="font-medium text-foreground">{formData.email}</span>
              </p>
            </div>
            <Button
              variant="outline"
              className="w-full"
              onClick={() => navigate(-1)}
            >
              Go Back
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5">
      {/* Back Button */}
      <div className="relative z-10 pt-4 px-4 sm:px-6">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate(-1)}
          className="gap-2 text-muted-foreground hover:text-foreground"
        >
          <ChevronLeft className="w-4 h-4" />
          Back
        </Button>
      </div>

      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-grid-pattern opacity-5" />
        <div className="absolute top-0 right-0 w-96 h-96 bg-primary/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-primary/5 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2" />
        
        <div className="relative max-w-4xl mx-auto px-4 py-16 sm:py-24">
          {/* Badge */}
          <div className="flex justify-center mb-8">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20">
              <Sparkles className="w-4 h-4 text-primary" />
              <span className="text-sm font-medium text-primary">Coming Soon</span>
            </div>
          </div>

          {/* Title */}
          <div className="text-center mb-12">
            <h1 className="text-4xl sm:text-5xl font-bold tracking-tight mb-4">
              Fleet Management,{" "}
              <span className="text-primary">Simplified</span>
            </h1>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Join the waitlist to be the first to know when we launch. 
              Help us build the perfect tool for your fleet.
            </p>
          </div>

          {/* Form Card */}
          <Card className="max-w-2xl mx-auto border-border/50 shadow-xl bg-card/80 backdrop-blur-sm">
            <CardHeader className="text-center pb-2">
              <CardTitle className="flex items-center justify-center gap-2 text-xl">
                <Bell className="w-5 h-5 text-primary" />
                Get Notified
              </CardTitle>
              <CardDescription>
                Enter your email to join the waitlist. All other fields are optional.
              </CardDescription>
            </CardHeader>
            
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Email - Required */}
                <div className="space-y-2">
                  <Label htmlFor="email" className="flex items-center gap-1">
                    Email Address <span className="text-destructive">*</span>
                  </Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="you@example.com"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="h-12"
                    required
                  />
                </div>

                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-border" />
                  </div>
                  <div className="relative flex justify-center text-xs uppercase">
                    <span className="bg-card px-2 text-muted-foreground">Optional Information</span>
                  </div>
                </div>

                {/* Vehicle Count */}
                <div className="space-y-2">
                  <Label htmlFor="vehicleCount" className="flex items-center gap-2">
                    <Car className="w-4 h-4 text-muted-foreground" />
                    How many vehicles are in your fleet?
                  </Label>
                  <Select
                    value={formData.vehicleCount}
                    onValueChange={(value) => setFormData({ ...formData, vehicleCount: value })}
                  >
                    <SelectTrigger className="h-12">
                      <SelectValue placeholder="Select fleet size" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1-5">1-5 vehicles</SelectItem>
                      <SelectItem value="6-10">6-10 vehicles</SelectItem>
                      <SelectItem value="11-25">11-25 vehicles</SelectItem>
                      <SelectItem value="26-50">26-50 vehicles</SelectItem>
                      <SelectItem value="50+">50+ vehicles</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Tracking Product */}
                <div className="space-y-3">
                  <Label className="flex items-center gap-2">
                    <Radio className="w-4 h-4 text-muted-foreground" />
                    What tracking product do you use?
                  </Label>
                  <RadioGroup
                    value={formData.trackingProduct}
                    onValueChange={(value) => setFormData({ ...formData, trackingProduct: value })}
                    className="grid gap-3"
                  >
                    <div className="flex items-center space-x-3">
                      <RadioGroupItem value="bouncie" id="bouncie" />
                      <Label htmlFor="bouncie" className="font-normal cursor-pointer">Bouncie</Label>
                    </div>
                    <div className="flex items-center space-x-3">
                      <RadioGroupItem value="built-in" id="built-in" />
                      <Label htmlFor="built-in" className="font-normal cursor-pointer">Built-in car software</Label>
                    </div>
                    <div className="flex items-center space-x-3">
                      <RadioGroupItem value="other" id="other" />
                      <Label htmlFor="other" className="font-normal cursor-pointer">Other</Label>
                    </div>
                  </RadioGroup>
                  
                  {formData.trackingProduct === "other" && (
                    <Input
                      placeholder="Please specify..."
                      value={formData.trackingProductOther}
                      onChange={(e) => setFormData({ ...formData, trackingProductOther: e.target.value })}
                      className="mt-2 ml-6"
                    />
                  )}
                </div>

                {/* Would Use */}
                <div className="space-y-3">
                  <Label className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-muted-foreground" />
                    Do you see yourself using this for your fleet?
                  </Label>
                  <RadioGroup
                    value={formData.wouldUse}
                    onValueChange={(value) => setFormData({ ...formData, wouldUse: value })}
                    className="flex flex-wrap gap-3"
                  >
                    {["Definitely", "Probably", "Maybe", "Not sure"].map((option) => {
                      const value = option.toLowerCase().replace(/\s+/g, "-");
                      const isSelected = formData.wouldUse === value;
                      return (
                        <div key={option} className="flex items-center">
                          <RadioGroupItem value={value} id={value} className="sr-only peer" />
                          <Label
                            htmlFor={value}
                            className={cn(
                              "px-4 py-2 rounded-full border cursor-pointer transition-all",
                              "hover:bg-muted/50 peer-focus-visible:ring-2 peer-focus-visible:ring-ring peer-focus-visible:ring-offset-2",
                              isSelected
                                ? "bg-primary/10 border-primary text-primary"
                                : "border-border"
                            )}
                          >
                            {option}
                          </Label>
                        </div>
                      );
                    })}
                  </RadioGroup>
                </div>

                {/* Price Willing to Pay */}
                <div className="space-y-2">
                  <Label htmlFor="priceWilling" className="flex items-center gap-2">
                    <DollarSign className="w-4 h-4 text-muted-foreground" />
                    How much would you pay for this? (per month)
                  </Label>
                  <Select
                    value={formData.priceWilling}
                    onValueChange={(value) => setFormData({ ...formData, priceWilling: value })}
                  >
                    <SelectTrigger className="h-12">
                      <SelectValue placeholder="Select a price range" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="free">Free only</SelectItem>
                      <SelectItem value="1-10">$1 - $10</SelectItem>
                      <SelectItem value="11-25">$11 - $25</SelectItem>
                      <SelectItem value="26-50">$26 - $50</SelectItem>
                      <SelectItem value="51-100">$51 - $100</SelectItem>
                      <SelectItem value="100+">$100+</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Feedback */}
                <div className="space-y-2">
                  <Label htmlFor="feedback" className="flex items-center gap-2">
                    <MessageSquare className="w-4 h-4 text-muted-foreground" />
                    Any suggestions or feedback?
                  </Label>
                  <Textarea
                    id="feedback"
                    placeholder="Tell us what features you'd love to see, or any other thoughts..."
                    value={formData.feedback}
                    onChange={(e) => setFormData({ ...formData, feedback: e.target.value })}
                    className="min-h-[100px] resize-none"
                  />
                </div>

                {/* Submit Button */}
                <Button 
                  type="submit" 
                  className="w-full h-12 text-base font-medium gap-2"
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                      Joining...
                    </>
                  ) : (
                    <>
                      Join the Waitlist
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </Button>

                {/* Not Now Button */}
                <Button
                  type="button"
                  variant="ghost"
                  className="w-full h-11 text-base"
                  onClick={() => navigate(-1)}
                >
                  Not Now
                </Button>

                <p className="text-xs text-center text-muted-foreground">
                  We respect your privacy. No spam, ever.
                </p>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Waitlist;
