import { apiClient } from '@/lib/api-client';

export interface User {
  id: number;
  user_id: number;
  email: string;
  email_verified: boolean;
  first_name?: string;
  last_name?: string;
  phone_number?: string;
  country?: string;
  state?: string;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  firstName?: string;
  lastName?: string;
  phone?: string;
  country?: string;
  state?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface DeleteAccountRequest {
  reason?: string;
}

class AuthService {
  async register(data: RegisterRequest): Promise<User> {
    // Map frontend field names to backend field names
    const requestData = {
      email: data.email,
      password: data.password,
      firstName: data.firstName,
      lastName: data.lastName,
      phone: data.phone,
      country: data.country,
      state: data.state,
    };
    return apiClient.post<User>('/api/auth/register', requestData);
  }

  async login(data: LoginRequest): Promise<AuthResponse> {
    return apiClient.post<AuthResponse>('/api/auth/login/json', data);
  }

  async getCurrentUser(): Promise<User> {
    return apiClient.get<User>('/api/auth/me');
  }

  async updateProfile(data: {
    firstName?: string;
    lastName?: string;
    phone?: string;
    country?: string;
    state?: string;
  }): Promise<User> {
    return apiClient.put<User>('/api/auth/profile', data);
  }

  setToken(token: string, rememberMe: boolean = true): void {
    if (rememberMe) {
      localStorage.setItem('auth_token', token);
      // Remove from sessionStorage if it exists
      sessionStorage.removeItem('auth_token');
    } else {
      sessionStorage.setItem('auth_token', token);
      // Remove from localStorage if it exists
      localStorage.removeItem('auth_token');
    }
  }

  getToken(): string | null {
    // Check localStorage first (remember me), then sessionStorage
    return localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
  }

  removeToken(): void {
    localStorage.removeItem('auth_token');
    sessionStorage.removeItem('auth_token');
  }

  setRememberedEmail(email: string): void {
    const accounts = this.getRememberedAccounts();
    // Check if email already exists
    const existingIndex = accounts.findIndex(acc => acc.email === email);
    
    if (existingIndex >= 0) {
      // Update existing account timestamp
      accounts[existingIndex].lastUsed = new Date().toISOString();
    } else {
      // Add new account
      accounts.push({
        email,
        lastUsed: new Date().toISOString(),
      });
    }
    
    // Sort by last used (most recent first) and keep only last 5
    accounts.sort((a, b) => new Date(b.lastUsed).getTime() - new Date(a.lastUsed).getTime());
    const recentAccounts = accounts.slice(0, 5);
    
    localStorage.setItem('remembered_accounts', JSON.stringify(recentAccounts));
  }

  getRememberedAccounts(): Array<{ email: string; lastUsed: string }> {
    const stored = localStorage.getItem('remembered_accounts');
    if (!stored) {
      // Check for old single email format and migrate
      const oldEmail = localStorage.getItem('remembered_email');
      if (oldEmail) {
        const accounts = [{ email: oldEmail, lastUsed: new Date().toISOString() }];
        localStorage.setItem('remembered_accounts', JSON.stringify(accounts));
        localStorage.removeItem('remembered_email');
        return accounts;
      }
      return [];
    }
    try {
      return JSON.parse(stored);
    } catch {
      return [];
    }
  }

  getRememberedEmail(): string | null {
    const accounts = this.getRememberedAccounts();
    return accounts.length > 0 ? accounts[0].email : null;
  }

  clearRememberedEmail(): void {
    localStorage.removeItem('remembered_accounts');
    localStorage.removeItem('remembered_email'); // Legacy cleanup
  }

  removeRememberedAccount(email: string): void {
    const accounts = this.getRememberedAccounts();
    const filtered = accounts.filter(acc => acc.email !== email);
    if (filtered.length > 0) {
      localStorage.setItem('remembered_accounts', JSON.stringify(filtered));
    } else {
      localStorage.removeItem('remembered_accounts');
    }
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  async deleteAccount(request: DeleteAccountRequest): Promise<void> {
    await apiClient.post('/api/auth/account/delete', request);
  }
}

export const authService = new AuthService();

