import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { authService } from "@/services/auth-service";

type AuthMode = "demo" | "real";

interface User {
  id: string;
  email?: string;
  firstName?: string;
  lastName?: string;
  mode: AuthMode;
}

interface AuthContextType {
  user: User | null;
  mode: AuthMode | null;
  isAuthenticated: boolean;
  isDemo: boolean;
  login: (email: string, password: string, rememberMe?: boolean) => Promise<{ error?: string }>;
  signup: (userData: SignupData) => Promise<{ error?: string }>;
  loginDemo: () => Promise<{ error?: string }>;
  logout: () => void;
}

interface SignupData {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  phone: string;
  country: string;
  state: string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = user !== null;
  const mode = user?.mode ?? null;
  const isDemo = mode === "demo";

  // Check for existing token on mount and restore user session
  useEffect(() => {
    const checkAuth = async () => {
      const token = authService.getToken();
      if (token) {
        try {
          const userData = await authService.getCurrentUser();
          setUser({
            id: userData.id.toString(),
            email: userData.email,
            mode: "real",
          });
        } catch (error) {
          // Token is invalid or expired, clear it
          authService.removeToken();
          setUser(null);
          // Only redirect if we're not already on auth page
          if (typeof window !== 'undefined' && !window.location.pathname.includes('/auth')) {
            // Don't redirect immediately - let the app render first
            setTimeout(() => {
              window.location.href = '/auth';
            }, 100);
          }
        }
      }
      setIsLoading(false);
    };
    checkAuth();
  }, []);

  // Periodically validate token (every 5 minutes)
  useEffect(() => {
    if (!user || user.mode === 'demo') return;

    const interval = setInterval(async () => {
      const token = authService.getToken();
      if (token) {
        try {
          await authService.getCurrentUser();
          // Token is still valid
        } catch (error) {
          // Token expired, clear it and logout
          authService.removeToken();
          setUser(null);
          if (typeof window !== 'undefined' && !window.location.pathname.includes('/auth')) {
            window.location.href = '/auth';
          }
        }
      }
    }, 5 * 60 * 1000); // Check every 5 minutes

    return () => clearInterval(interval);
  }, [user]);

  const login = async (email: string, password: string, rememberMe: boolean = true): Promise<{ error?: string }> => {
    try {
      const response = await authService.login({ email, password });
      authService.setToken(response.access_token, rememberMe);
      
      // Save email if remember me is checked
      if (rememberMe) {
        authService.setRememberedEmail(email);
      } else {
        // Clear remembered email if not using remember me
        authService.clearRememberedEmail();
      }
      
      // Fetch user data
      const userData = await authService.getCurrentUser();
      setUser({
        id: userData.id.toString(),
        email: userData.email,
        mode: "real",
      });
      
      return {};
    } catch (error) {
      return { 
        error: error instanceof Error ? error.message : "Failed to login. Please try again." 
      };
    }
  };

  const signup = async (userData: SignupData): Promise<{ error?: string }> => {
    try {
      // Send all registration data to backend
      const newUser = await authService.register({
        email: userData.email,
        password: userData.password,
        firstName: userData.firstName,
        lastName: userData.lastName,
        phone: userData.phone,
        country: userData.country,
        state: userData.state,
      });
      
      // After successful registration, automatically log in
      // Signup always uses rememberMe = true
      const response = await authService.login({
        email: userData.email,
        password: userData.password,
      });
      
      authService.setToken(response.access_token, true);
      // Remember email for signup (always remember me)
      authService.setRememberedEmail(userData.email);
      
      setUser({
        id: newUser.id.toString(),
        email: newUser.email,
        mode: "real",
      });
      
      return {};
    } catch (error) {
      return { 
        error: error instanceof Error ? error.message : "Failed to create account. Please try again." 
      };
    }
  };

  const loginDemo = async (): Promise<{ error?: string }> => {
    // Temporary: Set demo user locally
    setUser({ id: "demo-user", mode: "demo" });
    return {};
  };

  const logout = () => {
    authService.removeToken();
    setUser(null);
  };

  // Don't render children until auth check is complete
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        mode,
        isAuthenticated,
        isDemo,
        login,
        signup,
        loginDemo,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
