import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format a date/time as a relative time string (e.g., "2 hours ago", "3 days ago")
 */
export function formatRelativeTime(date: string | Date | null | undefined): string {
  if (!date) return "Never";
  
  const now = new Date();
  const then = typeof date === 'string' ? new Date(date) : date;
  
  if (isNaN(then.getTime())) return "Invalid date";
  
  const diffMs = now.getTime() - then.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);
  const diffWeeks = Math.floor(diffDays / 7);
  const diffMonths = Math.floor(diffDays / 30);
  const diffYears = Math.floor(diffDays / 365);
  
  if (diffSeconds < 60) return "Just now";
  if (diffMinutes < 60) return `${diffMinutes} minute${diffMinutes !== 1 ? 's' : ''} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
  if (diffWeeks < 4) return `${diffWeeks} week${diffWeeks !== 1 ? 's' : ''} ago`;
  if (diffMonths < 12) return `${diffMonths} month${diffMonths !== 1 ? 's' : ''} ago`;
  return `${diffYears} year${diffYears !== 1 ? 's' : ''} ago`;
}

/**
 * Get connection health status based on last sync time
 */
export function getConnectionHealth(lastSync: string | Date | null | undefined): {
  status: 'excellent' | 'good' | 'warning' | 'error';
  label: string;
} {
  if (!lastSync) {
    return { status: 'error', label: 'Never synced' };
  }
  
  const now = new Date();
  const syncTime = typeof lastSync === 'string' ? new Date(lastSync) : lastSync;
  
  if (isNaN(syncTime.getTime())) {
    return { status: 'error', label: 'Invalid date' };
  }
  
  const diffMs = now.getTime() - syncTime.getTime();
  const diffHours = diffMs / (1000 * 60 * 60);
  
  if (diffHours < 1) return { status: 'excellent', label: 'Excellent' };
  if (diffHours < 24) return { status: 'good', label: 'Good' };
  if (diffHours < 72) return { status: 'warning', label: 'Stale' };
  return { status: 'error', label: 'Outdated' };
}
