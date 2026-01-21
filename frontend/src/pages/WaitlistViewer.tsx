import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Lock, LogOut, Download } from "lucide-react";
import { waitlistViewerService, WaitlistEntry } from "@/services/waitlist-viewer-service";
import { format } from "date-fns";

const WaitlistViewer = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [entries, setEntries] = useState<WaitlistEntry[]>([]);
  const [loadingEntries, setLoadingEntries] = useState(false);

  // Make this page non-indexable (best-effort for SPA routes).
  useEffect(() => {
    const metaName = "robots";
    const content = "noindex, nofollow, noarchive, nosnippet";

    const existing = document.querySelector(`meta[name="${metaName}"]`) as HTMLMetaElement | null;
    const created = !existing;
    const meta = existing ?? document.createElement("meta");

    meta.setAttribute("name", metaName);
    meta.setAttribute("content", content);
    if (created) document.head.appendChild(meta);

    return () => {
      // Only remove if we created it (avoid impacting other routes).
      if (created) meta.remove();
    };
  }, []);

  // Check if already authenticated on mount
  useEffect(() => {
    checkAuth();
  }, []);

  // Load entries when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      loadEntries();
    }
  }, [isAuthenticated]);

  const checkAuth = async () => {
    try {
      const result = await waitlistViewerService.checkAuth();
      if (result.authenticated) {
        setIsAuthenticated(true);
      }
    } catch (error) {
      // Not authenticated, show login form
      setIsAuthenticated(false);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password.trim()) {
      toast.error("Please enter a password");
      return;
    }

    setLoading(true);
    try {
      // Send password as-is (no trimming) to match server-side comparison
      const result = await waitlistViewerService.authenticate(password.trim());
      if (result.authenticated) {
        setIsAuthenticated(true);
        setPassword("");
        toast.success("Authentication successful");
      } else {
        toast.error(result.message || "Invalid password");
      }
    } catch (error) {
      toast.error("Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await waitlistViewerService.logout();
      setIsAuthenticated(false);
      setEntries([]);
      toast.success("Logged out successfully");
    } catch (error) {
      toast.error("Failed to logout");
    }
  };

  const loadEntries = async () => {
    setLoadingEntries(true);
    try {
      const result = await waitlistViewerService.getEntries();
      if (result.success && result.entries) {
        setEntries(result.entries);
      } else {
        toast.error("Failed to load entries");
      }
    } catch (error) {
      toast.error("Failed to load waitlist entries");
    } finally {
      setLoadingEntries(false);
    }
  };

  const exportCSV = () => {
    const headers = [
      "Email",
      "Vehicle Count",
      "Tracking Product",
      "Tracking Product Other",
      "Would Use",
      "Price Willing",
      "Feedback",
      "Created At",
      "Notified At"
    ];
    const rows = entries.map(e => [
      e.email,
      e.vehicle_count || "",
      e.tracking_product || "",
      e.tracking_product_other || "",
      e.would_use || "",
      e.price_willing || "",
      e.feedback || "",
      e.created_at ? format(new Date(e.created_at), "yyyy-MM-dd HH:mm") : "",
      e.notified_at ? format(new Date(e.notified_at), "yyyy-MM-dd HH:mm") : ""
    ]);
    
    const csv = [headers, ...rows].map(row => 
      row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(",")
    ).join("\n");
    
    const blob = new Blob([csv], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `waitlist-${new Date().toISOString().split("T")[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-4">
        <Card className="w-full max-w-md">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Lock className="w-5 h-5" />
              <CardTitle>Waitlist Viewer Access</CardTitle>
            </div>
            <CardDescription>
              Enter the password to view waitlist entries
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleLogin} className="space-y-4">
              <div className="space-y-2">
                <Input
                  type="password"
                  placeholder="Enter password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoFocus
                  disabled={loading}
                />
              </div>
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? "Authenticating..." : "Authenticate"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-4 sm:p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-3xl font-bold">Waitlist Entries</h1>
            <p className="text-muted-foreground">View all users who signed up for the waitlist</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={exportCSV}>
              <Download className="w-4 h-4 mr-2" />
              Export CSV
            </Button>
            <Button variant="outline" onClick={handleLogout}>
              <LogOut className="w-4 h-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>All Waitlist Entries</CardTitle>
            <CardDescription>
              Total: {entries.length} entries
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loadingEntries ? (
              <div className="text-center py-8">Loading entries...</div>
            ) : entries.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">No entries found</div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Email</TableHead>
                      <TableHead>Vehicle Count</TableHead>
                      <TableHead>Tracking Product</TableHead>
                      <TableHead>Would Use</TableHead>
                      <TableHead>Price Willing</TableHead>
                      <TableHead>Created At</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {entries.map((entry) => (
                      <TableRow key={entry.id}>
                        <TableCell className="font-medium">{entry.email}</TableCell>
                        <TableCell>{entry.vehicle_count || "-"}</TableCell>
                        <TableCell>
                          {entry.tracking_product || "-"}
                          {entry.tracking_product_other && (
                            <span className="text-xs text-muted-foreground ml-1">
                              ({entry.tracking_product_other})
                            </span>
                          )}
                        </TableCell>
                        <TableCell>{entry.would_use || "-"}</TableCell>
                        <TableCell>{entry.price_willing || "-"}</TableCell>
                        <TableCell>
                          {entry.created_at
                            ? format(new Date(entry.created_at), "MMM d, yyyy HH:mm")
                            : "-"}
                        </TableCell>
                        <TableCell>
                          {entry.notified_at ? (
                            <Badge variant="default">Notified</Badge>
                          ) : (
                            <Badge variant="outline">Pending</Badge>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>

        {entries.some(e => e.feedback) && (
          <Card>
            <CardHeader>
              <CardTitle>Feedback</CardTitle>
              <CardDescription>User feedback and suggestions</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {entries
                  .filter(e => e.feedback)
                  .map((entry) => (
                    <div key={entry.id} className="border-b border-border pb-4 last:border-0 last:pb-0">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <p className="font-medium text-sm mb-1">{entry.email}</p>
                          <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                            {entry.feedback}
                          </p>
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {entry.created_at
                            ? format(new Date(entry.created_at), "MMM d, yyyy")
                            : ""}
                        </span>
                      </div>
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default WaitlistViewer;
