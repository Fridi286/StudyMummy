import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
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
  private baseUrl = 'http://localhost:8000/api/v1/shop';

  getShopItems(): Observable<Item[]> {
    return this.http.get<Item[]>(`${this.baseUrl}/items`);
  }

  buyItem(itemId: string, quantity: number): Observable<BuyResponse> {
    return this.http.post<BuyResponse>(`${this.baseUrl}/items/${itemId}/buy`, { quantity });
  }
}
