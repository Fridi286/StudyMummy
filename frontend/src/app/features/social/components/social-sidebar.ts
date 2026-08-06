import { Component, OnInit, inject, signal, Output, EventEmitter, Input, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AutoCompleteModule, AutoCompleteCompleteEvent } from 'primeng/autocomplete';
import { ButtonModule } from 'primeng/button';
import { AvatarModule } from 'primeng/avatar';
import { MessageService } from 'primeng/api';
import { SocialService, FriendshipResponse, UserPublic, ChatroomResponse } from '../../../core/services/social.service';
import { TradeService, TradeResponse } from '../../../core/services/trade.service';
import { AuthService } from '../../../core/auth/auth.service';
import { ChatService } from '../../../core/services/chat.service';
import { AvatarUrlPipe } from '../../../shared/pipes/avatar-url.pipe';
import { InitialsPipe } from '../../../shared/pipes/initials.pipe';
import { BackendAssetUrlPipe } from '../../../shared/pipes/backend-asset-url.pipe';

@Component({
  selector: 'app-social-sidebar',
  standalone: true,
  imports: [CommonModule, FormsModule, AutoCompleteModule, ButtonModule, AvatarModule, AvatarUrlPipe, InitialsPipe, BackendAssetUrlPipe],
  templateUrl: './social-sidebar.html'
})
export class SocialSidebarComponent implements OnInit {
  socialService = inject(SocialService);
  tradeService = inject(TradeService);
  authService = inject(AuthService);
  chatService = inject(ChatService);
  messageService = inject(MessageService);

  constructor() {
    effect(() => {
      const updateCount = this.chatService.latestTradeUpdate();
      if (updateCount > 0) {
        this.loadPendingTrades();
      }
    });
  }

  @Input() activeRoomId: string | undefined;
  @Output() roomSelected = new EventEmitter<ChatroomResponse>();

  friends = signal<FriendshipResponse[]>([]);
  pendingRequests = signal<FriendshipResponse[]>([]);
  pendingOutgoing = signal<FriendshipResponse[]>([]);
  chatrooms = signal<ChatroomResponse[]>([]);
  pendingTrades = signal<TradeResponse[]>([]);

  searchQuery: any = '';
  searchResults = signal<UserPublic[]>([]);

  tradesSectionExpanded = signal(false);

  toggleTradesSection() {
    this.tradesSectionExpanded.update(v => !v);
  }

  ngOnInit() {
    this.loadFriends();
    this.loadChatrooms();
    this.loadPendingTrades();
  }

  loadFriends() {
    this.socialService.getFriends().subscribe(res => {
      this.friends.set(res.friends);
      this.pendingRequests.set(res.pending_incoming);
      this.pendingOutgoing.set(res.pending_outgoing);
    });
  }

  loadChatrooms() {
    this.socialService.getChatrooms().subscribe(res => {
      this.chatrooms.set(res);
    });
  }

  loadPendingTrades() {
    this.tradeService.getPendingTrades().subscribe(trades => {
      this.pendingTrades.set(trades);
    });
  }

  // --- Search & Requests ---
  searchUsers(event: AutoCompleteCompleteEvent) {
    if (event.query.length >= 1) {
      this.socialService.searchUsers(event.query).subscribe(users => {
        const friendIds = this.friends().map(f => f.friend.user_id);
        const incomingIds = this.pendingRequests().map(f => f.friend.user_id);
        const outgoingIds = this.pendingOutgoing().map(f => f.friend.user_id);
        const excludeIds = [...friendIds, ...incomingIds, ...outgoingIds];
        this.searchResults.set(users.filter(u => !excludeIds.includes(u.user_id)));
      });
    } else {
      this.searchResults.set([]);
    }
  }

  sendFriendRequest(user: UserPublic) {
    this.socialService.sendFriendRequest(user.user_id).subscribe({
      next: () => {
        this.messageService.add({ severity: 'success', summary: 'Request Sent', detail: `Friend request sent to ${user.username}!` });
        this.searchQuery = '';
        this.loadFriends();
      },
      error: (err) => {
        this.messageService.add({ severity: 'error', summary: 'Error', detail: err.error?.detail || 'Failed to send friend request' });
      }
    });
  }

  onUserSelect(event: any) {
    this.sendFriendRequest(event.value);
    setTimeout(() => { this.searchQuery = ''; });
  }

  acceptRequest(req: FriendshipResponse) {
    this.socialService.acceptFriendRequest(req.friendship_id).subscribe(() => {
      this.loadFriends();
      this.loadChatrooms();
    });
  }

  declineRequest(req: FriendshipResponse) {
    this.socialService.declineFriendRequest(req.friendship_id).subscribe(() => {
      this.loadFriends();
    });
  }

  // --- Trades ---
  acceptTrade(trade: TradeResponse) {
    this.tradeService.acceptTrade(trade.trade_id).subscribe({
      next: () => {
        const received = [];
        if (trade.sender_coins > 0) received.push(`${trade.sender_coins} coins`);
        const rItems = this.getOfferedItems(trade).map((i: any) => `${i.quantity}x ${i.item.name}`);
        if (rItems.length) received.push(...rItems);

        const given = [];
        if (trade.receiver_coins > 0) given.push(`${trade.receiver_coins} coins`);
        const gItems = this.getRequestedItems(trade).map((i: any) => `${i.quantity}x ${i.item.name}`);
        if (gItems.length) given.push(...gItems);

        let detail = `Trade with ${trade.sender.username} complete!`;
        if (received.length) detail += `\nReceived: ${received.join(', ')}.`;
        if (given.length) detail += `\nGave: ${given.join(', ')}.`;

        this.messageService.add({ severity: 'success', summary: 'Trade Accepted', detail: detail, life: 5000 });
        this.loadPendingTrades();
      },
      error: (err) => {
        this.messageService.add({ severity: 'error', summary: 'Trade Error', detail: err.error?.detail || 'Failed to accept trade.' });
      }
    });
  }

  rejectTrade(trade: TradeResponse) {
    this.tradeService.rejectTrade(trade.trade_id).subscribe(() => {
      this.loadPendingTrades();
    });
  }

  cancelTrade(trade: TradeResponse) {
    this.tradeService.cancelTrade(trade.trade_id).subscribe(() => {
      this.loadPendingTrades();
    });
  }

  getOfferedItems(trade: any) {
    return trade.trade_items?.filter((i: any) => i.owner_id === trade.sender_id) || [];
  }

  getRequestedItems(trade: any) {
    return trade.trade_items?.filter((i: any) => i.owner_id === trade.receiver_id) || [];
  }

  // --- Chatrooms ---
  selectChatroom(room: ChatroomResponse) {
    this.roomSelected.emit(room);
  }

  getOtherMember(room: ChatroomResponse): UserPublic | undefined {
    const currentUserId = this.authService.currentUser()?.user_id;
    return room.members.find(m => m.user_id !== currentUserId);
  }

  getPresence(userId: string): string {
    return this.chatService.userPresence()[userId] || 'offline';
  }

  // Expose these methods to allow parent to trigger refreshes
  refreshFriendsAndChats() {
    this.loadFriends();
    this.loadChatrooms();
  }

  refreshTrades() {
    this.loadPendingTrades();
  }
}
