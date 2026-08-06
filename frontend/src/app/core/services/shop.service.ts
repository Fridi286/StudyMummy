import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_V1 } from '../config/api.config';
import { Item } from './inventory.service';

export interface BuyResponse {
  message: string;
  new_coin_balance: number;
}

@Injectable({
  providedIn: 'root'
})
export class ShopService {
  private http = inject(HttpClient);
  private baseUrl = `${API_V1}/shop`;

  getShopItems(): Observable<Item[]> {
    return this.http.get<Item[]>(`${this.baseUrl}/items`);
  }

  buyItem(itemId: string, quantity: number): Observable<BuyResponse> {
    return this.http.post<BuyResponse>(`${this.baseUrl}/items/${itemId}/buy`, { quantity });
  }
}
