import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { InventoryService, UserInventoryResponse, InventoryItem, ActiveItem } from '../../core/services/inventory.service';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { ToastModule } from 'primeng/toast';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { MessageService } from 'primeng/api';
import { AuthService } from '../../core/auth/auth.service';
import { RouterModule } from '@angular/router';
import { BackendAssetUrlPipe } from '../../shared/pipes/backend-asset-url.pipe';

@Component({
  selector: 'app-inventory',
  standalone: true,
  imports: [CommonModule, CardModule, ButtonModule, ToastModule, ProgressSpinnerModule, RouterModule, BackendAssetUrlPipe],
  providers: [MessageService],
  templateUrl: './inventory.component.html',
  styleUrls: ['./inventory.component.css']
})
export class InventoryComponent implements OnInit {
  inventoryService = inject(InventoryService);
  messageService = inject(MessageService);
  authService = inject(AuthService);

  inventory = signal<InventoryItem[]>([]);
  activeItems = signal<ActiveItem[]>([]);
  isLoading = signal(true);

  ngOnInit() {
    this.loadInventory();
  }

  loadInventory() {
    this.isLoading.set(true);
    this.inventoryService.getInventory().subscribe({
      next: (res) => {
        this.inventory.set(res.inventory);
        this.activeItems.set(res.active_items);
        this.isLoading.set(false);
      },
      error: (err) => {
        console.error('Failed to load inventory', err);
        this.isLoading.set(false);
      }
    });
  }

  useItem(inventoryItem: InventoryItem) {
    this.inventoryService.useItem(inventoryItem.item.item_id).subscribe({
      next: (res) => {
        this.messageService.add({
          severity: 'success',
          summary: 'Item Used!',
          detail: res.message
        });

        // Notify auth service to refresh user (to update XP/Coins instantly)
        if (res.instant_effects_applied) {
          // A hack to force user refresh if we don't have a direct method
          // The real app would dispatch an action or fetch profile again
          // Here we just reload the page or update local state if possible.
          // Or we can just call loadInventory to sync items.
        }

        // Re-fetch inventory to get new active items and exact quantity
        this.loadInventory();
      },
      error: (err) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: err.error?.detail || 'Failed to use item'
        });
      }
    });
  }

  unequipItem(activeItemId: string) {
    this.inventoryService.unequipItem(activeItemId).subscribe({
      next: (res) => {
        this.messageService.add({ severity: 'success', summary: 'Unequipped', detail: res.message });
        this.loadInventory(); // Reload to reflect changes
      },
      error: (err) => {
        this.messageService.add({ severity: 'error', summary: 'Error', detail: err.error?.detail || 'Failed to unequip item' });
      }
    });
  }
}
