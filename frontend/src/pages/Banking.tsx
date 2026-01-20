import { useState } from "react";
import { 
  Wallet, TrendingUp, TrendingDown, ArrowUpRight, ArrowDownRight, CreditCard, 
  PiggyBank, Building2, Download, Filter, Plus, Search, Car, Fuel, Wrench,
  Shield, Calendar, DollarSign, Percent, FileText, FileSpreadsheet, Receipt,
  CheckCircle2, Clock, AlertCircle
} from "lucide-react";
import { useRegionalSettings } from "@/contexts/RegionalSettingsContext";
import { formatCurrency } from "@/lib/regional-utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { 
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, Legend, CartesianGrid,
  PieChart, Pie, Cell, AreaChart, Area, BarChart, Bar
} from "recharts";

// Mock data
// Calculate totals from linked accounts
const chaseBalance = 28450;
const wellsFargoBalance = 13700;
const creditCardBalance = -2340; // negative = debt
const autoLoanBalance = -18500; // negative = debt
const autoLoanOriginal = 35000; // original loan amount

const totalBalance = chaseBalance + wellsFargoBalance + creditCardBalance + autoLoanBalance; // 21,310
const availableCash = chaseBalance + wellsFargoBalance; // 42,150 (only positive accounts)
const creditLimit = 10000; // assumed credit limit
const creditUtilization = Math.round((Math.abs(creditCardBalance) / creditLimit) * 100); // 23%

const kpiData = {
  totalBalance: availableCash, // Net worth = positive accounts only for simplicity
  availableCash: availableCash,
  mtdPayouts: 24580,
  mtdExpenses: 8420,
  netProfit: 24580 - 8420, // 16,160
  creditUtilization: creditUtilization
};

const linkedAccounts = [
  { id: 1, institution: "Chase", name: "Business Checking", type: "Chequing", available: chaseBalance, current: chaseBalance, logo: "🏦", sparkline: [28000, 29500, 27800, 30200, chaseBalance] },
  { id: 2, institution: "Wells Fargo", name: "Savings", type: "Savings", available: wellsFargoBalance, current: wellsFargoBalance, logo: "🏛️", sparkline: [12000, 12500, 13000, 13200, wellsFargoBalance] },
  { id: 3, institution: "Capital One", name: "Venture Card", type: "Credit Card", available: creditLimit - Math.abs(creditCardBalance), current: creditCardBalance, logo: "💳", sparkline: [-1800, -2100, -1950, -2200, creditCardBalance] },
  { id: 4, institution: "Tesla Finance", name: "Auto Loan - Tesla Model 3", type: "Loan", available: autoLoanOriginal, current: autoLoanBalance, logo: "🚗", sparkline: [-19200, -19000, -18800, -18650, autoLoanBalance] },
];

const payoutReconciliation = [
  // Net profit = payout amount - estimated expenses (roughly 15-20% of payout for Turo fees, taxes, etc.)
  { id: 1, date: "Nov 28", amount: 2845, trips: 8, vehicles: ["Tesla Model 3", "BMW X5"], netProfit: Math.round(2845 * 0.82), status: "matched" },
  { id: 2, date: "Nov 21", amount: 3120, trips: 12, vehicles: ["Audi A4", "Mercedes C-Class", "Tesla Model Y"], netProfit: Math.round(3120 * 0.82), status: "matched" },
  { id: 3, date: "Nov 14", amount: 2560, trips: 6, vehicles: ["BMW X5", "Tesla Model 3"], netProfit: Math.round(2560 * 0.82), status: "pending" },
  { id: 4, date: "Nov 7", amount: 2980, trips: 9, vehicles: ["Tesla Model Y", "Audi A4"], netProfit: Math.round(2980 * 0.82), status: "matched" },
];

// Expense categories - total should match mtdExpenses (8420)
const expenseCategories = [
  { name: "Fuel", value: 1450, color: "hsl(var(--chart-1))" },
  { name: "Insurance", value: 2800, color: "hsl(var(--chart-2))" },
  { name: "Maintenance", value: 1420, color: "hsl(var(--chart-3))" },
  { name: "Repairs", value: 980, color: "hsl(var(--chart-4))" },
  { name: "Cleaning", value: 680, color: "hsl(var(--primary))" },
  { name: "Registration", value: 280, color: "hsl(var(--chart-5))" },
  { name: "Other", value: 810, color: "hsl(var(--muted-foreground))" },
];
// Total: 1450 + 2800 + 1420 + 980 + 680 + 280 + 810 = 8,420 ✓

