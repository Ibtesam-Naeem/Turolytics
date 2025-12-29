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
} from "lucide-react";
import { NavLink } from "@/components/NavLink";
import { Link, useLocation } from "react-router-dom";

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

const mainItems = [
  { title: "Dashboard", url: "/demo", icon: BarChart3 },
  { title: "Trip History", url: "/demo", icon: History },
  { title: "Banking", url: "/demo", icon: Wallet },
  { title: "Map", url: "/demo", icon: Map },
  { title: "Documents", url: "/demo", icon: FileText },
  { title: "Settings", url: "/demo", icon: Settings },
];

const vehicleItems = [
  { title: "Vehicle Overview", url: "/demo", icon: Car },
];

const analyticsItems = [
  { title: "Reviews", url: "/demo", icon: Star },
  { title: "Analytics", url: "/demo", icon: BarChart3 },
  { title: "ROI Calculator", url: "/demo", icon: Calculator },
];

const managementItems = [
  { title: "Maintenance", url: "/demo", icon: Wrench },
  { title: "Expense Tracking", url: "/demo", icon: Receipt },
];

export function DemoSidebar() {
  const { open } = useSidebar();
  const location = useLocation();
  const currentPath = location.pathname;

  const isActive = (path: string) => {
    if (path === "/demo") return currentPath === "/demo";
    return currentPath.startsWith(path);
  };

  return (
    <Sidebar className={open ? "w-60" : "w-14"} collapsible="icon">
      <SidebarContent>
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
                      end={item.url === "/demo"}
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

        {/* Sign Up CTA */}
        <div className="mt-auto border-t border-border p-4">
          {open && (
            <div className="mb-3 text-xs text-muted-foreground">
              Demo Mode
            </div>
          )}
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton asChild>
                <Link
                  to="/auth?mode=signup"
                  className="w-full hover:bg-muted/50"
                >
                  {open ? <span>Sign Up Free</span> : <span>Sign Up</span>}
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </div>
      </SidebarContent>
    </Sidebar>
  );
}








