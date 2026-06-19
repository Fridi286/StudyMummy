import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Item {
  item_id: string;
  name: string;
  type: string;
  icon_url?: string;
  effects?: Record<string, any>;
  cost: number;
}

export interface InventoryItem {
  inventory_id: string;
  quantity: number;
  acquired_at: string;
  item: Item;
}

export interface ActiveItem {
  active_item_id: string;
  name: string;
  effects: Record<string, any>;
  activated_at: string;
  expires_at?: string;
  item: Item;
}

export interface UserInventoryResponse {
  inventory: InventoryItem[];
  active_items: ActiveItem[];
}

export interface UseItemResponse {
  message: string;
  inventory_item: InventoryItem;
  active_item?: ActiveItem;
  instant_effects_applied?: Record<string, any>;
}

@Injectable({
  providedIn: 'root'
})
export class InventoryService {
  private http = inject(HttpClient);
  private baseUrl = 'http://localhost:8000/api/v1/inventory';

  getInventory(): Observable<UserInventoryResponse> {
    return this.http.get<UserInventoryResponse>(this.baseUrl);
  }

  useItem(itemId: string): Observable<UseItemResponse> {
    return this.http.post<UseItemResponse>(`${this.baseUrl}/items/${itemId}/use`, {});
  }

  unequipItem(activeItemId: string): Observable<{message: string}> {
    return this.http.post<{message: string}>(`${this.baseUrl}/active-items/${activeItemId}/unequip`, {});
  }
}
