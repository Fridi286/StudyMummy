import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { getApiBaseUrl } from '../config/api.config';

export interface SlotMachineRequest {
  bet_amount: number;
}

export interface SlotMachineResponse {
  result: string; // 'jackpot', 'small_win', 'loss'
  payout: number;
  net_change: number;
  new_balance: number;
  message: string;
}

@Injectable({
  providedIn: 'root'
})
export class CasinoService {
  private http = inject(HttpClient);
  private baseUrl = `${getApiBaseUrl()}/api/v1/gambling`;

  playSlotMachine(betAmount: number): Observable<SlotMachineResponse> {
    return this.http.post<SlotMachineResponse>(`${this.baseUrl}/slotmachine`, { bet_amount: betAmount });
  }
}
