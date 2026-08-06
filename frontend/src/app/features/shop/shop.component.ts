import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ShopService } from '../../core/services/shop.service';
import { InventoryService, Item } from '../../core/services/inventory.service';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { ToastModule } from 'primeng/toast';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { InputNumberModule } from 'primeng/inputnumber';
import { TabsModule } from 'primeng/tabs';
import { MessageService } from 'primeng/api';
import { AuthService } from '../../core/auth/auth.service';
import { BackendAssetUrlPipe } from '../../shared/pipes/backend-asset-url.pipe';

interface ShopItemModel extends Item {
  buyQuantity: number;
}

@Component({
  selector: 'app-shop',
  standalone: true,
  imports: [CommonModule, FormsModule, CardModule, ButtonModule, ToastModule, ProgressSpinnerModule, InputNumberModule, TabsModule, BackendAssetUrlPipe],
  providers: [MessageService],
  templateUrl: './shop.component.html'
})
export class ShopComponent implements OnInit {
  shopService = inject(ShopService);
  inventoryService = inject(InventoryService);
  messageService = inject(MessageService);
  authService = inject(AuthService);

  shopCategories = signal<{type: string, items: ShopItemModel[]}[]>([]);
  ownedItems = signal<Set<string>>(new Set());
  isLoading = signal(true);
  isBuying = signal<string | null>(null);
  currentCoins = signal<number>(0);

  ngOnInit() {
    this.loadShop();
    this.loadCoins();
  }

  loadCoins() {
    const userId = this.authService.currentUser()?.user_id;
    if (userId) {
      this.authService.fetchProfile(userId).subscribe({
        next: (profile) => this.currentCoins.set(profile.coins),
        error: (err) => console.error("Failed to load coins", err)
      });
    }
  }

  loadShop() {
    this.isLoading.set(true);
    
    // Fetch both shop items and inventory to determine ownership
    this.inventoryService.getInventory().subscribe({
      next: (invRes) => {
        const owned = new Set<string>();
        invRes.inventory.forEach(i => owned.add(i.item.item_id));
        invRes.active_items.forEach(a => owned.add(a.item.item_id)); // just in case it's active instead of inventory
        this.ownedItems.set(owned);
        
        this.shopService.getShopItems().subscribe({
          next: (items) => {
            const models = items.map(i => ({...i, buyQuantity: 1}));
            
            const groups: Record<string, ShopItemModel[]> = {};
            for (const m of models) {
                const t = m.type.toUpperCase();
                if (!groups[t]) groups[t] = [];
                groups[t].push(m);
            }
            
            const categories = Object.keys(groups).map(k => ({ type: k, items: groups[k] }));
            
            this.shopCategories.set(categories);
            this.isLoading.set(false);
          },
          error: (err) => {
            this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to load shop items' });
            this.isLoading.set(false);
          }
        });
      },
      error: (err) => {
        console.error("Failed to fetch inventory for ownership", err);
        this.isLoading.set(false);
      }
    });
  }

  buyItem(item: ShopItemModel) {
    if (item.buyQuantity <= 0) return;
    
    this.isBuying.set(item.item_id);
    this.shopService.buyItem(item.item_id, item.buyQuantity).subscribe({
      next: (res) => {
        this.messageService.add({ severity: 'success', summary: 'Purchased!', detail: res.message });
        this.isBuying.set(null);
        this.currentCoins.set(res.new_coin_balance);
        item.buyQuantity = 1; // reset quantity
        
        // Update owned status locally without reloading everything
        if (item.type.toUpperCase() === 'COSMETIC') {
           const newOwned = new Set(this.ownedItems());
           newOwned.add(item.item_id);
           this.ownedItems.set(newOwned);
        }
      },
      error: (err) => {
        this.messageService.add({ severity: 'error', summary: 'Purchase Failed', detail: err.error?.detail || 'Failed to buy item' });
        this.isBuying.set(null);
      }
    });
  }
}
