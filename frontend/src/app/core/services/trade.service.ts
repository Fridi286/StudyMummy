import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { UserPublic } from './social.service';
import { getApiBaseUrl } from '../config/api.config';

export interface TradeItemCreate {
  item_id: string;
  quantity: number;
  owner_id: string;
}

export interface TradeCreate {
  receiver_id: string;
  sender_coins: number;
  receiver_coins: number;
  trade_items: TradeItemCreate[];
}

export interface TradeItemResponse {
  trade_item_id: string;
  trade_id: string;
  owner_id: string;
  item: any; // Using any for simplicity here, matches ItemResponse
  quantity: number;
}

export interface TradeResponse {
  trade_id: string;
  sender_id: string;
  receiver_id: string;
  sender_coins: number;
  receiver_coins: number;
  status: string;
  created_at: string;
  updated_at: string;
  sender: UserPublic;
  receiver: UserPublic;
  trade_items: TradeItemResponse[];
}

@Injectable({
  providedIn: 'root'
})
export class TradeService {
  private http = inject(HttpClient);
  private apiUrl = `${getApiBaseUrl()}/api/v1/economy/trades`;

  createTrade(trade: TradeCreate): Observable<TradeResponse> {
    return this.http.post<TradeResponse>(this.apiUrl, trade);
  }

  getPendingTrades(): Observable<TradeResponse[]> {
    return this.http.get<TradeResponse[]>(`${this.apiUrl}/pending`);
  }

  acceptTrade(tradeId: string): Observable<TradeResponse> {
    return this.http.post<TradeResponse>(`${this.apiUrl}/${tradeId}/accept`, {});
  }

  rejectTrade(tradeId: string): Observable<TradeResponse> {
    return this.http.post<TradeResponse>(`${this.apiUrl}/${tradeId}/reject`, {});
  }

  cancelTrade(tradeId: string): Observable<TradeResponse> {
    return this.http.post<TradeResponse>(`${this.apiUrl}/${tradeId}/cancel`, {});
  }
}
