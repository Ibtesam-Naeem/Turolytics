import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { toast } from "sonner";
import { Search, Send, ChevronLeft, Download } from "lucide-react";
import { waitlistAdminService, WaitlistEntry } from "@/services/waitlist-admin-service";
import { format } from "date-fns";

const WaitlistAdmin = () => {
  const navigate = useNavigate();
  const [entries, setEntries] = useState<WaitlistEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 50;

  useEffect(() => {
    loadEntries();
  }, [page, search]);

  const loadEntries = async () => {
    setLoading(true);
    try {
      const result = await waitlistAdminService.getEntries(page, pageSize, search);
      if (result.success) {
        setEntries(result.entries || []);
        setTotal(result.total || 0);
      }
    } catch (error) {
      toast.error("Failed to load waitlist entries");
    } finally {
      setLoading(false);
    }
  };

  const handleSendBulk = async () => {
    if (!confirm("Send launch email to all waitlist members who haven't been notified yet?")) {
      return;
    }

    setSending(true);
    try {
      const result = await waitlistAdminService.sendBulkEmail();
      if (result.success) {
        toast.success(
          `Sent to ${result.sent_count} recipients. ${result.failed_count} failed.`
        );
        loadEntries(); // Refresh to show updated notified_at
      } else {
        toast.error(result.message || "Failed to send bulk email");
      }
    } catch (error) {
      toast.error("Failed to send bulk email");
    } finally {
      setSending(false);
    }
  };

  const exportCSV = () => {
    const headers = ["Email", "Vehicle Count", "Tracking Product", "Would Use", "Price Willing", "Created At", "Notified At"];
    const rows = entries.map(e => [
      e.email,
      e.vehicle_count || "",
      e.tracking_product || "",
      e.would_use || "",
      e.price_willing || "",
      e.created_at ? format(new Date(e.created_at), "yyyy-MM-dd HH:mm") : "",
      e.notified_at ? format(new Date(e.notified_at), "yyyy-MM-dd HH:mm") : ""
    ]);
    
    const csv = [headers, ...rows].map(row => row.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `waitlist-${new Date().toISOString().split("T")[0]}.csv`;
    a.click();
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => navigate(-1)}>
            <ChevronLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <div>
            <h1 className="text-3xl font-bold">Waitlist Admin</h1>
            <p className="text-muted-foreground">Manage waitlist entries and send launch emails</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={exportCSV}>
            <Download className="w-4 h-4 mr-2" />
            Export CSV
          </Button>
          <Button onClick={handleSendBulk} disabled={sending}>
            <Send className="w-4 h-4 mr-2" />
            {sending ? "Sending..." : "Send Launch Email"}
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Waitlist Entries</CardTitle>
              <CardDescription>
                Total: {total} entries
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="Search by email..."
                  value={search}
                  onChange={(e) => {
                    setSearch(e.target.value);
                    setPage(1);
                  }}
                  className="pl-10 w-64"
                />
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8">Loading...</div>
          ) : entries.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">No entries found</div>
          ) : (
            <>
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
                      <TableCell>{entry.tracking_product || "-"}</TableCell>
                      <TableCell>{entry.would_use || "-"}</TableCell>
                      <TableCell>{entry.price_willing || "-"}</TableCell>
                      <TableCell>
                        {format(new Date(entry.created_at), "MMM d, yyyy HH:mm")}
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
              <div className="flex items-center justify-between mt-4">
                <div className="text-sm text-muted-foreground">
                  Page {page} of {Math.ceil(total / pageSize)}
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => p + 1)}
                    disabled={page >= Math.ceil(total / pageSize)}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default WaitlistAdmin;
