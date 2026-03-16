import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';
import { tap } from 'rxjs/operators';
import { User } from '../shared/models/user.model';
import { environment } from '../../environments/environment';


interface LoginResponse {
  access_token: string;
  token_type: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private tokenKey = 'access_token';
  private _currentUser$ = new BehaviorSubject<User | null>(null);
  readonly currentUser$ = this._currentUser$.asObservable();

  private userCache = new Map<string, User>();

  constructor(private http: HttpClient) {
    if (this.getToken()) {
      this.fetchCurrentUser().subscribe();
    }
  }

  register(data: { username: string; email: string; password: string }) {
    return this.http.post(`${environment.apiBaseUrl}api/auth/register`, data);
  }

  login(data: { email: string; password: string }): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${environment.apiBaseUrl}api/auth/login`, data).pipe(
      tap(res => {
        localStorage.setItem(this.tokenKey, res.access_token);
        this.fetchCurrentUser().subscribe();
      })
    );
  }

  fetchCurrentUser(): Observable<User> {
    return this.http.get<User>(`${environment.apiBaseUrl}api/users/me`).pipe(
      tap(user => {
        this._currentUser$.next(user);
        this.cacheUser(user);
      })
    );
  }

  logout() {
    localStorage.removeItem(this.tokenKey);
    this._currentUser$.next(null);
    this.userCache.clear();
  }

  getToken(): string | null {
    return localStorage.getItem(this.tokenKey);
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  getCurrentUserId(): string | null {
    return this._currentUser$.value?.id ?? null;
  }

  cacheUser(user: User): void {
    this.userCache.set(user.id, user);
  }

  getCachedUser(id: string): User | null {
    return this.userCache.get(id) ?? null;
  }
}
