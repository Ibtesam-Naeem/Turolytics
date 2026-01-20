// Stub auth service for demo mode
// Real authentication not available in demo

export interface User {
  id: string;
  email: string;
  firstName?: string;
  lastName?: string;
}

export interface UserSession {
  id: number;
  device_info?: string;
  ip_address?: string;
  created_at?: string;
  browser?: string;
  os?: string;
  location?: string;
}

class AuthService {
  getToken(): string | null {
    return localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
  }

  setToken(token: string, rememberMe: boolean): void {
    if (rememberMe) {
      localStorage.setItem('auth_token', token);
    } else {
      sessionStorage.setItem('auth_token', token);
    }
  }

  removeToken(): void {
    localStorage.removeItem('auth_token');
    sessionStorage.removeItem('auth_token');
  }

  async getCurrentUser(): Promise<User> {
    // Demo mode - return stub user
    return { id: "demo-user", email: "demo@example.com" };
  }

  async login(data: { email: string; password: string; rememberMe?: boolean }): Promise<{ access_token: string }> {
    // Demo mode - not used (loginDemo is used instead)
    throw new Error("Real login not available in demo mode");
  }

  async register(data: any): Promise<User> {
    // Demo mode - not used
    throw new Error("Real registration not available in demo mode");
  }

  async getSessions(): Promise<UserSession[]> {
    // Demo mode - return empty array
    return [];
  }

  async revokeSession(sessionId: number): Promise<void> {
    // Demo mode - stub
  }

  async updateProfile(data: any): Promise<User> {
    // Demo mode - stub
    return { id: "demo-user", email: "demo@example.com" };
  }

  async deleteAccount(data: { reason: string }): Promise<void> {
    // Demo mode - stub
  }

  getRememberedAccounts(): Array<{ email: string }> {
    const email = localStorage.getItem('remembered_email');
    return email ? [{ email }] : [];
  }

  setRememberedEmail(email: string): void {
    localStorage.setItem('remembered_email', email);
  }

  clearRememberedEmail(): void {
    localStorage.removeItem('remembered_email');
  }

  removeRememberedAccount(email: string): void {
    if (localStorage.getItem('remembered_email') === email) {
      localStorage.removeItem('remembered_email');
    }
  }
}

export const authService = new AuthService();