const transactions = [
  { id: 1, date: "Nov 28", merchant: "Turo Payout", amount: 2845, category: "Income", vehicle: "Multiple", turoRelated: true, type: "income" },
  { id: 2, date: "Nov 27", merchant: "Shell Gas Station", amount: -65, category: "Fuel", vehicle: "Tesla Model 3", turoRelated: true, type: "expense" },
  { id: 3, date: "Nov 27", merchant: "AutoZone", amount: -120, category: "Maintenance", vehicle: "BMW X5", turoRelated: true, type: "expense" },
  { id: 4, date: "Nov 26", merchant: "State Farm", amount: -450, category: "Insurance", vehicle: "All Vehicles", turoRelated: true, type: "expense" },
  { id: 5, date: "Nov 25", merchant: "Express Car Wash", amount: -35, category: "Cleaning", vehicle: "Mercedes C-Class", turoRelated: true, type: "expense" },
  { id: 6, date: "Nov 24", merchant: "Turo Payout", amount: 1580, category: "Income", vehicle: "Tesla Model Y", turoRelated: true, type: "income" },
  { id: 7, date: "Nov 23", merchant: "Costco Gas", amount: -78, category: "Fuel", vehicle: "Audi A4", turoRelated: true, type: "expense" },
  { id: 8, date: "Nov 22", merchant: "Discount Tire", amount: -380, category: "Repairs", vehicle: "BMW X5", turoRelated: true, type: "expense" },
];

// Monthly cashflow data - last 12 months showing realistic growth pattern
const cashflowData = [
  { month: "Dec 2023", inflow: 18200, outflow: -15200, net: 3000 },
  { month: "Jan 2024", inflow: 19500, outflow: -15800, net: 3700 },
  { month: "Feb 2024", inflow: 20100, outflow: -16200, net: 3900 },
  { month: "Mar 2024", inflow: 21800, outflow: -16800, net: 5000 },
  { month: "Apr 2024", inflow: 22500, outflow: -17200, net: 5300 },
  { month: "May 2024", inflow: 23800, outflow: -17800, net: 6000 },
  { month: "Jun 2024", inflow: 25100, outflow: -18500, net: 6600 },
  { month: "Jul 2024", inflow: 26800, outflow: -19200, net: 7600 },
  { month: "Aug 2024", inflow: 26200, outflow: -19000, net: 7200 },
  { month: "Sep 2024", inflow: 24800, outflow: -18200, net: 6600 },
  { month: "Oct 2024", inflow: 23100, outflow: -17500, net: 5600 },
  { month: "Nov 2024", inflow: 24580, outflow: -8420, net: 16160 },
];

const upcomingBills = [
  { id: 1, name: "Tesla Finance", nextPayment: "Dec 5", minPayment: 485, apr: 4.9, balance: 18500, vehicle: "Tesla Model 3" },
  { id: 2, name: "Capital One Card", nextPayment: "Dec 12", minPayment: 125, apr: 19.9, balance: 2340, vehicle: null },
  { id: 3, name: "Insurance Premium", nextPayment: "Dec 18", minPayment: 450, apr: 0, balance: 450, vehicle: "All Vehicles" },
  { id: 4, name: "BMW Financial Services", nextPayment: "Dec 20", minPayment: 520, apr: 3.9, balance: 24800, vehicle: "BMW X5" },
  { id: 5, name: "Mercedes-Benz Financial", nextPayment: "Dec 22", minPayment: 380, apr: 3.5, balance: 15200, vehicle: "Mercedes C-Class" },
];

const vehicleCosts = [
  { name: "Tesla Model 3", fuel: 0, maintenance: 120, insurance: 150, loan: 485, earnings: 3200, netProfit: 2445, image: "🚗" },
  { name: "BMW X5", fuel: 380, maintenance: 450, insurance: 180, loan: 520, earnings: 2800, netProfit: 1270, image: "🚙" },
  { name: "Mercedes C-Class", fuel: 220, maintenance: 180, insurance: 160, loan: 0, earnings: 2100, netProfit: 1540, image: "🚘" },
  { name: "Audi A4", fuel: 195, maintenance: 95, insurance: 155, loan: 380, earnings: 1950, netProfit: 1125, image: "🏎️" },
  { name: "Tesla Model Y", fuel: 0, maintenance: 85, insurance: 165, loan: 550, earnings: 2850, netProfit: 2050, image: "⚡" },
];

