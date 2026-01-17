import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, useNavigate } from "react-router-dom";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/AppSidebar";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import { ThemeProvider, useTheme } from "@/contexts/ThemeContext";
import { RegionalSettingsProvider } from "@/contexts/RegionalSettingsContext";
import { Eye, Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import Landing from "./pages/Landing";
import Auth from "./pages/Auth";
import ForgotPassword from "./pages/ForgotPassword";
import Index from "./pages/Index";
import Banking from "./pages/Banking";
import MapPage from "./pages/MapPage";
import Documents from "./pages/Documents";
import Settings from "./pages/Settings";
import Reviews from "./pages/Reviews";
import Analytics from "./pages/Analytics";
import Maintenance from "./pages/Maintenance";
import ExpenseTracking from "./pages/ExpenseTracking";
import ROICalculator from "./pages/ROICalculator";
import Vehicles from "./pages/Vehicles";
import VehicleDocuments from "./pages/VehicleDocuments";
import VehicleDetails from "./pages/VehicleDetails";
import TripHistory from "./pages/TripHistory";
import NotFound from "./pages/NotFound";
import BouncieCallback from "./pages/BouncieCallback";
import Waitlist from "./pages/Waitlist";
import WaitlistAdmin from "./pages/WaitlistAdmin";

const queryClient = new QueryClient();

// Demo banner component - only shows in demo mode
const DemoBanner = () => {
  const navigate = useNavigate();
  const { isDemo } = useAuth();
  
  if (!isDemo) {
    return null;
  }

  return (
    <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-xs">
      <Eye className="h-3 w-3 text-primary" />
      <span className="text-muted-foreground">Demo</span>
      <button
        onClick={() => navigate("/waitlist")}
        className="text-primary hover:underline font-medium"
      >
        Join waitlist
      </button>
    </div>
  );
};

// Theme toggle button component
const ThemeToggle = () => {
  const { resolvedTheme, setTheme } = useTheme();
  
  const toggleTheme = () => {
    if (resolvedTheme === "dark") {
      setTheme("light");
    } else {
      setTheme("dark");
    }
  };

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggleTheme}
      className="h-9 w-9"
      aria-label="Toggle theme"
    >
      {resolvedTheme === "dark" ? (
        <Sun className="h-4 w-4" />
      ) : (
        <Moon className="h-4 w-4" />
      )}
    </Button>
  );
};

// Layout wrapper for authenticated pages with sidebar
const AuthenticatedLayout = ({ children }: { children: React.ReactNode }) => (
  <SidebarProvider>
    <div className="flex min-h-screen w-full max-w-full overflow-x-hidden">
      <AppSidebar />
      <div className="flex-1 flex flex-col w-full max-w-full overflow-x-hidden">
        <header className="h-12 flex items-center gap-4 border-b border-border bg-background sticky top-0 z-20 px-4 w-full max-w-full">
          <SidebarTrigger />
          <DemoBanner />
          <div className="ml-auto">
            <ThemeToggle />
          </div>
        </header>
        <main className="flex-1 w-full max-w-full overflow-x-hidden">
          {children}
        </main>
      </div>
    </div>
  </SidebarProvider>
);

const App = () => (
  <ThemeProvider>
    <RegionalSettingsProvider>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <TooltipProvider>
            <Toaster />
            <Sonner />
            <BrowserRouter>
            <Routes>
              {/* Public routes */}
              <Route path="/" element={<Landing />} />
              <Route path="/auth" element={<Auth />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />
              <Route path="/auth/bouncie/callback" element={<BouncieCallback />} />
              <Route path="/waitlist" element={<Waitlist />} />
              <Route path="/waitlist/admin" element={<AuthenticatedLayout><WaitlistAdmin /></AuthenticatedLayout>} />
              
              {/* Authenticated routes with sidebar */}
              <Route path="/dashboard" element={<AuthenticatedLayout><Index /></AuthenticatedLayout>} />
              <Route path="/trip-history" element={<AuthenticatedLayout><TripHistory /></AuthenticatedLayout>} />
              <Route path="/banking" element={<AuthenticatedLayout><Banking /></AuthenticatedLayout>} />
              <Route path="/map" element={<AuthenticatedLayout><MapPage /></AuthenticatedLayout>} />
              <Route path="/documents" element={<AuthenticatedLayout><Documents /></AuthenticatedLayout>} />
              <Route path="/settings" element={<AuthenticatedLayout><Settings /></AuthenticatedLayout>} />
              <Route path="/reviews" element={<AuthenticatedLayout><Reviews /></AuthenticatedLayout>} />
              <Route path="/analytics" element={<AuthenticatedLayout><Analytics /></AuthenticatedLayout>} />
              <Route path="/roi-calculator" element={<AuthenticatedLayout><ROICalculator /></AuthenticatedLayout>} />
              <Route path="/maintenance" element={<AuthenticatedLayout><Maintenance /></AuthenticatedLayout>} />
              <Route path="/expense-tracking" element={<AuthenticatedLayout><ExpenseTracking /></AuthenticatedLayout>} />
              <Route path="/vehicles" element={<AuthenticatedLayout><Vehicles /></AuthenticatedLayout>} />
              <Route path="/vehicles/documents" element={<AuthenticatedLayout><VehicleDocuments /></AuthenticatedLayout>} />
              <Route path="/vehicles/details" element={<AuthenticatedLayout><VehicleDetails /></AuthenticatedLayout>} />
              
              {/* Catch-all */}
              <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </AuthProvider>
  </QueryClientProvider>
    </RegionalSettingsProvider>
  </ThemeProvider>
);

export default App;
