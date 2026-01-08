import { useState, useEffect } from "react";
import { 
  Star, 
  MessageSquare, 
  Search, 
  Car, 
  ExternalLink, 
  Filter, 
  X, 
  Loader2,
  TrendingUp,
  CheckCircle2,
  Clock,
  AlertCircle,
  ChevronDown,
  Sparkles
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { reviewsService, Review } from "@/services/reviews-service";
import { formatDistanceToNow, format } from "date-fns";
import { cn } from "@/lib/utils";

const Reviews = () => {
  const [selectedRating, setSelectedRating] = useState<number | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalReviews, setTotalReviews] = useState(0);
  const [sortBy, setSortBy] = useState<string>("recent");
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState<string>("all");
  const [limit] = useState(50);
  const [offset, setOffset] = useState(0);

  // Fetch reviews from API
  useEffect(() => {
    const loadReviews = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await reviewsService.getReviews({
          min_rating: selectedRating || undefined,
          limit,
          offset: 0,
        });
        setReviews(response.reviews);
        setTotalReviews(response.total);
        setOffset(0);
      } catch (err) {
        console.error("Error loading reviews:", err);
        setError("Failed to load reviews. Please try again.");
      } finally {
        setIsLoading(false);
      }
    };

    loadReviews();
  }, [selectedRating, limit]);

  // Calculate statistics
  const validRatings = reviews.filter(r => r.rating != null && r.rating > 0 && r.rating <= 5);
  const averageRating = validRatings.length > 0
    ? validRatings.reduce((sum, r) => sum + (r.rating || 0), 0) / validRatings.length
    : 0;

  const ratingDistribution = [5, 4, 3, 2, 1].map(stars => {
    const count = reviews.filter(r => r.rating === stars).length;
    const percentage = totalReviews > 0 ? (count / totalReviews) * 100 : 0;
    return { stars, count, percentage };
  });

  const fiveStarCount = reviews.filter(r => r.rating === 5).length;
  const fourStarCount = reviews.filter(r => r.rating === 4).length;
  const threeStarCount = reviews.filter(r => r.rating === 3).length;
  const twoStarCount = reviews.filter(r => r.rating === 2).length;
  const oneStarCount = reviews.filter(r => r.rating === 1).length;

  const reviewsWithResponse = reviews.filter(r => r.has_host_response).length;
  const responseRate = totalReviews > 0 ? (reviewsWithResponse / totalReviews) * 100 : 0;
  const pendingReplies = reviews.filter(r => !r.has_host_response && r.rating != null).length;

  // Filter reviews based on active tab
  let filteredReviews = reviews;
  
  if (activeTab === "pending") {
    filteredReviews = reviews.filter(r => !r.has_host_response && r.rating != null);
  } else if (activeTab === "responded") {
    filteredReviews = reviews.filter(r => r.has_host_response);
  }

  // Apply rating filter
  if (selectedRating) {
    filteredReviews = filteredReviews.filter(r => r.rating === selectedRating);
  }

  // Apply search filter
  if (searchQuery) {
    const query = searchQuery.toLowerCase();
    filteredReviews = filteredReviews.filter(r => 
      r.customer_name?.toLowerCase().includes(query) ||
      r.review_text?.toLowerCase().includes(query) ||
      r.vehicle_info?.toLowerCase().includes(query)
    );
  }

  // Apply sorting
  filteredReviews = [...filteredReviews].sort((a, b) => {
    if (sortBy === "highest") {
      return (b.rating || 0) - (a.rating || 0);
    } else if (sortBy === "lowest") {
      return (a.rating || 0) - (b.rating || 0);
    } else {
      const dateA = a.date ? new Date(a.date).getTime() : 0;
      const dateB = b.date ? new Date(b.date).getTime() : 0;
      return dateB - dateA;
    }
  });

  const loadMoreReviews = async () => {
    try {
      const newOffset = offset + limit;
      const response = await reviewsService.getReviews({
        min_rating: selectedRating || undefined,
        limit,
        offset: newOffset,
      });
      setReviews(prev => [...prev, ...response.reviews]);
      setOffset(newOffset);
    } catch (err) {
      console.error("Error loading more reviews:", err);
      setError("Failed to load more reviews. Please try again.");
    }
  };

  const cleanDateString = (dateString: string | null | undefined, customerName: string | null | undefined): string | null => {
    if (!dateString) return null;
    
    // Convert to string if it's not already
    let cleaned = String(dateString).trim();
    
    // Strategy 1: ALWAYS find month name first and extract from there (most reliable)
    // This works regardless of what comes before the date
    const monthPattern = /(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)/i;
    const dateMatch = cleaned.match(monthPattern);
    
    if (dateMatch && dateMatch.index !== undefined) {
      // Extract from the month name onwards - this removes everything before it
      cleaned = cleaned.substring(dateMatch.index).trim();
      // Remove any leading separators (bullet, dash, spaces, etc.)
      cleaned = cleaned.replace(/^[•\-\s]+/, '').trim();
      // Return early if we successfully found and extracted the date
      return cleaned || null;
    }
    
    // Strategy 2: If no month found, try to remove customer name (fallback)
    if (!customerName) return cleaned;
    
    const nameToRemove = customerName.trim();
    const nameEscaped = nameToRemove.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const nameLower = nameToRemove.toLowerCase();
    const cleanedLower = cleaned.toLowerCase();
    
    // Check if name appears at the start and remove it
    if (cleanedLower.startsWith(nameLower)) {
      cleaned = cleaned.substring(nameToRemove.length).trim();
      cleaned = cleaned.replace(/^[•\-\s]+/, '').trim();
    } else {
      // Try regex patterns to remove name
      // Pattern 1: "Name • Date" or "Name•Date"
      cleaned = cleaned.replace(new RegExp(`^${nameEscaped}\\s*[•\\-]\\s*`, 'i'), '');
      
      // Pattern 2: "Name Date" (space-separated)
      if (cleaned === String(dateString).trim()) {
        cleaned = cleaned.replace(new RegExp(`^${nameEscaped}\\s+`, 'i'), '');
      }
    }
    
    // Final cleanup - ensure no name remnants at start
    if (cleaned.toLowerCase().startsWith(nameLower)) {
      cleaned = cleaned.substring(nameToRemove.length).trim();
      cleaned = cleaned.replace(/^[•\-\s]+/, '').trim();
    }
    
    return cleaned || null;
  };

  const formatReviewDate = (dateString?: string, customerName?: string) => {
    if (!dateString) return "Date unknown";
    const cleanedDate = cleanDateString(dateString, customerName);
    if (!cleanedDate) return "Date unknown";
    try {
      const date = new Date(cleanedDate);
      return formatDistanceToNow(date, { addSuffix: true });
    } catch {
      return cleanedDate;
    }
  };

  const formatFullDate = (dateString?: string, customerName?: string) => {
    if (!dateString) return "";
    
    const dateStr = String(dateString).trim();
    
    // Check if it's already a valid ISO date string (doesn't need cleaning)
    const isoDatePattern = /^\d{4}-\d{2}-\d{2}/;
    if (isoDatePattern.test(dateStr)) {
      // It's already a clean ISO date, just format it
      try {
        const date = new Date(dateStr);
        return format(date, "MMM d, yyyy");
      } catch {
        return "";
      }
    }
    
    // Always clean the date string to remove customer name (defensive)
    // This handles cases where the date string might contain the name
    const cleanedDate = cleanDateString(dateStr, customerName);
    if (!cleanedDate) return "";
    
    try {
      const date = new Date(cleanedDate);
      // Check if date is valid
      if (isNaN(date.getTime())) {
        // If date parsing failed, return cleaned string (might be just text like "July 24, 2025")
        return cleanedDate;
      }
      return format(date, "MMM d, yyyy");
    } catch {
      // If parsing fails, return the cleaned string (should be just the date part)
      return cleanedDate;
    }
  };

  const handleReplyClick = () => {
    window.open('https://turo.com', '_blank');
  };

  const cleanHostResponse = (response: string | null | undefined): string | null => {
    if (!response) return null;
    // Remove 'Your response' or 'Your Response' from the beginning (case-insensitive)
    const cleaned = response.replace(/^Your\s+response\s*/i, '').trim();
    return cleaned || null;
  };

  const getRatingColor = (rating: number) => {
    if (rating >= 4.5) return "text-emerald-500";
    if (rating >= 3.5) return "text-yellow-500";
    if (rating >= 2.5) return "text-orange-500";
    return "text-red-500";
  };

  const getRatingBgColor = (rating: number) => {
    if (rating >= 4.5) return "bg-emerald-500/10 border-emerald-500/20";
    if (rating >= 3.5) return "bg-yellow-500/10 border-yellow-500/20";
    if (rating >= 2.5) return "bg-orange-500/10 border-orange-500/20";
    return "bg-red-500/10 border-red-500/20";
  };

  if (isLoading && reviews.length === 0) {
    return (
      <div className="min-h-screen bg-background p-6 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-muted-foreground">Loading reviews...</p>
        </div>
      </div>
    );
  }

  if (error && reviews.length === 0) {
    return (
      <div className="min-h-screen bg-background p-6 flex items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="p-6">
            <p className="text-destructive mb-4">{error}</p>
            <Button onClick={() => window.location.reload()}>Retry</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20 p-4 md:p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        {/* Header Section */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-4xl font-bold text-foreground mb-2">Reviews</h1>
            <p className="text-muted-foreground">Manage and respond to guest feedback</p>
          </div>
          {selectedRating && (
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => setSelectedRating(null)}
              className="gap-2"
            >
              <X className="h-4 w-4" />
              Clear filter
            </Button>
          )}
        </div>

        {/* Stats Overview Cards */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {/* Average Rating Card */}
          <Card className="relative overflow-hidden border-2">
            <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-primary/10" />
            <CardContent className="p-6 relative">
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 rounded-xl bg-primary/10">
                  <Star className="h-6 w-6 text-primary fill-primary" />
                </div>
                <Badge variant="secondary" className="text-xs">
                  {totalReviews} total
                </Badge>
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium text-muted-foreground">Average Rating</p>
                <div className="flex items-baseline gap-2">
                  <span className={cn("text-4xl font-bold", getRatingColor(averageRating))}>
                    {averageRating > 0 ? averageRating.toFixed(1) : "0.0"}
                  </span>
                  <div className="flex items-center gap-0.5">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <Star 
                        key={i} 
                        className={cn(
                          "h-4 w-4",
                          i < Math.round(averageRating) ? "fill-primary text-primary" : "text-muted-foreground/30"
                        )} 
                      />
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 5-Star Reviews Card */}
          <Card className="relative overflow-hidden border-2 border-emerald-500/20">
            <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-emerald-500/10" />
            <CardContent className="p-6 relative">
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 rounded-xl bg-emerald-500/10">
                  <Sparkles className="h-6 w-6 text-emerald-500" />
                </div>
                <Badge className="bg-emerald-500/20 text-emerald-700 border-emerald-500/30">
                  {totalReviews > 0 ? ((fiveStarCount / totalReviews) * 100).toFixed(0) : 0}%
                </Badge>
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium text-muted-foreground">5-Star Reviews</p>
                <p className="text-4xl font-bold text-emerald-600">{fiveStarCount}</p>
              </div>
            </CardContent>
          </Card>

          {/* Response Rate Card */}
          <Card className="relative overflow-hidden border-2 border-blue-500/20">
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-blue-500/10" />
            <CardContent className="p-6 relative">
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 rounded-xl bg-blue-500/10">
                  <MessageSquare className="h-6 w-6 text-blue-500" />
                </div>
                <Badge className="bg-blue-500/20 text-blue-700 border-blue-500/30">
                  {responseRate.toFixed(0)}%
                </Badge>
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium text-muted-foreground">Response Rate</p>
                <p className="text-4xl font-bold text-blue-600">{responseRate.toFixed(0)}%</p>
              </div>
            </CardContent>
          </Card>

          {/* Pending Replies Card */}
          <Card className={cn(
            "relative overflow-hidden border-2",
            pendingReplies > 0 ? "border-amber-500/20" : "border-muted"
          )}>
            <div className={cn(
              "absolute inset-0",
              pendingReplies > 0 ? "bg-gradient-to-br from-amber-500/5 to-amber-500/10" : "bg-muted/5"
            )} />
            <CardContent className="p-6 relative">
              <div className="flex items-center justify-between mb-4">
                <div className={cn(
                  "p-3 rounded-xl",
                  pendingReplies > 0 ? "bg-amber-500/10" : "bg-muted/10"
                )}>
                  <Clock className={cn(
                    "h-6 w-6",
                    pendingReplies > 0 ? "text-amber-500" : "text-muted-foreground"
                  )} />
                </div>
                {pendingReplies > 0 && (
                  <Badge className="bg-amber-500/20 text-amber-700 border-amber-500/30">
                    Action needed
                  </Badge>
                )}
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium text-muted-foreground">Pending Replies</p>
                <p className={cn(
                  "text-4xl font-bold",
                  pendingReplies > 0 ? "text-amber-600" : "text-muted-foreground"
                )}>
                  {pendingReplies}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content Area */}
        <div className="grid gap-4 lg:grid-cols-12">
          {/* Sidebar - Rating Breakdown */}
          <div className="lg:col-span-3 space-y-3">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Filter className="h-5 w-5" />
                  Rating Breakdown
                </CardTitle>
                <CardDescription>Filter by rating</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {ratingDistribution.map((item) => (
                    <button
                      key={item.stars}
                      onClick={() => setSelectedRating(selectedRating === item.stars ? null : item.stars)}
                      className={cn(
                        "flex items-center gap-2 w-full p-2 rounded-lg transition-all text-left",
                        "hover:bg-muted/50",
                        selectedRating === item.stars 
                          ? "bg-primary/10 ring-2 ring-primary/20" 
                          : "bg-muted/30",
                        item.count === 0 && "opacity-50 cursor-not-allowed"
                      )}
                      disabled={item.count === 0}
                    >
                      <div className="flex items-center gap-1 min-w-[2.5rem]">
                        <span className="text-xs font-semibold">{item.stars}</span>
                        <Star className="h-3.5 w-3.5 fill-yellow-400 text-yellow-400" />
                      </div>
                      <Progress 
                        value={item.percentage} 
                        className="flex-1 h-2"
                      />
                      <span className="text-xs font-medium text-muted-foreground min-w-[1.75rem] text-right">
                        {item.count}
                      </span>
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Quick Stats */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Quick Stats</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">5 Stars</span>
                  <span className="text-xs font-semibold text-emerald-600">{fiveStarCount}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">4 Stars</span>
                  <span className="text-xs font-semibold text-blue-600">{fourStarCount}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">3 Stars</span>
                  <span className="text-xs font-semibold text-yellow-600">{threeStarCount}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">2 Stars</span>
                  <span className="text-xs font-semibold text-orange-600">{twoStarCount}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">1 Star</span>
                  <span className="text-xs font-semibold text-red-600">{oneStarCount}</span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Main Reviews List */}
          <div className="lg:col-span-9">
            <Card>
              <CardHeader>
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div>
                    <CardTitle className="text-2xl mb-2">
                      {selectedRating 
                        ? `${selectedRating}-Star Reviews` 
                        : activeTab === "pending" 
                          ? "Pending Replies"
                          : activeTab === "responded"
                            ? "Responded Reviews"
                            : "All Reviews"}
                    </CardTitle>
                    <CardDescription>
                      {filteredReviews.length} {filteredReviews.length === 1 ? 'review' : 'reviews'}
                    </CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input 
                        placeholder="Search reviews..." 
                        className="pl-9 w-[200px]"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                      />
                    </div>
                    <Select value={sortBy} onValueChange={setSortBy}>
                      <SelectTrigger className="w-[140px]">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="recent">Most Recent</SelectItem>
                        <SelectItem value="highest">Highest Rated</SelectItem>
                        <SelectItem value="lowest">Lowest Rated</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {/* Tabs */}
                <Tabs value={activeTab} onValueChange={setActiveTab} className="mt-4">
                  <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="all">All</TabsTrigger>
                    <TabsTrigger value="pending" className="relative">
                      Pending
                      {pendingReplies > 0 && (
                        <Badge className="ml-2 h-5 w-5 p-0 flex items-center justify-center text-xs">
                          {pendingReplies}
                        </Badge>
                      )}
                    </TabsTrigger>
                    <TabsTrigger value="responded">Responded</TabsTrigger>
                  </TabsList>
                </Tabs>
              </CardHeader>

              <CardContent>
                {isLoading && reviews.length > 0 ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-6 w-6 animate-spin text-primary" />
                  </div>
                ) : (
                  <div className="space-y-3">
                    {filteredReviews.length === 0 ? (
                      <div className="text-center py-16 text-muted-foreground">
                        <Star className="h-16 w-16 mx-auto mb-4 opacity-30" />
                        <p className="text-lg font-medium mb-2">
                          {selectedRating 
                            ? `No ${selectedRating}-star reviews found`
                            : searchQuery 
                              ? "No reviews match your search"
                              : activeTab === "pending"
                                ? "No pending replies"
                                : "No reviews yet"}
                        </p>
                        <p className="text-sm">
                          {searchQuery && "Try adjusting your search terms"}
                        </p>
                      </div>
                    ) : (
                      filteredReviews.map((review) => {
                        const initials = review.customer_name
                          ? review.customer_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
                          : '??';
                        const rating = review.rating || 0;
                        const hasResponse = review.has_host_response;
                        
                        return (
                          <Card 
                            key={review.id} 
                            className={cn(
                              "transition-all hover:shadow-md",
                              !hasResponse && rating > 0 && "border-amber-500/30 bg-amber-50/50 dark:bg-amber-950/10"
                            )}
                          >
                            <CardContent className="p-4">
                              <div className="flex items-start gap-3">
                                <Avatar className="h-10 w-10 border-2 border-border shrink-0">
                                  <AvatarFallback className="bg-gradient-to-br from-primary/20 to-primary/10 text-primary font-semibold text-sm">
                                    {initials}
                                  </AvatarFallback>
                                </Avatar>
                                
                                <div className="flex-1 min-w-0 space-y-2">
                                  {/* Header Row */}
                                  <div className="flex items-start justify-between gap-3">
                                    <div className="flex-1 min-w-0">
                                      <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                                        <h3 className="font-semibold text-base text-foreground">
                                          {review.customer_name || "Anonymous Guest"}
                                        </h3>
                                        {review.vehicle_info && (
                                          <Badge variant="outline" className="gap-1.5 text-xs">
                                            <Car className="h-3 w-3" />
                                            {review.vehicle_info}
                                          </Badge>
                                        )}
                                        {hasResponse && (
                                          <Badge className="bg-emerald-500/20 text-emerald-700 border-emerald-500/30 gap-1.5 text-xs">
                                            <CheckCircle2 className="h-3 w-3" />
                                            Responded
                                          </Badge>
                                        )}
                                        {!hasResponse && rating > 0 && (
                                          <Badge className="bg-amber-500/20 text-amber-700 border-amber-500/30 gap-1.5 text-xs">
                                            <Clock className="h-3 w-3" />
                                            Pending
                                          </Badge>
                                        )}
                                      </div>
                                      
                                      <div className="flex items-center gap-2.5 flex-wrap">
                                        {rating > 0 && (
                                          <div className={cn(
                                            "flex items-center gap-1 px-2 py-0.5 rounded-md border text-xs",
                                            getRatingBgColor(rating)
                                          )}>
                                            <div className="flex items-center gap-0.5">
                                              {Array.from({ length: 5 }).map((_, i) => (
                                                <Star 
                                                  key={i} 
                                                  className={cn(
                                                    "h-3 w-3",
                                                    i < rating 
                                                      ? "fill-yellow-400 text-yellow-400" 
                                                      : "text-muted-foreground/30"
                                                  )} 
                                                />
                                              ))}
                                            </div>
                                            <span className={cn("text-xs font-semibold ml-0.5", getRatingColor(rating))}>
                                              {rating}.0
                                            </span>
                                          </div>
                                        )}
                                        {review.date && (
                                          <Badge variant="outline" className="text-xs">
                                            {formatFullDate(review.date, review.customer_name)}
                                          </Badge>
                                        )}
                                      </div>
                                    </div>
                                  </div>

                                  {/* Review Text */}
                                  {review.review_text && (
                                    <div className="pt-1">
                                      <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">
                                        {review.review_text}
                                      </p>
                                    </div>
                                  )}
                                  
                                  {/* Areas of Improvement */}
                                  {review.areas_of_improvement && review.areas_of_improvement.length > 0 && (
                                    <div className="flex flex-wrap gap-1.5">
                                      {review.areas_of_improvement.map((area, idx) => (
                                        <Badge 
                                          key={idx} 
                                          variant="outline" 
                                          className="text-xs bg-muted/50 py-0.5"
                                        >
                                          <AlertCircle className="h-2.5 w-2.5 mr-1" />
                                          {area}
                                        </Badge>
                                      ))}
                                    </div>
                                  )}
                                  
                                  {/* Host Response */}
                                  {review.host_response && (() => {
                                    const cleanedResponse = cleanHostResponse(review.host_response);
                                    return cleanedResponse ? (
                                      <div className="pt-1 p-3 rounded-lg bg-primary/5 border-l-2 border-primary">
                                        <div className="flex items-center gap-1.5 mb-1">
                                          <MessageSquare className="h-3.5 w-3.5 text-primary" />
                                          <p className="text-xs font-semibold text-primary">Your Response</p>
                                        </div>
                                        <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">
                                          {cleanedResponse}
                                        </p>
                                      </div>
                                    ) : null;
                                  })()}
                                  
                                  {/* Reply Button */}
                                  {!hasResponse && rating > 0 && (
                                    <div className="pt-1">
                                      <Button 
                                        variant="outline" 
                                        size="sm" 
                                        className="gap-1.5 h-8 text-xs hover:bg-primary hover:text-primary-foreground transition-colors"
                                        onClick={handleReplyClick}
                                      >
                                        <MessageSquare className="h-3.5 w-3.5" />
                                        Reply on Turo
                                        <ExternalLink className="h-3 w-3" />
                                      </Button>
                                    </div>
                                  )}
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        );
                      })
                    )}
                  </div>
                )}
                
                {filteredReviews.length > 0 && offset + limit < totalReviews && (
                  <div className="mt-6">
                    <Button 
                      variant="outline" 
                      className="w-full"
                      onClick={loadMoreReviews}
                      disabled={isLoading}
                    >
                      {isLoading ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Loading...
                        </>
                      ) : (
                        <>
                          Load More Reviews
                          <span className="ml-2 text-xs text-muted-foreground">
                            ({totalReviews - (offset + filteredReviews.length)} remaining)
                          </span>
                        </>
                      )}
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Reviews;
