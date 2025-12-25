import { Receipt, DollarSign, TrendingDown, PieChart, Search, Download, FileSpreadsheet, FileText, Calendar } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useState } from "react";

const ExpenseTracking = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [dateRange, setDateRange] = useState("this-month");

  const expenses = [
    { description: "Oil Change - BMW X5", category: "Maintenance", amount: 180, date: "Today", vehicle: "BMW X5" },
    { description: "Monthly Insurance Premium", category: "Insurance", amount: 2800, date: "Yesterday", vehicle: "All Vehicles" },
    { description: "Brake Pad Replacement - Audi A4", category: "Maintenance", amount: 420, date: "Nov 18", vehicle: "Audi A4" },
    { description: "Professional Detailing", category: "Cleaning", amount: 150, date: "Nov 17", vehicle: "Tesla Model 3" },
    { description: "Supercharger - Tesla Model Y", category: "Fuel", amount: 45, date: "Nov 15", vehicle: "Tesla Model Y" },
  ];

  const filteredExpenses = expenses.filter(expense => 
    expense.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
    expense.vehicle.toLowerCase().includes(searchQuery.toLowerCase()) ||
    expense.category.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="mx-auto max-w-[2000px] space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Expense Tracking</h1>
            <p className="text-sm text-muted-foreground">Monitor and manage fleet expenses</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button variant="outline" size="sm" className="gap-2">
              <FileSpreadsheet className="h-4 w-4" />
              CSV
            </Button>
            <Button variant="outline" size="sm" className="gap-2">
              <FileText className="h-4 w-4" />
              PDF
            </Button>
            <Button className="gap-2">
              <Receipt className="h-4 w-4" />
              Add Expense
            </Button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search expenses..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
          <Select value={dateRange} onValueChange={setDateRange}>
            <SelectTrigger className="w-[180px]">
              <Calendar className="h-4 w-4 mr-2" />
              <SelectValue placeholder="Date range" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="today">Today</SelectItem>
              <SelectItem value="this-week">This Week</SelectItem>
              <SelectItem value="this-month">This Month</SelectItem>
              <SelectItem value="last-month">Last Month</SelectItem>
              <SelectItem value="this-year">This Year</SelectItem>
              <SelectItem value="all-time">All Time</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Expense Overview */}
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader>
              <CardTitle>Total Expenses</CardTitle>
              <CardDescription>This month</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-foreground">$8,450</p>
              <p className="text-sm text-success flex items-center gap-1 mt-1">
                <TrendingDown className="h-4 w-4" />
                -5.3% from last month
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Maintenance</CardTitle>
              <CardDescription>Service costs</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-foreground">$3,240</p>
              <p className="text-sm text-muted-foreground mt-1">38% of total</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Insurance</CardTitle>
              <CardDescription>Monthly premiums</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-foreground">$2,800</p>
              <p className="text-sm text-muted-foreground mt-1">33% of total</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Other</CardTitle>
              <CardDescription>Misc expenses</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-foreground">$2,410</p>
              <p className="text-sm text-muted-foreground mt-1">29% of total</p>
            </CardContent>
          </Card>
        </div>

        {/* Expense Categories */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PieChart className="h-5 w-5" />
              Expense Breakdown
            </CardTitle>
            <CardDescription>Spending by category</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                { category: "Maintenance & Repairs", amount: 3240, percentage: 38, color: "bg-blue-500" },
                { category: "Insurance Premiums", amount: 2800, percentage: 33, color: "bg-green-500" },
                { category: "Fuel & Charging", amount: 1450, percentage: 17, color: "bg-yellow-500" },
                { category: "Cleaning & Detailing", amount: 680, percentage: 8, color: "bg-purple-500" },
                { category: "Registration & Fees", amount: 280, percentage: 4, color: "bg-red-500" },
              ].map((item, idx) => (
                <div key={idx}>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3">
                      <div className={`w-3 h-3 rounded-full ${item.color}`} />
                      <span className="text-sm font-medium text-foreground">{item.category}</span>
                    </div>
                    <div className="text-right">
                      <span className="font-bold text-foreground">${item.amount.toLocaleString()}</span>
                      <span className="text-sm text-muted-foreground ml-2">({item.percentage}%)</span>
                    </div>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${item.color}`} 
                      style={{ width: `${item.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Recent Expenses */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Expenses</CardTitle>
            <CardDescription>
              {filteredExpenses.length} transaction{filteredExpenses.length !== 1 ? 's' : ''} found
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {filteredExpenses.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <Receipt className="h-12 w-12 text-muted-foreground/50 mb-3" />
                  <p className="text-muted-foreground">No expenses found matching your search</p>
                </div>
              ) : (
                filteredExpenses.map((expense, idx) => (
                  <div key={idx} className="flex items-center justify-between p-4 border border-border rounded-lg hover:bg-muted/50 transition-colors">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <p className="font-medium text-foreground">{expense.description}</p>
                        <Badge variant="secondary">{expense.category}</Badge>
                      </div>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <span>{expense.vehicle}</span>
                        <span>•</span>
                        <span>{expense.date}</span>
                      </div>
                    </div>
                    <p className="font-bold text-destructive">-${expense.amount}</p>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ExpenseTracking;