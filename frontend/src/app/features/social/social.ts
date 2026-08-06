import { Component, inject, signal, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ConfirmationService, MessageService } from 'primeng/api';
import { SocialService, ChatroomResponse, UserPublic } from '../../core/services/social.service';

import { SocialSidebarComponent } from './components/social-sidebar';
import { ChatWindowComponent } from './components/chat-window';
import { TradeDialogComponent } from './components/trade-dialog';

@Component({
  selector: 'app-social',
  standalone: true,
  imports: [CommonModule, SocialSidebarComponent, ChatWindowComponent, TradeDialogComponent],
  templateUrl: './social.html',
  styleUrl: './social.css',
})
export class Social {
  socialService = inject(SocialService);
  confirmationService = inject(ConfirmationService);
  messageService = inject(MessageService);

  @ViewChild(SocialSidebarComponent) sidebar!: SocialSidebarComponent;

  activeChatroom = signal<ChatroomResponse | null>(null);
  
  // Trading
  displayTradeModal = signal(false);
  tradeFriend = signal<UserPublic | null>(null);

  onRoomSelected(room: ChatroomResponse | null) {
    this.activeChatroom.set(room);
  }

  openTradeModal(friend: UserPublic) {
    this.tradeFriend.set(friend);
    this.displayTradeModal.set(true);
  }

  onTradeProposed() {
    this.sidebar?.refreshTrades();
  }

  onRemoveFriend(friend: UserPublic) {
    this.confirmationService.confirm({
      message: `Are you sure you want to remove ${friend.username} as a friend? This will permanently delete your chat history.`,
      header: 'Confirm Removal',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.socialService.removeFriend(friend.user_id).subscribe({
          next: () => {
            this.messageService.add({ severity: 'success', summary: 'Removed', detail: `${friend.username} has been removed.` });
            this.sidebar?.refreshFriendsAndChats();
            const room = this.activeChatroom();
            if (room && !room.is_group && room.members.some(m => m.user_id === friend.user_id)) {
              this.activeChatroom.set(null);
            }
          },
          error: (err) => {
            this.messageService.add({ severity: 'error', summary: 'Error', detail: err.error?.detail || 'Failed to remove friend' });
          }
        });
      }
    });
  }
}
