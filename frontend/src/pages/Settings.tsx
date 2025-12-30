import { User as UserIcon, Bell, Shield, CreditCard, Car, Globe, DollarSign, Key, Trash2, Monitor, Link as LinkIcon, Building2, Check, Lock, Sparkles, Search, Loader2, RefreshCw, AlertCircle, Phone, MapPin } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { ChangePasswordDialog } from "@/components/ChangePasswordDialog";
import { bouncieService, BouncieIntegrationStatus } from "@/services/bouncie-service";
import { turoService, TuroIntegrationStatus } from "@/services/turo-service";
import { authService, User } from "@/services/auth-service";
import { useToast } from "@/hooks/use-toast";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { useTheme } from "@/contexts/ThemeContext";
import { useRegionalSettings } from "@/contexts/RegionalSettingsContext";

const countries = [
  { code: "US", name: "United States" },
  { code: "CA", name: "Canada" },
  { code: "UK", name: "United Kingdom" },
  { code: "AU", name: "Australia" },
  { code: "DE", name: "Germany" },
  { code: "FR", name: "France" },
];

const statesByCountry: Record<string, { code: string; name: string }[]> = {
  US: [
    { code: "AL", name: "Alabama" },
    { code: "AK", name: "Alaska" },
    { code: "AZ", name: "Arizona" },
    { code: "CA", name: "California" },
    { code: "CO", name: "Colorado" },
    { code: "FL", name: "Florida" },
    { code: "GA", name: "Georgia" },
    { code: "NY", name: "New York" },
    { code: "TX", name: "Texas" },
    { code: "WA", name: "Washington" },
  ],
  CA: [
    { code: "AB", name: "Alberta" },
    { code: "BC", name: "British Columbia" },
    { code: "ON", name: "Ontario" },
    { code: "QC", name: "Quebec" },
  ],
  UK: [
    { code: "ENG", name: "England" },
    { code: "SCT", name: "Scotland" },
    { code: "WLS", name: "Wales" },
    { code: "NIR", name: "Northern Ireland" },
  ],
  AU: [
    { code: "NSW", name: "New South Wales" },
    { code: "VIC", name: "Victoria" },
    { code: "QLD", name: "Queensland" },
    { code: "WA", name: "Western Australia" },
  ],
  DE: [
    { code: "BY", name: "Bavaria" },
    { code: "BE", name: "Berlin" },
    { code: "HH", name: "Hamburg" },
    { code: "NW", name: "North Rhine-Westphalia" },
  ],
  FR: [
    { code: "IDF", name: "Île-de-France" },
    { code: "PAC", name: "Provence-Alpes-Côte d'Azur" },
    { code: "ARA", name: "Auvergne-Rhône-Alpes" },
    { code: "OCC", name: "Occitanie" },
  ],
};

