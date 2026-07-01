import { Component, Input, Output, EventEmitter, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DialogModule } from 'primeng/dialog';
import { ButtonModule } from 'primeng/button';
import { InputNumberModule } from 'primeng/inputnumber';
import { MessageService } from 'primeng/api';
import { TradeService, TradeItemCreate } from '../../../core/services/trade.service';
import { InventoryService, InventoryItem } from '../../../core/services/inventory.service';
import { AuthService } from '../../../core/auth/auth.service';
import { UserPublic } from '../../../core/services/social.service';
import { AvatarUrlPipe } from '../../../shared/pipes/avatar-url.pipe';

@Component({
  selector: 'app-trade-dialog',
  standalone: true,
  imports: [CommonModule, FormsModule, DialogModule, ButtonModule, InputNumberModule, AvatarUrlPipe],
  templateUrl: './trade-dialog.html'
})
export class TradeDialogComponent {
  authService = inject(AuthService);
  tradeService = inject(TradeService);
  inventoryService = inject(InventoryService);
  messageService = inject(MessageService);

  @Input() visible = false;
  @Output() visibleChange = new EventEmitter<boolean>();
  
  @Output() tradeProposed = new EventEmitter<void>();

  _targetUser: UserPublic | null = null;
  @Input() set targetUser(user: UserPublic | null) {
    this._targetUser = user;
    if (user) {
      this.resetTrade();
      this.loadInventories(user);
    }
  }
  get targetUser() { return this._targetUser; }

  myInventory = signal<InventoryItem[]>([]);
  friendInventory = signal<InventoryItem[]>([]);
  offerCoins = 0;
  requestCoins = 0;
  offerItems = signal<Record<string, number>>({});
  requestItems = signal<Record<string, number>>({});

  close() {
    this.visible = false;
    this.visibleChange.emit(false);
  }

  resetTrade() {
    this.offerCoins = 0;
    this.requestCoins = 0;
    this.offerItems.set({});
    this.requestItems.set({});
  }

  loadInventories(friend: UserPublic) {
    this.inventoryService.getInventory().subscribe(res => {
      this.myInventory.set(res.inventory);
    });
    this.inventoryService.getUserInventory(friend.user_id).subscribe(res => {
      this.friendInventory.set(res.inventory);
    });
  }

  changeOfferItem(itemId: string, delta: number, max: number) {
    this.offerItems.update(items => {
      const current = items[itemId] || 0;
      const next = Math.max(0, Math.min(max, current + delta));
      if (next === 0) {
        const copy = {...items};
        delete copy[itemId];
        return copy;
      }
      return {...items, [itemId]: next};
    });
  }
  
  changeRequestItem(itemId: string, delta: number, max: number) {
    this.requestItems.update(items => {
      const current = items[itemId] || 0;
      const next = Math.max(0, Math.min(max, current + delta));
      if (next === 0) {
        const copy = {...items};
        delete copy[itemId];
        return copy;
      }
      return {...items, [itemId]: next};
    });
  }

  submitTrade() {
    const friend = this.targetUser;
    const currentUser = this.authService.currentUser();
    if (!friend || !currentUser) return;
    
    const tradeItems: TradeItemCreate[] = [];
    
    // Add offered items
    Object.entries(this.offerItems()).forEach(([itemId, qty]) => {
      tradeItems.push({ item_id: itemId, quantity: qty, owner_id: currentUser.user_id });
    });
    
    // Add requested items
    Object.entries(this.requestItems()).forEach(([itemId, qty]) => {
      tradeItems.push({ item_id: itemId, quantity: qty, owner_id: friend.user_id });
    });
    
    this.tradeService.createTrade({
      receiver_id: friend.user_id,
      sender_coins: this.offerCoins,
      receiver_coins: this.requestCoins,
      trade_items: tradeItems
    }).subscribe({
      next: () => {
        this.messageService.add({ severity: 'success', summary: 'Trade Proposed', detail: 'Your trade offer was sent!' });
        this.tradeProposed.emit();
        this.close();
      },
      error: (err) => {
        this.messageService.add({ severity: 'error', summary: 'Trade Error', detail: err.error?.detail || 'Failed to propose trade.' });
      }
    });
  }
}
