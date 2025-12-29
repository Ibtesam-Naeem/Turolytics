import { DistanceUnit, Currency, TimeFormat } from "@/contexts/RegionalSettingsContext";

// Conversion constants
const KM_TO_MILES = 0.621371;
const MILES_TO_KM = 1.60934;

// Currency exchange rates (approximate - in production, fetch from API)
const USD_TO_CAD = 1.35;
const CAD_TO_USD = 0.74;

/**
 * Convert kilometers to miles
 */
export const kmToMiles = (km: number): number => {
  return km * KM_TO_MILES;
};

/**
 * Convert miles to kilometers
 */
export const milesToKm = (miles: number): number => {
  return miles * MILES_TO_KM;
};

/**
 * Convert distance based on unit preference
 * @param value - Distance value (assumed to be in km)
 * @param targetUnit - Target unit to convert to
 * @returns Converted distance value
 */
export const convertDistance = (value: number, targetUnit: DistanceUnit): number => {
  if (targetUnit === "miles") {
    return kmToMiles(value);
  }
  return value; // Already in km
};

/**
 * Format distance with unit label
 */
export const formatDistance = (value: number, unit: DistanceUnit): string => {
  const converted = convertDistance(value, unit);
  const rounded = Math.round(converted * 10) / 10; // Round to 1 decimal place
  return `${rounded.toLocaleString()} ${unit === "miles" ? "mi" : "km"}`;
};

/**
 * Convert currency based on preference
 * @param value - Currency value (assumed to be in USD)
 * @param targetCurrency - Target currency to convert to
 * @returns Converted currency value
 */
export const convertCurrency = (value: number, targetCurrency: Currency): number => {
  if (targetCurrency === "cad") {
    return value * USD_TO_CAD;
  }
  return value; // Already in USD
};

/**
 * Format currency with symbol
 */
export const formatCurrency = (value: number, currency: Currency): string => {
  const converted = convertCurrency(value, currency);
  const currencyCode = currency === "cad" ? "CAD" : "USD";
  const locale = currency === "cad" ? "en-CA" : "en-US";
  
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency: currencyCode,
    maximumFractionDigits: 0,
  }).format(converted);
};

/**
 * Format currency with symbol (for smaller amounts with decimals)
 */
export const formatCurrencyDecimal = (value: number, currency: Currency): string => {
  const converted = convertCurrency(value, currency);
  const currencyCode = currency === "cad" ? "CAD" : "USD";
  const locale = currency === "cad" ? "en-CA" : "en-US";
  
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency: currencyCode,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(converted);
};

/**
 * Format time based on format preference
 * @param date - Date object or time string
 * @param format - Time format (12h or 24h)
 * @returns Formatted time string
 */
export const formatTime = (date: Date | string, format: TimeFormat): string => {
  const dateObj = typeof date === "string" ? new Date(date) : date;
  
  if (format === "24h") {
    const hours = dateObj.getHours().toString().padStart(2, "0");
    const minutes = dateObj.getMinutes().toString().padStart(2, "0");
    return `${hours}:${minutes}`;
  } else {
    // 12-hour format
    let hours = dateObj.getHours();
    const minutes = dateObj.getMinutes();
    const period = hours >= 12 ? "p.m." : "a.m.";
    
    if (hours === 0) {
      hours = 12;
    } else if (hours > 12) {
      hours = hours - 12;
    }
    
    const minutesStr = minutes > 0 ? `:${minutes.toString().padStart(2, "0")}` : "";
    return `${hours}${minutesStr} ${period}`;
  }
};

/**
 * Format time string (e.g., "4:30 p.m.") to desired format
 */
export const formatTimeString = (timeStr: string, format: TimeFormat): string => {
  // Try to parse common time formats
  const timeMatch = timeStr.match(/(\d+):?(\d+)?\s*(a\.m\.|p\.m\.|AM|PM)/i);
  
  if (timeMatch) {
    let hours = parseInt(timeMatch[1]);
    const minutes = timeMatch[2] ? parseInt(timeMatch[2]) : 0;
    const period = timeMatch[3].toLowerCase();
    
    if (period.includes("p.m.") || period.includes("pm")) {
      if (hours !== 12) hours += 12;
    } else {
      if (hours === 12) hours = 0;
    }
    
    const date = new Date();
    date.setHours(hours, minutes, 0, 0);
    return formatTime(date, format);
  }
  
  // If parsing fails, try to parse as 24-hour format
  const time24Match = timeStr.match(/(\d+):(\d+)/);
  if (time24Match) {
    const hours = parseInt(time24Match[1]);
    const minutes = parseInt(time24Match[2]);
    const date = new Date();
    date.setHours(hours, minutes, 0, 0);
    return formatTime(date, format);
  }
  
  // Return original if can't parse
  return timeStr;
};