const Settings = () => {
  const [bouncieStatus, setBouncieStatus] = useState<BouncieIntegrationStatus | null>(null);
  const [bouncieLoading, setBouncieLoading] = useState(true);
  const [bouncieConnecting, setBouncieConnecting] = useState(false);
  const [bouncieDisconnecting, setBouncieDisconnecting] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [turoStatus, setTuroStatus] = useState<TuroIntegrationStatus | null>(null);
  const [turoLoading, setTuroLoading] = useState(true);
  const [turoConnecting, setTuroConnecting] = useState(false);
  const [turoDisconnecting, setTuroDisconnecting] = useState(false);
  const [turoConnectDialogOpen, setTuroConnectDialogOpen] = useState(false);
  const [turo2FADialogOpen, setTuro2FADialogOpen] = useState(false);
  const [turoCredentials, setTuroCredentials] = useState({ email: "", password: "" });
  const [turo2FACode, setTuro2FACode] = useState("");
  const [turoSessionId, setTuroSessionId] = useState<string | null>(null);
  const [bankingConnected, setBankingConnected] = useState(false);
  const [changePasswordOpen, setChangePasswordOpen] = useState(false);
  const [deleteAccountOpen, setDeleteAccountOpen] = useState(false);
  const [deleteAccountLoading, setDeleteAccountLoading] = useState(false);
  const [deletionReason, setDeletionReason] = useState("");
  const [deleteAccountStep, setDeleteAccountStep] = useState<1 | 2>(1);
  const { theme, setTheme } = useTheme();
  const [user, setUser] = useState<User | null>(null);
  const [userLoading, setUserLoading] = useState(true);
  const [editProfileOpen, setEditProfileOpen] = useState(false);
  const [editProfileLoading, setEditProfileLoading] = useState(false);
  const [editFormData, setEditFormData] = useState({
    firstName: "",
    lastName: "",
    phone: "",
    country: "",
    state: "",
  });
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const { distanceUnit, currency, timeFormat, setDistanceUnit, setCurrency, setTimeFormat } = useRegionalSettings();
  
  // Get tab from URL params, default to "profile"
  const [activeTab, setActiveTab] = useState(() => {
    return searchParams.get('tab') || 'profile';
  });
  
  // Sync tab with URL params when they change
  useEffect(() => {
    const tabFromUrl = searchParams.get('tab');
    if (tabFromUrl && tabFromUrl !== activeTab) {
      setActiveTab(tabFromUrl);
    }
  }, [searchParams, activeTab]);
  
  // Handle tab change - update both state and URL
  const handleTabChange = (value: string) => {
    setActiveTab(value);
    const newParams = new URLSearchParams(searchParams);
    newParams.set('tab', value);
    setSearchParams(newParams, { replace: true });
  };

  const loadBouncieStatus = async () => {
    try {
      setBouncieLoading(true);
      const status = await bouncieService.getIntegrationStatus();
      setBouncieStatus(status);
    } catch (error) {
      console.error('Failed to load Bouncie status:', error);
      // Set default status if API call fails (backend might not be running)
      setBouncieStatus({ connected: false, message: 'Unable to check status' });
    } finally {
      setBouncieLoading(false);
    }
  };

  // Check for OAuth callback results
  useEffect(() => {
    const bouncieSuccess = searchParams.get('bouncie_success');
    const bouncieError = searchParams.get('bouncie_error');
    
    if (bouncieSuccess === 'true') {
      toast({
        title: "Bouncie Connected",
        description: "Your Bouncie account has been successfully connected.",
      });
      // Remove OAuth params but keep tab param
      const newParams = new URLSearchParams(searchParams);
      newParams.delete('bouncie_success');
      setSearchParams(newParams, { replace: true });
      // Refresh status
      loadBouncieStatus();
    } else if (bouncieError) {
      toast({
        title: "Connection Failed",
        description: `Failed to connect Bouncie: ${bouncieError}`,
        variant: "destructive",
      });
      // Remove OAuth params but keep tab param
      const newParams = new URLSearchParams(searchParams);
      newParams.delete('bouncie_error');
      setSearchParams(newParams, { replace: true });
    }
  }, [searchParams, toast, setSearchParams]);

  // Load Bouncie status on mount
  useEffect(() => {
    loadBouncieStatus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Load Turo status on mount
  useEffect(() => {
    loadTuroStatus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Load user data on mount
  useEffect(() => {
    const loadUser = async () => {
      try {
        setUserLoading(true);
        const userData = await authService.getCurrentUser();
        setUser(userData);
      } catch (error) {
        console.error('Failed to load user data:', error);
        toast({
          title: "Error",
          description: "Failed to load user information.",
          variant: "destructive",
        });
      } finally {
        setUserLoading(false);
      }
    };
    loadUser();
  }, [toast]);

  const handleUpdateProfile = async () => {
    try {
      setEditProfileLoading(true);
      const updatedUser = await authService.updateProfile({
        firstName: editFormData.firstName,
        lastName: editFormData.lastName,
        phone: editFormData.phone,
        country: editFormData.country,
        state: editFormData.state,
      });
      setUser(updatedUser);
      setEditProfileOpen(false);
      toast({
        title: "Profile Updated",
        description: "Your profile information has been successfully updated.",
      });
    } catch (error) {
      console.error('Failed to update profile:', error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to update profile. Please try again.",
        variant: "destructive",
      });
    } finally {
      setEditProfileLoading(false);
    }
  };

  const availableStates = editFormData.country ? statesByCountry[editFormData.country] || [] : [];

  const loadTuroStatus = async () => {
    try {
      setTuroLoading(true);
      const status = await turoService.getIntegrationStatus();
      setTuroStatus(status);
    } catch (error) {
      console.error('Failed to load Turo status:', error);
      setTuroStatus({ connected: false, message: 'Unable to check status' });
    } finally {
      setTuroLoading(false);
    }
  };

  const handleConnectTuro = async () => {
    if (!turoCredentials.email || !turoCredentials.password) {
      toast({
        title: "Missing Credentials",
        description: "Please enter both email and password.",
        variant: "destructive",
      });
      return;
    }

    try {
      setTuroConnecting(true);
      const result = await turoService.connect(turoCredentials);
      
      if (result.requires_2fa && result.session_id) {
        // 2FA required - show 2FA dialog
        setTuroSessionId(result.session_id);
        setTuroConnectDialogOpen(false);
        setTuro2FADialogOpen(true);
        toast({
          title: "2FA Required",
          description: "Please enter the 2FA code sent to your phone.",
        });
      } else {
        // Login successful without 2FA
        toast({
          title: "Turo Connected",
          description: "Your Turo account has been successfully connected.",
        });
        setTuroConnectDialogOpen(false);
        setTuroCredentials({ email: "", password: "" });
        await loadTuroStatus();
      }
    } catch (error) {
      toast({
        title: "Connection Failed",
        description: error instanceof Error ? error.message : "Failed to connect Turo account.",
        variant: "destructive",
      });
    } finally {
      setTuroConnecting(false);
    }
  };

  const handleSubmit2FA = async () => {
    if (!turo2FACode || !turoSessionId) {
      toast({
        title: "Missing Information",
        description: "Please enter the 2FA code.",
        variant: "destructive",
      });
      return;
    }

    try {
      setTuroConnecting(true);
      const result = await turoService.submit2FA({
        session_id: turoSessionId,
        code: turo2FACode,
      });
      
      toast({
        title: "Turo Connected",
        description: "Your Turo account has been successfully connected.",
      });
      setTuro2FADialogOpen(false);
      setTuro2FACode("");
      setTuroSessionId(null);
      setTuroCredentials({ email: "", password: "" });
      await loadTuroStatus();
    } catch (error) {
      toast({
        title: "2FA Failed",
        description: error instanceof Error ? error.message : "Invalid 2FA code or session expired.",
        variant: "destructive",
      });
    } finally {
      setTuroConnecting(false);
    }
  };

  const handleDisconnectTuro = async () => {
    if (!confirm('Are you sure you want to disconnect Turo? This will remove your stored credentials.')) {
      return;
    }

    try {
      setTuroDisconnecting(true);
      await turoService.disconnect();
      toast({
        title: "Turo Disconnected",
        description: "Your Turo integration has been disconnected.",
      });
      await loadTuroStatus();
    } catch (error) {
      toast({
        title: "Disconnect Failed",
        description: error instanceof Error ? error.message : "Failed to disconnect Turo.",
        variant: "destructive",
      });
    } finally {
      setTuroDisconnecting(false);
    }
  };

  const handleDeleteAccountContinue = () => {
    if (!deletionReason.trim()) {
      toast({
        title: "Reason Required",
        description: "Please provide a reason for deleting your account.",
        variant: "destructive",
      });
      return;
    }
    setDeleteAccountStep(2);
  };

  const handleDeleteAccountConfirm = async () => {
    try {
      setDeleteAccountLoading(true);
      await authService.deleteAccount({ reason: deletionReason });
      
      toast({
        title: "Account Deleted",
        description: "Your account has been permanently deleted.",
      });
      
      // Logout and redirect
      setTimeout(() => {
        window.location.href = '/';
      }, 2000);
    } catch (error) {
      toast({
        title: "Deletion Failed",
        description: error instanceof Error ? error.message : "Failed to delete account.",
        variant: "destructive",
      });
    } finally {
      setDeleteAccountLoading(false);
      setDeleteAccountOpen(false);
      setDeletionReason("");
      setDeleteAccountStep(1);
    }
  };

  const handleConnectBouncie = async () => {
    try {
      setBouncieConnecting(true);
      // Get authorization URL and redirect to it
      const authUrl = await bouncieService.getAuthorizationUrl(false);
      // Full page redirect to Bouncie OAuth
      window.location.href = authUrl;
    } catch (error) {
      toast({
        title: "Connection Failed",
        description: error instanceof Error ? error.message : "Failed to get authorization URL.",
        variant: "destructive",
      });
      setBouncieConnecting(false);
    }
  };

  const handleDisconnectBouncie = async () => {
    if (!confirm('Are you sure you want to disconnect Bouncie? This will stop automatic trip matching.')) {
      return;
    }

    try {
      setBouncieDisconnecting(true);
      await bouncieService.disconnect();
      toast({
        title: "Bouncie Disconnected",
        description: "Your Bouncie integration has been disconnected.",
      });
      await loadBouncieStatus();
    } catch (error) {
      toast({
        title: "Disconnect Failed",
        description: error instanceof Error ? error.message : "Failed to disconnect Bouncie.",
        variant: "destructive",
      });
    } finally {
      setBouncieDisconnecting(false);
    }
  };

  const handleSyncMatches = async () => {
    try {
      setSyncing(true);
      const result = await bouncieService.syncMatches(365, true, false);
      toast({
        title: "Sync Complete",
        description: `Matched ${result.matches_created || 0} trips successfully.`,
      });
    } catch (error) {
      toast({
        title: "Sync Failed",
        description: error instanceof Error ? error.message : "Failed to sync trip matches.",
        variant: "destructive",
      });
    } finally {
      setSyncing(false);
    }
  };

  const bouncieConnected = bouncieStatus?.connected ?? false;

  return (
    <>
      <div className="min-h-screen bg-background p-6">
      <div className="mx-auto max-w-[2000px] space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Settings</h1>
          <p className="text-muted-foreground">Manage your account settings and preferences</p>
        </div>

        <Tabs value={activeTab} onValueChange={handleTabChange} className="space-y-6">
          <ScrollArea className="w-full">
            <TabsList className="inline-flex w-max lg:w-auto lg:grid lg:grid-cols-6">
              <TabsTrigger value="profile">Profile</TabsTrigger>
              <TabsTrigger value="integrations">Integrations</TabsTrigger>
              <TabsTrigger value="preferences">Preferences</TabsTrigger>
              <TabsTrigger value="security">Security</TabsTrigger>
              <TabsTrigger value="billing">Billing</TabsTrigger>
              <TabsTrigger value="account">Account</TabsTrigger>
            </TabsList>
            <ScrollBar orientation="horizontal" className="lg:hidden" />
          </ScrollArea>

          {/* Profile Tab */}
          <TabsContent value="profile" className="space-y-6">
            <div className="grid gap-6 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <UserIcon className="h-5 w-5" />
                    Profile Information
                  </CardTitle>
                  <CardDescription>Update your personal details</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {userLoading ? (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Loading profile information...
                    </div>
                  ) : (
                    <>
                      <div>
                        <Label>Full Name</Label>
                        <p className="text-sm text-muted-foreground mt-1">
                          {user?.first_name || user?.last_name
                            ? `${user?.first_name || ''} ${user?.last_name || ''}`.trim() || "Not provided"
                            : "Not provided"}
                        </p>
                      </div>
                      <div>
                        <Label>Email</Label>
                        <p className="text-sm text-muted-foreground mt-1">
                          {user?.email || "Not available"}
                        </p>
                        {user?.email_verified && (
                          <Badge variant="secondary" className="mt-1">
                            Verified
                          </Badge>
                        )}
                      </div>
                      <div>
                        <Label>Phone Number</Label>
                        <p className="text-sm text-muted-foreground mt-1">
                          {user?.phone_number || "Not provided"}
                        </p>
                      </div>
                      <div>
                        <Label>Location</Label>
                        <p className="text-sm text-muted-foreground mt-1">
                          {user?.state && user?.country
                            ? `${user.state}, ${user.country}`
                            : user?.country || user?.state || "Not provided"}
                        </p>
                      </div>
                      <div>
                        <Label>Member Since</Label>
                        <p className="text-sm text-muted-foreground mt-1">
                          {user?.created_at 
                            ? new Date(user.created_at).toLocaleDateString('en-US', { 
                                year: 'numeric', 
                                month: 'long', 
                                day: 'numeric' 
                              })
                            : "Not available"}
                        </p>
                      </div>
                      <Button 
                        variant="outline" 
                        onClick={() => {
                          setEditFormData({
                            firstName: user?.first_name || "",
                            lastName: user?.last_name || "",
                            phone: user?.phone_number || "",
                            country: user?.country || "",
                            state: user?.state || "",
                          });
                          setEditProfileOpen(true);
                        }}
                      >
                        Edit Profile
                      </Button>
                    </>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Bell className="h-5 w-5" />
                    Notifications
                  </CardTitle>
                  <CardDescription>Manage notification preferences</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Email Notifications</Label>
                      <p className="text-sm text-muted-foreground">Receive trip updates via email</p>
                    </div>
                    <Switch defaultChecked />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <Label>SMS Alerts</Label>
                      <p className="text-sm text-muted-foreground">Get text messages for important events</p>
                    </div>
                    <Switch defaultChecked />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Push Notifications</Label>
                      <p className="text-sm text-muted-foreground">Browser notifications for real-time updates</p>
                    </div>
                    <Switch />
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Integrations Tab */}
          <TabsContent value="integrations" className="space-y-6">
            <div className="grid gap-6 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Car className="h-5 w-5" />
                    Bouncie Integration
                  </CardTitle>
                  <CardDescription>Connect GPS tracking for real-time vehicle data</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {bouncieLoading ? (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Loading status...
                    </div>
                  ) : (
                    <>
                      <div className="flex items-center justify-between">
                        <div>
                          <Label>Status</Label>
                          <div className="mt-1 flex items-center gap-2">
                            <Badge variant={bouncieConnected ? "default" : "secondary"}>
                              {bouncieConnected ? "Connected" : "Not Connected"}
                            </Badge>
                            {bouncieConnected && bouncieStatus?.expired && (
                              <Badge variant="destructive">Expired</Badge>
                            )}
                          </div>
                        </div>
                      </div>
                      
                      {bouncieConnected && bouncieStatus && (
                        <div className="space-y-2 rounded-lg bg-muted p-3">
                          {bouncieStatus.bouncie_user_email && (
                            <div>
                              <p className="text-sm font-medium">Connected Account</p>
                              <p className="text-sm text-muted-foreground">{bouncieStatus.bouncie_user_email}</p>
                            </div>
                          )}
                          {bouncieStatus.expires_at && (
                            <div>
                              <p className="text-sm font-medium">Expires</p>
                              <p className="text-sm text-muted-foreground">
                                {new Date(bouncieStatus.expires_at).toLocaleDateString()}
                              </p>
                            </div>
                          )}
                        </div>
                      )}

                      {bouncieConnected && (
                        <div className="space-y-2">
                          <Button 
                            variant="outline" 
                            onClick={handleSyncMatches}
                            disabled={syncing}
                            className="w-full"
                          >
                            {syncing ? (
                              <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Syncing...
                              </>
                            ) : (
                              <>
                                <RefreshCw className="mr-2 h-4 w-4" />
                                Sync Trip Matches
                              </>
                            )}
                          </Button>
                        </div>
                      )}

                      <Button 
                        variant={bouncieConnected ? "outline" : "default"}
                        onClick={bouncieConnected ? handleDisconnectBouncie : handleConnectBouncie}
                        disabled={bouncieConnecting || bouncieDisconnecting}
                        className="w-full"
                      >
                        {bouncieConnecting ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Connecting...
                          </>
                        ) : bouncieDisconnecting ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Disconnecting...
                          </>
                        ) : bouncieConnected ? (
                          "Disconnect"
                        ) : (
                          "Connect Bouncie"
                        )}
                      </Button>
                    </>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <LinkIcon className="h-5 w-5" />
                    Turo Account
                  </CardTitle>
                  <CardDescription>Sync bookings and guest information automatically</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {turoLoading ? (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Loading status...
                    </div>
                  ) : (
                    <>
                      <div className="flex items-center justify-between">
                        <div>
                          <Label>Status</Label>
                          <div className="mt-1">
                            <Badge variant={turoStatus?.connected ? "default" : "secondary"}>
                              {turoStatus?.connected ? "Connected" : "Not Connected"}
                            </Badge>
                          </div>
                        </div>
                      </div>
                      {turoStatus?.connected && turoStatus.email && (
                        <div className="space-y-2 rounded-lg bg-muted p-3">
                          <p className="text-sm font-medium">Connected Account</p>
                          <p className="text-sm text-muted-foreground">{turoStatus.email}</p>
                        </div>
                      )}
                      <Button 
                        variant={turoStatus?.connected ? "outline" : "default"}
                        onClick={turoStatus?.connected ? handleDisconnectTuro : () => setTuroConnectDialogOpen(true)}
                        disabled={turoConnecting || turoDisconnecting}
                        className="w-full"
                      >
                        {turoConnecting ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Connecting...
                          </>
                        ) : turoDisconnecting ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Disconnecting...
                          </>
                        ) : turoStatus?.connected ? (
                          "Disconnect"
                        ) : (
                          "Connect Turo"
                        )}
                      </Button>
                    </>
                  )}
                </CardContent>
              </Card>

              {/* Turo Connect Dialog */}
              <Dialog open={turoConnectDialogOpen} onOpenChange={setTuroConnectDialogOpen}>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Connect Turo Account</DialogTitle>
                    <DialogDescription>
                      Enter your Turo email and password. Your credentials will be encrypted and stored securely.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label htmlFor="turo-email">Turo Email</Label>
                      <Input
                        id="turo-email"
                        type="email"
                        placeholder="you@example.com"
                        value={turoCredentials.email}
                        onChange={(e) => setTuroCredentials(prev => ({ ...prev, email: e.target.value }))}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="turo-password">Turo Password</Label>
                      <Input
                        id="turo-password"
                        type="password"
                        placeholder="••••••••"
                        value={turoCredentials.password}
                        onChange={(e) => setTuroCredentials(prev => ({ ...prev, password: e.target.value }))}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' && !turoConnecting) {
                            handleConnectTuro();
                          }
                        }}
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setTuroConnectDialogOpen(false)}>
                      Cancel
                    </Button>
                    <Button onClick={handleConnectTuro} disabled={turoConnecting}>
                      {turoConnecting ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Connecting...
                        </>
                      ) : (
                        "Connect"
                      )}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>


              {/* Turo 2FA Dialog */}
              <Dialog open={turo2FADialogOpen} onOpenChange={setTuro2FADialogOpen}>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Enter 2FA Code</DialogTitle>
                    <DialogDescription>
                      Please enter the 2FA code sent to your phone to complete the Turo connection.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label htmlFor="turo-2fa-code">2FA Code</Label>
                      <Input
                        id="turo-2fa-code"
                        type="text"
                        placeholder="123456"
                        value={turo2FACode}
                        onChange={(e) => setTuro2FACode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                        maxLength={6}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' && !turoConnecting && turo2FACode.length >= 4) {
                            handleSubmit2FA();
                          }
                        }}
                      />
                      <p className="text-xs text-muted-foreground">
                        Enter the 6-digit code sent to your phone
                      </p>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => {
                      setTuro2FADialogOpen(false);
                      setTuro2FACode("");
                      setTuroSessionId(null);
                    }}>
                      Cancel
                    </Button>
                    <Button onClick={handleSubmit2FA} disabled={turoConnecting || turo2FACode.length < 4}>
                      {turoConnecting ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Submitting...
                        </>
                      ) : (
                        "Submit 2FA"
                      )}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Building2 className="h-5 w-5" />
                    Banking Integration
                  </CardTitle>
                  <CardDescription>Connect for automatic transaction import</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Status</Label>
                      <div className="mt-1">
                        <Badge variant={bankingConnected ? "default" : "secondary"}>
                          {bankingConnected ? "Connected" : "Not Connected"}
                        </Badge>
                      </div>
                    </div>
                  </div>
                  {bankingConnected && (
                    <div className="space-y-2 rounded-lg bg-muted p-3">
                      <p className="text-sm font-medium">Connected Account</p>
                      <p className="text-sm text-muted-foreground">Chase •••• 4242</p>
                    </div>
                  )}
                  <Button 
                    variant={bankingConnected ? "outline" : "default"}
                    onClick={() => setBankingConnected(!bankingConnected)}
                  >
                    {bankingConnected ? "Disconnect" : "Connect Bank"}
                  </Button>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Preferences Tab */}
          <TabsContent value="preferences" className="space-y-6">
            <div className="grid gap-6 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Monitor className="h-5 w-5" />
                    Appearance
                  </CardTitle>
                  <CardDescription>Customize how Turolytics looks</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Theme</Label>
                      <p className="text-sm text-muted-foreground">Switch between light and dark mode</p>
                    </div>
                    <Select value={theme} onValueChange={(value) => setTheme(value as "light" | "dark" | "system")}>
                      <SelectTrigger className="w-32">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="light">Light</SelectItem>
                        <SelectItem value="dark">Dark</SelectItem>
                        <SelectItem value="system">System</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Globe className="h-5 w-5" />
                    Regional Settings
                  </CardTitle>
                  <CardDescription>Set your location and format preferences</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Units</Label>
                    <Select value={distanceUnit} onValueChange={(value) => setDistanceUnit(value as "km" | "miles")}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="km">Kilometers (km)</SelectItem>
                        <SelectItem value="miles">Miles (mi)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Currency</Label>
                    <Select value={currency} onValueChange={(value) => setCurrency(value as "usd" | "cad")}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="usd">USD ($)</SelectItem>
                        <SelectItem value="cad">CAD ($)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Time Format</Label>
                    <Select value={timeFormat} onValueChange={(value) => setTimeFormat(value as "12h" | "24h")}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="12h">12-hour</SelectItem>
                        <SelectItem value="24h">24-hour</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Security Tab */}
          <TabsContent value="security" className="space-y-6">
            <div className="grid gap-6 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Shield className="h-5 w-5" />
                    Password & Authentication
                  </CardTitle>
                  <CardDescription>Manage your account security</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label>Password</Label>
                    <p className="text-sm text-muted-foreground mt-1">Last changed 3 months ago</p>
                  </div>
                  <Button variant="outline" onClick={() => setChangePasswordOpen(true)}>Change Password</Button>
                  <ChangePasswordDialog open={changePasswordOpen} onOpenChange={setChangePasswordOpen} />
                  <Separator />
                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Two-Factor Authentication</Label>
                      <p className="text-sm text-muted-foreground">Add an extra layer of security</p>
                    </div>
                    <Switch />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Key className="h-5 w-5" />
                    Active Sessions
                  </CardTitle>
                  <CardDescription>Manage your active login sessions</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between rounded-lg border p-3">
                      <div>
                        <p className="text-sm font-medium">Current Session</p>
                        <p className="text-xs text-muted-foreground">Chrome on MacOS • Toronto, CA</p>
                      </div>
                      <Badge variant="secondary">Active</Badge>
                    </div>
                    <div className="flex items-center justify-between rounded-lg border p-3">
                      <div>
                        <p className="text-sm font-medium">Mobile Device</p>
                        <p className="text-xs text-muted-foreground">Safari on iPhone • 2 days ago</p>
                      </div>
                      <Button variant="ghost" size="sm">Revoke</Button>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Key className="h-5 w-5" />
                    API Keys
                  </CardTitle>
                  <CardDescription>Manage API access for integrations</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-sm text-muted-foreground">
                    Create API keys to integrate Turolytics with external services
                  </p>
                  <Button variant="outline">Generate New Key</Button>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Billing Tab */}
          <TabsContent value="billing" className="space-y-6">
            {/* Stripe Security Badge */}
            <div className="flex items-center justify-center gap-3 rounded-lg border border-border/50 bg-gradient-to-r from-[#635bff]/5 to-[#635bff]/10 p-4">
              <div className="flex items-center gap-2">
                <Lock className="h-4 w-4 text-[#635bff]" />
                <span className="text-sm text-muted-foreground">Powered by</span>
              </div>
              <div className="flex items-center gap-1.5">
                <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M13.976 9.15c-2.172-.806-3.356-1.426-3.356-2.409 0-.831.683-1.305 1.901-1.305 2.227 0 4.515.858 6.09 1.631l.89-5.494C18.252.975 15.697 0 12.165 0 9.667 0 7.589.654 6.104 1.872 4.56 3.147 3.757 4.992 3.757 7.218c0 4.039 2.467 5.76 6.476 7.219 2.585.92 3.445 1.574 3.445 2.583 0 .98-.84 1.545-2.354 1.545-1.875 0-4.965-.921-6.99-2.109l-.9 5.555C5.175 22.99 8.385 24 11.714 24c2.641 0 4.843-.624 6.328-1.813 1.664-1.305 2.525-3.236 2.525-5.732 0-4.128-2.524-5.851-6.591-7.305z" fill="#635bff"/>
                </svg>
                <span className="text-lg font-bold text-[#635bff]">stripe</span>
              </div>
            </div>

            {/* Plans */}
            <div className="grid gap-6 lg:grid-cols-3">
              {/* Free Plan */}
              <Card className="relative">
                <CardHeader>
                  <CardTitle>Free</CardTitle>
                  <CardDescription>Get started for free</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <p className="text-3xl font-bold">$0<span className="text-lg font-normal text-muted-foreground">/mo</span></p>
                    <p className="text-sm text-muted-foreground">No credit card required</p>
                  </div>
                  <Separator />
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary" />
                      <span>Up to 3 vehicles</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary" />
                      <span>Basic analytics</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary" />
                      <span>Trip tracking</span>
                    </li>
                  </ul>
                  <Button variant="outline" className="w-full" disabled>
                    Current Plan
                  </Button>
                </CardContent>
              </Card>

              {/* Monthly */}
              <Card className="relative border-primary">
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <Badge className="bg-primary">Popular</Badge>
                </div>
                <CardHeader>
                  <CardTitle>Pro Monthly</CardTitle>
                  <CardDescription>Flexible month-to-month billing</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <p className="text-3xl font-bold">TBD<span className="text-lg font-normal text-muted-foreground">/mo</span></p>
                    <p className="text-sm text-muted-foreground">Billed monthly</p>
                  </div>
                  <Separator />
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary" />
                      <span>Unlimited vehicles</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary" />
                      <span>Full analytics dashboard</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary" />
                      <span>Real-time GPS tracking</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary" />
                      <span>Expense tracking</span>
                    </li>
                    <li className="flex items-center gap-2 text-muted-foreground">
                      <Sparkles className="h-4 w-4" />
                      <span className="flex items-center gap-1">
                        Vehicle Acquisition Tool
                        <Badge variant="outline" className="ml-1 text-[10px] px-1 py-0">Coming Soon</Badge>
                      </span>
                    </li>
                  </ul>
                  <Button className="w-full">Subscribe Monthly</Button>
                </CardContent>
              </Card>

              {/* Yearly */}
              <Card className="relative">
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <Badge variant="secondary">Save 20%</Badge>
                </div>
                <CardHeader>
                  <CardTitle>Pro Yearly</CardTitle>
                  <CardDescription>Best value — 2 months free</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <p className="text-3xl font-bold">TBD<span className="text-lg font-normal text-muted-foreground">/yr</span></p>
                    <p className="text-sm text-muted-foreground">Billed annually</p>
                  </div>
                  <Separator />
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary" />
                      <span>Unlimited vehicles</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary" />
                      <span>Full analytics dashboard</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary" />
                      <span>Real-time GPS tracking</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary" />
                      <span>Expense tracking</span>
                    </li>
                    <li className="flex items-center gap-2 text-muted-foreground">
                      <Sparkles className="h-4 w-4" />
                      <span className="flex items-center gap-1">
                        Vehicle Acquisition Tool
                        <Badge variant="outline" className="ml-1 text-[10px] px-1 py-0">Coming Soon</Badge>
                      </span>
                    </li>
                  </ul>
                  <Button variant="outline" className="w-full">Subscribe Yearly</Button>
                </CardContent>
              </Card>
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CreditCard className="h-5 w-5" />
                    Payment Methods
                  </CardTitle>
                  <CardDescription>Manage your payment information</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="rounded-lg border p-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="rounded bg-muted p-2">
                          <CreditCard className="h-5 w-5" />
                        </div>
                        <div>
                          <p className="text-sm font-medium">•••• •••• •••• 4242</p>
                          <p className="text-xs text-muted-foreground">Expires 12/2026</p>
                        </div>
                      </div>
                      <Badge variant="secondary">Default</Badge>
                    </div>
                  </div>
                  <Button variant="outline" className="w-full">Add Payment Method</Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Invoice History</CardTitle>
                  <CardDescription>Download past invoices and receipts</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {[
                      { date: "Nov 1, 2025", amount: "$0.00", status: "Paid" },
                      { date: "Oct 1, 2025", amount: "$0.00", status: "Paid" },
                      { date: "Sep 1, 2025", amount: "$0.00", status: "Paid" },
                    ].map((invoice, i) => (
                      <div key={i} className="flex items-center justify-between rounded-lg border p-3">
                        <div>
                          <p className="text-sm font-medium">{invoice.date}</p>
                          <p className="text-xs text-muted-foreground">Invoice #{1000 + i}</p>
                        </div>
                        <div className="flex items-center gap-3">
                          <p className="text-sm font-medium">{invoice.amount}</p>
                          <Badge variant="secondary">{invoice.status}</Badge>
                          <Button variant="ghost" size="sm">Download</Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Account Tab */}
          <TabsContent value="account" className="space-y-6">
            <Card className="border-destructive">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-destructive">
                  <Trash2 className="h-5 w-5" />
                  Delete Account
                </CardTitle>
                <CardDescription>
                  Permanently delete your account and all associated data
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="rounded-lg bg-destructive/10 p-4 space-y-2">
                  <p className="text-sm font-medium">This action cannot be undone</p>
                  <p className="text-sm text-muted-foreground">
                    Deleting your account will permanently remove all your data including:
                  </p>
                  <ul className="text-sm text-muted-foreground list-disc list-inside space-y-1">
                    <li>All vehicle data and trip history</li>
                    <li>Financial records and invoices</li>
                    <li>Connected integrations and settings</li>
                    <li>Profile information and preferences</li>
                  </ul>
                </div>
                <Button 
                  variant="destructive" 
                  onClick={() => setDeleteAccountOpen(true)}
                >
                  Delete Account
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Delete Account Dialog */}
        <Dialog 
          open={deleteAccountOpen} 
          onOpenChange={(open) => {
            if (!open) {
              setDeleteAccountOpen(false);
              setDeleteAccountStep(1);
              setDeletionReason("");
            }
          }}
        >
          <DialogContent>
            {deleteAccountStep === 1 ? (
              <>
                <DialogHeader>
                  <DialogTitle className="flex items-center gap-2 text-destructive">
                    <Trash2 className="h-5 w-5" />
                    Delete Account
                  </DialogTitle>
                  <DialogDescription>
                    Please tell us why you're leaving. This helps us improve.
                  </DialogDescription>
                </DialogHeader>
                
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label htmlFor="deletion-reason">
                      Why are you deleting your account? <span className="text-destructive">*</span>
                    </Label>
                    <Textarea
                      id="deletion-reason"
                      placeholder="Please let us know why you're leaving (this helps us improve)..."
                      value={deletionReason}
                      onChange={(e) => setDeletionReason(e.target.value)}
                      rows={4}
                      maxLength={1000}
                      className="resize-none"
                    />
                    <p className="text-xs text-muted-foreground">
                      {deletionReason.length}/1000 characters
                    </p>
                  </div>
                  
                  <DialogFooter>
                    <Button
                      variant="outline"
                      onClick={() => {
                        setDeleteAccountOpen(false);
                        setDeleteAccountStep(1);
                        setDeletionReason("");
                      }}
                    >
                      Cancel
                    </Button>
                    <Button
                      variant="destructive"
                      onClick={handleDeleteAccountContinue}
                      disabled={!deletionReason.trim()}
                    >
                      Continue
                    </Button>
                  </DialogFooter>
                </div>
              </>
            ) : (
              <>
                <DialogHeader>
                  <DialogTitle className="flex items-center gap-2 text-destructive">
                    <AlertCircle className="h-5 w-5" />
                    Final Warning
                  </DialogTitle>
                  <DialogDescription>
                    This action cannot be undone. All your data will be permanently deleted.
                  </DialogDescription>
                </DialogHeader>
                
                <div className="space-y-4 py-4">
                  <div className="rounded-lg bg-destructive/10 border border-destructive/20 p-4 space-y-3">
                    <div className="flex items-start gap-3">
                      <AlertCircle className="h-5 w-5 text-destructive mt-0.5 flex-shrink-0" />
                      <div className="space-y-2">
                        <p className="text-sm font-semibold text-destructive">WARNING: This cannot be undone</p>
                        <p className="text-sm text-muted-foreground">
                          Deleting your account will permanently remove all your data including:
                        </p>
                        <ul className="text-sm text-muted-foreground list-disc list-inside space-y-1 ml-2">
                          <li>All vehicle data and trip history</li>
                          <li>Financial records and invoices</li>
                          <li>Connected integrations and settings</li>
                          <li>Profile information and preferences</li>
                          <li>All uploaded documents and files</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                  
                  <div className="rounded-lg bg-muted/50 p-3 border border-border">
                    <p className="text-xs font-medium text-muted-foreground mb-1">Your reason:</p>
                    <p className="text-sm text-foreground">{deletionReason}</p>
                  </div>
                  
                  <DialogFooter>
                    <Button
                      variant="outline"
                      onClick={() => setDeleteAccountStep(1)}
                      disabled={deleteAccountLoading}
                    >
                      Back
                    </Button>
                    <Button
                      variant="destructive"
                      onClick={handleDeleteAccountConfirm}
                      disabled={deleteAccountLoading}
                    >
                      {deleteAccountLoading ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Deleting...
                        </>
                      ) : (
                        "Yes, Delete My Account"
                      )}
                    </Button>
                  </DialogFooter>
                </div>
              </>
            )}
          </DialogContent>
        </Dialog>
      </div>
      </div>
      {/* Edit Profile Dialog */}
      <Dialog open={editProfileOpen} onOpenChange={setEditProfileOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Edit Profile</DialogTitle>
            <DialogDescription>
              Update your personal information. Changes will be saved immediately.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="edit-firstName">First Name</Label>
                <Input
                  id="edit-firstName"
                  value={editFormData.firstName}
                  onChange={(e) => setEditFormData({ ...editFormData, firstName: e.target.value })}
                  placeholder="John"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-lastName">Last Name</Label>
                <Input
                  id="edit-lastName"
                  value={editFormData.lastName}
                  onChange={(e) => setEditFormData({ ...editFormData, lastName: e.target.value })}
                  placeholder="Doe"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-phone">Phone Number</Label>
              <div className="relative">
                <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  id="edit-phone"
                  className="pl-9"
                  value={editFormData.phone}
                  onChange={(e) => setEditFormData({ ...editFormData, phone: e.target.value })}
                  placeholder="+1 (555) 000-0000"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Country</Label>
                <Select 
                  value={editFormData.country} 
                  onValueChange={(value) => {
                    setEditFormData({ 
                      ...editFormData, 
                      country: value,
                      state: "" // Clear state when country changes
                    });
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select country" />
                  </SelectTrigger>
                  <SelectContent>
                    {countries.map((country) => (
                      <SelectItem key={country.code} value={country.code}>
                        {country.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>State/Province</Label>
                <Select
                  value={editFormData.state}
                  onValueChange={(value) => setEditFormData({ ...editFormData, state: value })}
                  disabled={!editFormData.country}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select state" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableStates.map((state) => (
                      <SelectItem key={state.code} value={state.code}>
                        {state.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setEditProfileOpen(false)}
              disabled={editProfileLoading}
            >
              Cancel
            </Button>
            <Button
              onClick={handleUpdateProfile}
              disabled={editProfileLoading}
            >
              {editProfileLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                "Save Changes"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default Settings;