// formatCurrency will be imported from regional-utils

const MiniSparkline = ({ data, positive }: { data: number[], positive?: boolean }) => {
  const chartData = data.map((value, index) => ({ value, index }));
  const color = positive !== false ? "hsl(var(--success))" : "hsl(var(--destructive))";
  
  return (
    <div className="w-20 h-8">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData}>
          <Area type="monotone" dataKey="value" stroke={color} fill={color} fillOpacity={0.2} strokeWidth={1.5} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

const Banking = () => {
  const { currency } = useRegionalSettings();
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState("all");
  const [dateRange, setDateRange] = useState("30");

  const totalExpenses = expenseCategories.reduce((sum, cat) => sum + cat.value, 0);

  const filteredTransactions = transactions.filter(t => {
    const matchesSearch = t.merchant.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         t.category.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = filterType === "all" || t.type === filterType;
    return matchesSearch && matchesType;
  });

  return (
    <div className="min-h-screen bg-background">
      <div className="w-full px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Banking</h1>
            <p className="text-sm text-muted-foreground">Complete financial overview powered by Plaid</p>
          </div>
          <div className="flex gap-2 flex-wrap">
            <Button variant="outline" size="sm" className="gap-2">
              <FileText className="h-4 w-4" />
              CSV
            </Button>
            <Button variant="outline" size="sm" className="gap-2">
              <FileSpreadsheet className="h-4 w-4" />
              Excel
            </Button>
            <Button variant="outline" size="sm" className="gap-2">
              <Download className="h-4 w-4" />
              PDF
            </Button>
            <Button className="gap-2">
              <Plus className="h-4 w-4" />
              Link Account
            </Button>
          </div>
        </div>

        {/* KPI Cards - 6 per row on large screens */}
        <div className="grid gap-4 grid-cols-2 md:grid-cols-3 xl:grid-cols-6">
          <Card className="bg-gradient-to-br from-primary/10 to-primary/5 border-primary/20">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <Wallet className="h-5 w-5 text-primary" />
                <Badge variant="outline" className="text-xs text-success border-success/30">+8.2%</Badge>
              </div>
              <p className="text-xs text-muted-foreground font-medium">Total Balance</p>
              <p className="text-2xl font-bold text-foreground">{formatCurrency(kpiData.totalBalance, currency)}</p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-success/10 to-success/5 border-success/20">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <DollarSign className="h-5 w-5 text-success" />
                <Badge variant="outline" className="text-xs text-success border-success/30">+5.4%</Badge>
              </div>
              <p className="text-xs text-muted-foreground font-medium">Available Cash</p>
              <p className="text-2xl font-bold text-success">{formatCurrency(kpiData.availableCash, currency)}</p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-chart-1/10 to-chart-1/5 border-chart-1/20">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <ArrowDownRight className="h-5 w-5 text-chart-1" />
                <Badge variant="outline" className="text-xs text-success border-success/30">+12.5%</Badge>
              </div>
              <p className="text-xs text-muted-foreground font-medium">MTD Payouts</p>
              <p className="text-2xl font-bold text-foreground">{formatCurrency(kpiData.mtdPayouts, currency)}</p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-destructive/10 to-destructive/5 border-destructive/20">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <ArrowUpRight className="h-5 w-5 text-destructive" />
                <Badge variant="outline" className="text-xs text-success border-success/30">-5.3%</Badge>
              </div>
              <p className="text-xs text-muted-foreground font-medium">MTD Expenses</p>
              <p className="text-2xl font-bold text-destructive">{formatCurrency(kpiData.mtdExpenses, currency)}</p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-success/15 to-success/5 border-success/30">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <TrendingUp className="h-5 w-5 text-success" />
                <Badge variant="outline" className="text-xs text-success border-success/30">+18.2%</Badge>
              </div>
              <p className="text-xs text-muted-foreground font-medium">Net Profit</p>
              <p className="text-2xl font-bold text-success">{formatCurrency(kpiData.netProfit, currency)}</p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-warning/10 to-warning/5 border-warning/20">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <Percent className="h-5 w-5 text-warning" />
                <Badge variant="outline" className="text-xs text-success border-success/30">-2.1%</Badge>
              </div>
              <p className="text-xs text-muted-foreground font-medium">Credit Utilization</p>
              <p className="text-2xl font-bold text-warning">{kpiData.creditUtilization}%</p>
            </CardContent>
          </Card>
        </div>

        {/* Accounts Overview */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-lg">Linked Accounts</CardTitle>
                <CardDescription>Your connected financial accounts via Plaid</CardDescription>
              </div>
              <Button variant="outline" size="sm" className="gap-2">
                <Plus className="h-4 w-4" />
                Add Account
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wider">Institution</th>
                    <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wider">Account</th>
                    <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wider">Type</th>
                    <th className="text-right py-3 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wider">Available</th>
                    <th className="text-right py-3 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wider">Current</th>
                    <th className="text-right py-3 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wider">30-Day Trend</th>
                  </tr>
                </thead>
                <tbody>
                  {linkedAccounts.map((account) => (
                    <tr key={account.id} className="border-b border-border/50 hover:bg-muted/30 transition-colors">
                      <td className="py-4 px-4">
                        <div className="flex items-center gap-3">
                          <span className="text-2xl">{account.logo}</span>
                          <span className="font-medium text-foreground">{account.institution}</span>
                        </div>
                      </td>
                      <td className="py-4 px-4 text-foreground">{account.name}</td>
                      <td className="py-4 px-4">
                        <Badge variant="secondary" className="text-xs">{account.type}</Badge>
                      </td>
                      <td className="py-4 px-4 text-right font-medium text-foreground">
                        {account.type === "Credit Card" 
                          ? formatCurrency(account.available, currency) + " available"
                          : account.type === "Loan"
                            ? formatCurrency(account.available, currency) + " original"
                            : account.available > 0 
                              ? formatCurrency(account.available, currency) 
                              : "—"}
                      </td>
                      <td className={`py-4 px-4 text-right font-bold ${account.current >= 0 ? "text-success" : "text-destructive"}`}>
                        {account.current >= 0 
                          ? formatCurrency(account.current, currency) 
                          : `-${formatCurrency(Math.abs(account.current), currency)}`}
                      </td>
                      <td className="py-4 px-4 text-right">
                        <MiniSparkline data={account.sparkline} positive={account.sparkline[4] >= account.sparkline[0]} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Main Grid: Payout Reconciliation + Expense Classification */}
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Payout Reconciliation */}
          <Card className="border-2 border-primary/20 bg-gradient-to-br from-primary/5 to-transparent">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Receipt className="h-5 w-5 text-primary" />
                <CardTitle className="text-lg">Payout Reconciliation</CardTitle>
              </div>
              <CardDescription>Turo payouts matched with Plaid transactions</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {payoutReconciliation.map((payout) => (
                  <div key={payout.id} className="p-4 rounded-lg border border-border bg-card hover:bg-muted/30 transition-colors">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium text-foreground">{payout.date}</span>
                        <Badge 
                          variant={payout.status === "matched" ? "default" : "secondary"}
                          className={payout.status === "matched" ? "bg-success/20 text-success border-success/30" : ""}
                        >
                          {payout.status === "matched" ? <CheckCircle2 className="h-3 w-3 mr-1" /> : <Clock className="h-3 w-3 mr-1" />}
                          {payout.status}
                        </Badge>
                      </div>
                      <span className="text-xl font-bold text-success">{formatCurrency(payout.amount, currency)}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-4 text-muted-foreground">
                        <span>{payout.trips} trips</span>
                        <span className="text-xs">{payout.vehicles.join(", ")}</span>
                      </div>
                      <span className="text-success font-medium">Net: {formatCurrency(payout.netProfit, currency)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Expense Classification */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Expense Breakdown</CardTitle>
              <CardDescription>Spending by category this month</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="h-52 flex items-center justify-center">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={expenseCategories}
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={85}
                        paddingAngle={3}
                        dataKey="value"
                      >
                        {expenseCategories.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip 
                        formatter={(value: number) => formatCurrency(value, currency)}
                        contentStyle={{ 
                          backgroundColor: 'hsl(var(--card))', 
                          border: '1px solid hsl(var(--border))',
                          borderRadius: '8px'
                        }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="space-y-2">
                  {expenseCategories.map((category, index) => {
                    const percentage = ((category.value / totalExpenses) * 100).toFixed(1);
                    return (
                      <div key={index} className="p-2.5 rounded-lg border border-border/50 bg-muted/20 hover:bg-muted/40 transition-colors">
                        <div className="flex items-center justify-between mb-1.5">
                          <div className="flex items-center gap-2.5">
                            <div className="w-3.5 h-3.5 rounded-full shadow-sm" style={{ backgroundColor: category.color }} />
                            <span className="font-semibold text-sm text-foreground">{category.name}</span>
                          </div>
                          <span className="font-bold text-base text-foreground">{formatCurrency(category.value, currency)}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <Progress 
                            value={parseFloat(percentage)} 
                            className="flex-1 h-1.5 mr-3"
                          />
                          <span className="text-xs font-medium text-muted-foreground min-w-[3rem] text-right">
                            {percentage}%
                          </span>
                        </div>
                      </div>
                    );
                  })}
                  <div className="pt-3 mt-3 border-t-2 border-border">
                    <div className="flex items-center justify-between p-3 rounded-lg bg-destructive/10 border border-destructive/20">
                      <span className="font-bold text-base text-foreground">Total Expenses</span>
                      <span className="font-bold text-xl text-destructive">{formatCurrency(totalExpenses, currency)}</span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Cashflow Timeline */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Cashflow Timeline</CardTitle>
            <CardDescription>Monthly net cashflow over the last 12 months</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={cashflowData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="positiveGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--success))" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="hsl(var(--success))" stopOpacity={0.05}/>
                    </linearGradient>
                    <linearGradient id="negativeGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--destructive))" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="hsl(var(--destructive))" stopOpacity={0.05}/>
                    </linearGradient>
                    <linearGradient id="inflowGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--chart-1))" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="hsl(var(--chart-1))" stopOpacity={0.05}/>
                    </linearGradient>
                    <linearGradient id="outflowGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--chart-5))" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="hsl(var(--chart-5))" stopOpacity={0.05}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
                  <XAxis 
                    dataKey="month" 
                    tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }} 
                    stroke="hsl(var(--muted-foreground))"
                    angle={-45}
                    textAnchor="end"
                    height={80}
                  />
                  <YAxis 
                    tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }} 
                    stroke="hsl(var(--muted-foreground))" 
                    tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
                    width={60}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'hsl(var(--card))', 
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                    }}
                    formatter={(value: number, name: string) => {
                      if (name === 'inflow') return [formatCurrency(value, currency), 'Inflow'];
                      if (name === 'outflow') return [formatCurrency(Math.abs(value), currency), 'Outflow'];
                      return [formatCurrency(value, currency), 'Net'];
                    }}
                    labelStyle={{ fontWeight: 600, marginBottom: 4 }}
                  />
                  <Legend 
                    wrapperStyle={{ paddingTop: 20 }}
                    iconType="circle"
                    formatter={(value) => {
                      if (value === 'inflow') return 'Revenue';
                      if (value === 'outflow') return 'Expenses';
                      return 'Net Cashflow';
                    }}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="inflow" 
                    stroke="hsl(var(--chart-1))" 
                    fill="url(#inflowGradient)" 
                    strokeWidth={2}
                    name="inflow"
                    stackId="1"
                  />
                  <Area 
                    type="monotone" 
                    dataKey="outflow" 
                    stroke="hsl(var(--chart-5))" 
                    fill="url(#outflowGradient)" 
                    strokeWidth={2}
                    name="outflow"
                    stackId="1"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="net" 
                    stroke="hsl(var(--success))" 
                    strokeWidth={3}
                    dot={{ fill: 'hsl(var(--success))', r: 4, strokeWidth: 2, stroke: 'hsl(var(--card))' }}
                    activeDot={{ r: 6 }}
                    name="net"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Recent Transactions + Bills & Upcoming */}
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Recent Transactions */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <CardTitle className="text-lg">Recent Transactions</CardTitle>
                  <CardDescription>Searchable and filterable transaction history</CardDescription>
                </div>
                <div className="flex gap-2">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input 
                      placeholder="Search..." 
                      className="pl-9 w-40"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>
                  <Select value={filterType} onValueChange={setFilterType}>
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All</SelectItem>
                      <SelectItem value="income">Income</SelectItem>
                      <SelectItem value="expense">Expenses</SelectItem>
                    </SelectContent>
                  </Select>
                  <Select value={dateRange} onValueChange={setDateRange}>
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="7">Last 7 days</SelectItem>
                      <SelectItem value="30">Last 30 days</SelectItem>
                      <SelectItem value="90">Last 90 days</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-[400px] overflow-y-auto scrollbar-thin pr-2">
                {filteredTransactions.map((t) => (
                  <div key={t.id} className="flex items-center justify-between p-3 rounded-lg border border-border hover:bg-muted/30 transition-colors">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-full ${t.type === "income" ? "bg-success/10" : "bg-destructive/10"}`}>
                        {t.type === "income" ? (
                          <ArrowDownRight className="h-4 w-4 text-success" />
                        ) : (
                          <ArrowUpRight className="h-4 w-4 text-destructive" />
                        )}
                      </div>
                      <div>
                        <p className="font-medium text-foreground">{t.merchant}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant="secondary" className="text-xs">{t.category}</Badge>
                          <span className="text-xs text-muted-foreground">{t.date}</span>
                          {t.turoRelated && (
                            <Badge variant="outline" className="text-xs border-primary/30 text-primary">Turo</Badge>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className={`font-bold ${t.type === "income" ? "text-success" : "text-destructive"}`}>
                        {t.amount > 0 ? "+" : ""}{formatCurrency(Math.abs(t.amount), currency)}
                      </p>
                      <p className="text-xs text-muted-foreground">{t.vehicle}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Bills & Upcoming Payments */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <AlertCircle className="h-5 w-5 text-warning" />
                <CardTitle className="text-lg">Upcoming Bills</CardTitle>
              </div>
              <CardDescription>Plaid Liabilities & scheduled payments</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 max-h-[400px] overflow-y-auto scrollbar-thin pr-2">
                {upcomingBills.map((bill) => (
                <div key={bill.id} className="p-3 rounded-lg border border-border bg-muted/20">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-foreground text-sm">{bill.name}</span>
                    <Badge variant="outline" className="text-xs">{bill.nextPayment}</Badge>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-muted-foreground">Min Payment</span>
                      <p className="font-medium text-foreground">{formatCurrency(bill.minPayment, currency)}</p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">APR</span>
                      <p className="font-medium text-foreground">{bill.apr > 0 ? `${bill.apr}%` : "—"}</p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Balance</span>
                      <p className="font-medium text-destructive">{formatCurrency(bill.balance, currency)}</p>
                    </div>
                    {bill.vehicle && (
                      <div>
                        <span className="text-muted-foreground">Vehicle</span>
                        <p className="font-medium text-foreground truncate">{bill.vehicle}</p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Vehicle-Level Cost Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Vehicle Cost Breakdown</CardTitle>
            <CardDescription>Per-vehicle expenses and profitability this month</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
              {vehicleCosts.map((vehicle, index) => (
                <div key={index} className="p-4 rounded-xl border border-border bg-gradient-to-br from-card to-muted/20 hover:shadow-md transition-all">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-2xl">{vehicle.image}</span>
                    <span className="font-semibold text-foreground text-sm truncate">{vehicle.name}</span>
                  </div>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground flex items-center gap-1"><Fuel className="h-3 w-3" /> Fuel</span>
                      <span className="text-destructive font-medium">{vehicle.fuel > 0 ? `-${formatCurrency(vehicle.fuel, currency)}` : formatCurrency(0, currency)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground flex items-center gap-1"><Wrench className="h-3 w-3" /> Maint.</span>
                      <span className="text-destructive font-medium">-{formatCurrency(vehicle.maintenance, currency)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground flex items-center gap-1"><Shield className="h-3 w-3" /> Insurance</span>
                      <span className="text-destructive font-medium">-{formatCurrency(vehicle.insurance, currency)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground flex items-center gap-1"><CreditCard className="h-3 w-3" /> Loan</span>
                      <span className="text-destructive font-medium">{vehicle.loan > 0 ? `-${formatCurrency(vehicle.loan, currency)}` : formatCurrency(0, currency)}</span>
                    </div>
                    <div className="flex justify-between border-t border-border pt-2 mt-2">
                      <span className="text-muted-foreground">Earnings</span>
                      <span className="text-success font-medium">+{formatCurrency(vehicle.earnings, currency)}</span>
                    </div>
                    <div className="flex justify-between bg-success/10 -mx-2 px-2 py-1.5 rounded-lg">
                      <span className="font-semibold text-foreground">Net Profit</span>
                      <span className="text-success font-bold">{formatCurrency(vehicle.netProfit, currency)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Banking;
