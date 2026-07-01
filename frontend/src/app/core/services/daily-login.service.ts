import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { getApiBaseUrl } from '../config/api.config';

export interface DailyLoginStatus {
  last_login_date: string | null;
  current_streak: number;
  can_claim_today: boolean;
  reward_amount: number;
}

export interface DailyLoginClaimResponse {
  coins_awarded: number;
  new_balance: number;
  current_streak: number;
  message: string;
}

export interface DailyLoginHistoryResponse {
  history: string[];
}

@Injectable({
  providedIn: 'root'
})
export class DailyLoginService {
  private http = inject(HttpClient);
  private apiUrl = `${getApiBaseUrl()}/api/v1/daily-login`;

  getStatus(): Observable<DailyLoginStatus> {
    return this.http.get<DailyLoginStatus>(`${this.apiUrl}/status`);
  }

  claimReward(): Observable<DailyLoginClaimResponse> {
    return this.http.post<DailyLoginClaimResponse>(`${this.apiUrl}/claim`, {});
  }

  getHistory(): Observable<DailyLoginHistoryResponse> {
    return this.http.get<DailyLoginHistoryResponse>(`${this.apiUrl}/history`);
  }
}
