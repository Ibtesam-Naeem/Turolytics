import { useState } from "react";
import { 
  Wallet, 
  Map, 
  FileText, 
  Settings, 
  Star, 
  BarChart3, 
  Wrench, 
  Receipt,
  Calculator,
  Car,
  History,
  LogOut
} from "lucide-react";
import { NavLink } from "@/components/NavLink";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

const mainItems = [
  { title: "Dashboard", url: "/dashboard", icon: BarChart3 },
  { title: "Trip History", url: "/trip-history", icon: History },
  { title: "Banking", url: "/banking", icon: Wallet },
  { title: "Map", url: "/map", icon: Map },
  { title: "Documents", url: "/documents", icon: FileText },
  { title: "Settings", url: "/settings", icon: Settings },
];

const vehicleItems = [
  { title: "Vehicle Overview", url: "/vehicles", icon: Car },
];

const analyticsItems = [
  { title: "Reviews", url: "/reviews", icon: Star },
  { title: "Analytics", url: "/analytics", icon: BarChart3 },
  { title: "ROI Calculator", url: "/roi-calculator", icon: Calculator },
];

const managementItems = [
  { title: "Maintenance", url: "/maintenance", icon: Wrench },
  { title: "Expense Tracking", url: "/expense-tracking", icon: Receipt },
];

export function AppSidebar() {
  const { open } = useSidebar();
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();
  const currentPath = location.pathname;
  const [showLogoutDialog, setShowLogoutDialog] = useState(false);

  const isActive = (path: string) => {
    if (path === "/dashboard") return currentPath === "/dashboard";
    return currentPath.startsWith(path);
  };

  const isGroupExpanded = (items: typeof mainItems) => 
    items.some((item) => isActive(item.url));

  const handleLogout = () => {
    logout();
    navigate("/auth");
    setShowLogoutDialog(false);
  };

  return (
    <>
      <Sidebar className={open ? "w-60" : "w-14"} collapsible="icon">
        <SidebarContent className="flex flex-col h-full">
          {/* Header with Logo */}
          <Link to="/" className="block p-4 border-b border-border hover:bg-muted/50 transition-colors">
            {open ? (
              <div>
                <h2 className="text-lg font-bold text-foreground">Turolytics</h2>
                <p className="text-xs text-muted-foreground">Fleet Management</p>
              </div>
            ) : (
              <div className="flex justify-center">
                <span className="text-lg font-bold text-foreground">T</span>
              </div>
            )}
          </Link>

          {/* Main Navigation */}
          <SidebarGroup>
            <SidebarGroupLabel>Main</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {mainItems.map((item) => (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton asChild>
                      <NavLink 
                        to={item.url} 
                        end={item.url === "/dashboard"}
                        className="hover:bg-muted/50" 
                        activeClassName="bg-muted text-primary font-medium"
                      >
                        <item.icon className="h-4 w-4" />
                        {open && <span>{item.title}</span>}
                      </NavLink>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>

          {/* Vehicle Section */}
          <SidebarGroup>
            <SidebarGroupLabel>Vehicles</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {vehicleItems.map((item) => (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton asChild>
                      <NavLink 
                        to={item.url} 
                        className="hover:bg-muted/50" 
                        activeClassName="bg-muted text-primary font-medium"
                      >
                        <item.icon className="h-4 w-4" />
                        {open && <span>{item.title}</span>}
                      </NavLink>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>

          {/* Analytics Section */}
          <SidebarGroup>
            <SidebarGroupLabel>Insights</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {analyticsItems.map((item) => (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton asChild>
                      <NavLink 
                        to={item.url} 
                        className="hover:bg-muted/50" 
                        activeClassName="bg-muted text-primary font-medium"
                      >
                        <item.icon className="h-4 w-4" />
                        {open && <span>{item.title}</span>}
                      </NavLink>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>

          {/* Management Section */}
          <SidebarGroup>
            <SidebarGroupLabel>Management</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {managementItems.map((item) => (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton asChild>
                      <NavLink 
                        to={item.url} 
                        className="hover:bg-muted/50" 
                        activeClassName="bg-muted text-primary font-medium"
                      >
                        <item.icon className="h-4 w-4" />
                        {open && <span>{item.title}</span>}
                      </NavLink>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>

          {/* Spacer to push logout to bottom */}
          <div className="flex-1" />

          {/* Logout Button */}
          <SidebarGroup className="mt-auto border-t border-border">
            <SidebarGroupContent>
              <SidebarMenu>
                <SidebarMenuItem>
                  <SidebarMenuButton 
                    onClick={() => setShowLogoutDialog(true)}
                    className="hover:bg-destructive/10 hover:text-destructive transition-colors cursor-pointer"
                  >
                    <LogOut className="h-4 w-4" />
                    {open && <span>Sign Out</span>}
                  </SidebarMenuButton>
                </SidebarMenuItem>
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        </SidebarContent>
      </Sidebar>

      {/* Logout Confirmation Dialog */}
      <AlertDialog open={showLogoutDialog} onOpenChange={setShowLogoutDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              Sign out of Turolytics?
            </AlertDialogTitle>
            <AlertDialogDescription>
              You will need to sign in again to access your fleet dashboard.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleLogout} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              Sign Out
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}