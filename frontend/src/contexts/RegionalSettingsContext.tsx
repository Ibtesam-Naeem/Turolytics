import { createContext, useContext, useEffect, useState, ReactNode } from "react";

export type DistanceUnit = "km" | "miles";
export type Currency = "usd" | "cad";
export type TimeFormat = "12h" | "24h";

interface RegionalSettingsContextType {
  distanceUnit: DistanceUnit;
  currency: Currency;
  timeFormat: TimeFormat;
  setDistanceUnit: (unit: DistanceUnit) => void;
  setCurrency: (currency: Currency) => void;
  setTimeFormat: (format: TimeFormat) => void;
}

const RegionalSettingsContext = createContext<RegionalSettingsContextType | undefined>(undefined);

const REGIONAL_SETTINGS_STORAGE_KEY = "turolytics-regional-settings";

export const RegionalSettingsProvider = ({ children }: { children: ReactNode }) => {
  const [distanceUnit, setDistanceUnitState] = useState<DistanceUnit>(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem(REGIONAL_SETTINGS_STORAGE_KEY);
      if (stored) {
        try {
          const settings = JSON.parse(stored);
          if (settings.distanceUnit && ["km", "miles"].includes(settings.distanceUnit)) {
            return settings.distanceUnit;
          }
        } catch (e) {
          // Invalid JSON, use default
        }
      }
    }
    return "km";
  });

  const [currency, setCurrencyState] = useState<Currency>(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem(REGIONAL_SETTINGS_STORAGE_KEY);
      if (stored) {
        try {
          const settings = JSON.parse(stored);
          if (settings.currency && ["usd", "cad"].includes(settings.currency)) {
            return settings.currency;
          }
        } catch (e) {
          // Invalid JSON, use default
        }
      }
    }
    return "usd";
  });

  const [timeFormat, setTimeFormatState] = useState<TimeFormat>(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem(REGIONAL_SETTINGS_STORAGE_KEY);
      if (stored) {
        try {
          const settings = JSON.parse(stored);
          if (settings.timeFormat && ["12h", "24h"].includes(settings.timeFormat)) {
            return settings.timeFormat;
          }
        } catch (e) {
          // Invalid JSON, use default
        }
      }
    }
    return "12h";
  });

  // Save to localStorage whenever settings change
  useEffect(() => {
    if (typeof window !== "undefined") {
      const settings = {
        distanceUnit,
        currency,
        timeFormat,
      };
      localStorage.setItem(REGIONAL_SETTINGS_STORAGE_KEY, JSON.stringify(settings));
    }
  }, [distanceUnit, currency, timeFormat]);

  const setDistanceUnit = (unit: DistanceUnit) => {
    setDistanceUnitState(unit);
  };

  const setCurrency = (curr: Currency) => {
    setCurrencyState(curr);
  };

  const setTimeFormat = (format: TimeFormat) => {
    setTimeFormatState(format);
  };

  return (
    <RegionalSettingsContext.Provider
      value={{
        distanceUnit,
        currency,
        timeFormat,
        setDistanceUnit,
        setCurrency,
        setTimeFormat,
      }}
    >
      {children}
    </RegionalSettingsContext.Provider>
  );
};

export const useRegionalSettings = () => {
  const context = useContext(RegionalSettingsContext);
  if (context === undefined) {
    throw new Error("useRegionalSettings must be used within a RegionalSettingsProvider");
  }
  return context;
};

