import { Injectable, computed, signal, effect } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap, catchError, throwError } from 'rxjs';

export interface UserResponse {
  user_id: string;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  coins: number;
  experience: number;
  level: number;
  avatar_url?: string;
  last_login_date?: string;
  current_streak: number;
  iat?: number;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserUpdateResponse {
  user: UserResponse;
  access_token: string;
  token_type: string;
}

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  // Use a signal for reactive state management
  private tokenSignal = signal<string | null>(localStorage.getItem('access_token'));

  // Computed signals
  isAuthenticated = computed(() => this.tokenSignal() !== null);
  token = computed(() => this.tokenSignal());
  currentUser = computed(() => {
    const token = this.tokenSignal();
    if (!token) return null;
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return { 
        user_id: payload.sub,
        username: payload.username,
        first_name: payload.first_name,
        last_name: payload.last_name,
        avatar_url: payload.avatar_url,
        iat: payload.iat
      };
    } catch {
      return null;
    }
  });

  // Backend is proxied or absolute. Since both run in docker compose on different ports locally:
  // If we access the frontend from localhost:4200, we should point to localhost:8000 for the backend API.
  private apiUrl = 'http://localhost:8000/api/v1/auth';

  // Trigger to manually force avatar URL recomputation
  private avatarUpdateTrigger = signal<number>(0);

  // Globally accessible computed avatar URL with cache-busting timestamp
  cachedAvatarUrl = computed(() => {
    this.avatarUpdateTrigger(); // register dependency
    const user = this.currentUser();
    if (user && user.avatar_url) {
      return `http://localhost:8000${user.avatar_url}?v=${Date.now()}`;
    }
    return null;
  });



  constructor(
    private http: HttpClient,
    private router: Router,
  ) {}

  login(username: string, password: string): Observable<TokenResponse> {
    const body = new URLSearchParams();
    body.set('username', username);
    body.set('password', password);

    const headers = new HttpHeaders({
      'Content-Type': 'application/x-www-form-urlencoded',
    });

    return this.http
      .post<TokenResponse>(`${this.apiUrl}/session`, body.toString(), { headers })
      .pipe(
        tap((response) => {
          this.setToken(response.access_token);
        }),
        catchError((error) => {
          console.error('Login failed:', error);
          return throwError(() => error);
        }),
      );
  }

  register(userData: any): Observable<UserResponse> {
    return this.http.post<UserResponse>(`${this.apiUrl}/user`, userData).pipe(
      catchError((error) => {
        console.error('Registration failed:', error);
        return throwError(() => error);
      }),
    );
  }

  fetchProfile(userId: string): Observable<UserResponse> {
    return this.http.get<UserResponse>(`${this.apiUrl}/user/${userId}`).pipe(
      catchError((error) => {
        console.error('Failed to fetch profile:', error);
        return throwError(() => error);
      })
    );
  }

  updateProfile(userId: string, data: any): Observable<UserUpdateResponse> {
    return this.http.patch<UserUpdateResponse>(`${this.apiUrl}/user/${userId}`, data).pipe(
      tap((response) => {
        this.setToken(response.access_token);
      }),
      catchError((error) => {
        console.error('Failed to update profile:', error);
        return throwError(() => error);
      })
    );
  }

  uploadAvatar(userId: string, file: File): Observable<UserUpdateResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<UserUpdateResponse>(`${this.apiUrl}/user/${userId}/avatar`, formData).pipe(
      tap((response) => {
        this.setToken(response.access_token);
        this.avatarUpdateTrigger.update(v => v + 1); // Force avatar URL refresh
      }),
      catchError((error) => {
        console.error('Failed to upload avatar:', error);
        return throwError(() => error);
      })
    );
  }

  logout(): void {
    this.tokenSignal.set(null);
    localStorage.removeItem('access_token');
    this.router.navigate(['/login']);
  }

  private setToken(token: string): void {
    localStorage.setItem('access_token', token);
    this.tokenSignal.set(token);
  }
}
