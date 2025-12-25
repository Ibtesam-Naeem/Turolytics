import { useState, useEffect } from "react";
import { Star, MessageSquare, TrendingUp, Search, Car, Calendar, ExternalLink, Filter, X, Loader2 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { reviewsService, Review } from "@/services/reviews-service";
import { formatDistanceToNow } from "date-fns";

const Reviews = () => {
  const [selectedRating, setSelectedRating] = useState<number | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalReviews, setTotalReviews] = useState(0);
  const [sortBy, setSortBy] = useState<string>("recent");
  const [searchQuery, setSearchQuery] = useState("");
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
          offset: 0, // Reset to 0 when filters change
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

  // Calculate statistics from reviews
  const validRatings = reviews.filter(r => r.rating != null && r.rating > 0 && r.rating <= 5);
  const averageRating = validRatings.length > 0
    ? validRatings.reduce((sum, r) => sum + (r.rating || 0), 0) / validRatings.length
    : 0;

  // Calculate rating distribution
  const ratingDistribution = [5, 4, 3, 2, 1].map(stars => {
    const count = reviews.filter(r => r.rating === stars).length;
    const percentage = totalReviews > 0 ? (count / totalReviews) * 100 : 0;
    return { stars, count, percentage };
  });

  const fiveStarCount = reviews.filter(r => r.rating === 5).length;
  const fiveStarPercentage = totalReviews > 0 ? (fiveStarCount / totalReviews) * 100 : 0;

  // Calculate response rate
  const reviewsWithResponse = reviews.filter(r => r.has_host_response).length;
  const responseRate = totalReviews > 0 ? (reviewsWithResponse / totalReviews) * 100 : 0;
  const pendingReplies = reviews.filter(r => !r.has_host_response && r.rating != null).length;

  // Filter and sort reviews
  let filteredReviews = selectedRating 
    ? reviews.filter(r => r.rating === selectedRating)
    : reviews;

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
      // Most recent
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

  const formatReviewDate = (dateString?: string) => {
    if (!dateString) return "Date unknown";
    try {
      const date = new Date(dateString);
      return formatDistanceToNow(date, { addSuffix: true });
    } catch {
      return dateString;
    }
  };

  const handleReplyClick = () => {
    // Placeholder for Turo routing - will be implemented later
    window.open('https://turo.com', '_blank');
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
    <div className="min-h-screen bg-background p-6">
      <div className="mx-auto max-w-[2000px] space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Reviews</h1>
            <p className="text-sm text-muted-foreground">Guest feedback and ratings</p>
          </div>
          {selectedRating && (
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => setSelectedRating(null)}
              className="gap-2"
            >
              <X className="h-4 w-4" />
              Clear {selectedRating}-star filter
            </Button>
          )}
        </div>

        {/* Rating Overview */}
        <div className="grid gap-4 sm:grid-cols-3">
          <Card className="bg-gradient-to-br from-rating/10 to-rating/5 border-rating/20">
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground font-medium">Average Rating</p>
                  <div className="flex items-center gap-2 mt-1">
                    <Star className="h-6 w-6 fill-rating text-rating" />
                    <span className="text-3xl font-bold text-foreground">
                      {averageRating > 0 ? averageRating.toFixed(1) : "0.0"}
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm text-muted-foreground">{totalReviews} reviews</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-success/10 to-success/5 border-success/20">
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground font-medium">5-Star Reviews</p>
                  <p className="text-3xl font-bold mt-1 text-success">{fiveStarCount}</p>
                </div>
                <div className="p-3 rounded-full bg-success/20">
                  <Star className="h-5 w-5 fill-success text-success" />
                </div>
              </div>
              <p className="text-sm text-muted-foreground mt-3">
                {fiveStarPercentage > 0 ? `${fiveStarPercentage.toFixed(0)}%` : "0%"} of all reviews
              </p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-chart-4/10 to-chart-4/5 border-chart-4/20">
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground font-medium">Response Rate</p>
                  <p className="text-3xl font-bold mt-1" style={{ color: 'hsl(var(--chart-4))' }}>
                    {responseRate.toFixed(0)}%
                  </p>
                </div>
                <div className="p-3 rounded-full" style={{ backgroundColor: 'hsla(var(--chart-4), 0.2)' }}>
                  <MessageSquare className="h-5 w-5" style={{ color: 'hsl(var(--chart-4))' }} />
                </div>
              </div>
              <p className="text-sm text-muted-foreground mt-3">
                {pendingReplies} {pendingReplies === 1 ? 'pending reply' : 'pending replies'}
              </p>
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-6 lg:grid-cols-4">
          {/* Review Breakdown */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <Filter className="h-4 w-4" />
                Review Breakdown
              </CardTitle>
              <CardDescription className="text-xs">Click to filter by rating</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {ratingDistribution.map((item) => (
                  <button
                    key={item.stars}
                    onClick={() => setSelectedRating(selectedRating === item.stars ? null : item.stars)}
                    className={`flex items-center gap-2 w-full p-2 rounded-lg transition-all hover:bg-muted/50 ${
                      selectedRating === item.stars ? 'bg-primary/10 ring-1 ring-primary' : ''
                    } ${item.count === 0 ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                    disabled={item.count === 0}
                  >
                    <div className="flex items-center gap-0.5 w-8">
                      <span className="text-xs font-medium">{item.stars}</span>
                      <Star className="h-3 w-3 fill-rating text-rating" />
                    </div>
                    <Progress value={item.percentage} className="flex-1 h-2" />
                    <span className="text-xs text-muted-foreground w-8 text-right">{item.count}</span>
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Recent Reviews */}
          <Card className="lg:col-span-3">
            <CardHeader className="flex flex-row items-center justify-between flex-wrap gap-4">
              <div>
                <CardTitle className="flex items-center gap-2">
                  {selectedRating ? (
                    <>
                      {selectedRating}-Star Reviews
                      <Badge variant="secondary">{filteredReviews.length}</Badge>
                    </>
                  ) : (
                    'Recent Reviews'
                  )}
                </CardTitle>
                <CardDescription>
                  {selectedRating 
                    ? `Showing all ${selectedRating}-star reviews` 
                    : 'Latest guest feedback'}
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
                  <SelectTrigger className="w-[130px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="recent">Most Recent</SelectItem>
                    <SelectItem value="highest">Highest Rated</SelectItem>
                    <SelectItem value="lowest">Lowest Rated</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardHeader>
            <CardContent>
              {isLoading && reviews.length > 0 ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-primary" />
                </div>
              ) : (
                <div className="space-y-6">
                  {filteredReviews.length === 0 ? (
                    <div className="text-center py-12 text-muted-foreground">
                      <Star className="h-12 w-12 mx-auto mb-3 opacity-50" />
                      <p>
                        {selectedRating 
                          ? `No ${selectedRating}-star reviews found`
                          : searchQuery 
                            ? "No reviews match your search"
                            : "No reviews yet"}
                      </p>
                    </div>
                  ) : (
                    filteredReviews.map((review) => {
                      const initials = review.customer_name
                        ? review.customer_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
                        : '??';
                      const rating = review.rating || 0;
                      
                      return (
                        <div key={review.id} className="border-b border-border pb-6 last:border-0 last:pb-0">
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex items-start gap-3 flex-1">
                              <Avatar className="h-10 w-10">
                                <AvatarFallback className="bg-primary/10 text-primary">
                                  {initials}
                                </AvatarFallback>
                              </Avatar>
                              <div className="flex-1">
                                <div className="flex items-center flex-wrap gap-2">
                                  <p className="font-medium text-foreground">
                                    {review.customer_name || "Anonymous"}
                                  </p>
                                  {review.vehicle_info && (
                                    <Badge variant="secondary" className="gap-1">
                                      <Car className="h-3 w-3" />
                                      {review.vehicle_info}
                                    </Badge>
                                  )}
                                </div>
                                <div className="flex items-center gap-2 mt-1">
                                  {rating > 0 && (
                                    <div className="flex items-center gap-0.5">
                                      {Array.from({ length: 5 }).map((_, i) => (
                                        <Star 
                                          key={i} 
                                          className={`h-4 w-4 ${i < rating ? 'fill-rating text-rating' : 'text-muted'}`} 
                                        />
                                      ))}
                                    </div>
                                  )}
                                  {review.date && (
                                    <span className="text-sm text-muted-foreground">
                                      {formatReviewDate(review.date)}
                                    </span>
                                  )}
                                </div>
                                {review.review_text && (
                                  <p className="text-sm text-foreground mt-3">{review.review_text}</p>
                                )}
                                
                                {review.areas_of_improvement && review.areas_of_improvement.length > 0 && (
                                  <div className="mt-2 flex flex-wrap gap-1">
                                    {review.areas_of_improvement.map((area, idx) => (
                                      <Badge key={idx} variant="outline" className="text-xs">
                                        {area}
                                      </Badge>
                                    ))}
                                  </div>
                                )}
                                
                                {review.host_response && (
                                  <div className="mt-3 p-3 rounded-lg bg-muted/50 border-l-2 border-primary">
                                    <p className="text-xs font-medium text-primary mb-1">Your response:</p>
                                    <p className="text-sm text-muted-foreground">{review.host_response}</p>
                                  </div>
                                )}
                                
                                {!review.has_host_response && rating > 0 && (
                                  <div className="mt-3">
                                    <Button 
                                      variant="outline" 
                                      size="sm" 
                                      className="h-8 gap-2 hover:bg-primary hover:text-primary-foreground transition-colors"
                                      onClick={handleReplyClick}
                                    >
                                      <MessageSquare className="h-4 w-4" />
                                      Reply on Turo
                                      <ExternalLink className="h-3 w-3" />
                                    </Button>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              )}
              
              {filteredReviews.length > 0 && offset + limit < totalReviews && (
                <Button 
                  variant="outline" 
                  className="w-full mt-6"
                  onClick={loadMoreReviews}
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Loading...
                    </>
                  ) : (
                    `Load More Reviews (${totalReviews - (offset + filteredReviews.length)} remaining)`
                  )}
                </Button>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Reviews;
