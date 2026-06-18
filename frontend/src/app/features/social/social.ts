import { Component, inject, OnInit, signal, computed, effect, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AutoCompleteModule, AutoCompleteCompleteEvent } from 'primeng/autocomplete';
import { ButtonModule } from 'primeng/button';
import { AvatarModule } from 'primeng/avatar';
import { InputTextModule } from 'primeng/inputtext';
import { TooltipModule } from 'primeng/tooltip';
import { MenuModule } from 'primeng/menu';
import { MenuItem, ConfirmationService, MessageService } from 'primeng/api';
import { SocialService, UserPublic, FriendshipResponse, ChatroomResponse } from '../../core/services/social.service';
import { ChatService } from '../../core/services/chat.service';
import { AuthService } from '../../core/auth/auth.service';
import { AvatarUrlPipe } from '../../shared/pipes/avatar-url.pipe';
import { InitialsPipe } from '../../shared/pipes/initials.pipe';

@Component({
  selector: 'app-social',
  standalone: true,
  imports: [
    CommonModule, FormsModule, AutoCompleteModule, ButtonModule, AvatarModule, InputTextModule,
    TooltipModule, MenuModule, AvatarUrlPipe, InitialsPipe
  ],
  templateUrl: './social.html',
  styleUrl: './social.css',
})
export class Social implements OnInit {
  socialService = inject(SocialService);
  chatService = inject(ChatService);
  authService = inject(AuthService);
  confirmationService = inject(ConfirmationService);
  messageService = inject(MessageService);

  @ViewChild('scrollContainer') private scrollContainer!: ElementRef;

  friends = signal<FriendshipResponse[]>([]);
  pendingRequests = signal<FriendshipResponse[]>([]);
  pendingOutgoing = signal<FriendshipResponse[]>([]);
  chatrooms = signal<ChatroomResponse[]>([]);
  activeChatroom = signal<ChatroomResponse | null>(null);
  chatMessages = signal<any[]>([]);

  // Search
  searchQuery: any = '';
  searchResults = signal<UserPublic[]>([]);

  // Input
  messageContent = '';

  // Pagination
  isLoadingHistory = false;
  hasMoreHistory = true;
  messageOffset = 0;

  constructor() {
    effect(() => {
      const msg = this.chatService.latestMessage();
      if (msg && this.activeChatroom() && msg.room_id === this.activeChatroom()?.room_id) {
        this.chatMessages.update(msgs => [...msgs, msg]);
        this.scrollToBottom();
      }
    });
  }

  ngOnInit() {
    this.loadFriends();
    this.loadChatrooms();
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

  searchUsers(event: AutoCompleteCompleteEvent) {
    if (event.query.length >= 3) {
      this.socialService.searchUsers(event.query).subscribe(users => {
        // filter out users already in friends or pending
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
        this.messageService.add({
          severity: 'success',
          summary: 'Request Sent',
          detail: `Friend request sent to ${user.username}!`
        });
        this.searchQuery = '';
        this.loadFriends(); // Refresh to update outgoing requests
      },
      error: (err) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: err.error?.detail || 'Failed to send friend request'
        });
      }
    });
  }

  onUserSelect(event: any) {
    this.sendFriendRequest(event.value);
    setTimeout(() => {
      this.searchQuery = '';
    });
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

  removeFriend(friend: UserPublic) {
    this.confirmationService.confirm({
      message: `Are you sure you want to remove ${friend.username} as a friend? This will permanently delete your chat history.`,
      header: 'Confirm Removal',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.socialService.removeFriend(friend.user_id).subscribe({
          next: () => {
            this.messageService.add({
              severity: 'success',
              summary: 'Removed',
              detail: `${friend.username} has been removed.`
            });
            this.loadFriends();
            this.loadChatrooms();
            const room = this.activeChatroom();
            if (room && !room.is_group && room.members.some(m => m.user_id === friend.user_id)) {
              this.activeChatroom.set(null);
              this.chatMessages.set([]);
            }
          },
          error: (err) => {
            this.messageService.add({
              severity: 'error',
              summary: 'Error',
              detail: err.error?.detail || 'Failed to remove friend'
            });
          }
        });
      }
    });
  }

  openChatWithFriend(friend: UserPublic) {
    // Check if direct chatroom already exists
    const existingRoom = this.chatrooms().find(r => !r.is_group && r.members.some(m => m.user_id === friend.user_id));
    if (existingRoom) {
      this.selectChatroom(existingRoom);
    } else {
      this.messageService.add({
        severity: 'info',
        summary: 'No Chatroom',
        detail: 'No chatroom exists yet. It will be created when the request is accepted.'
      });
    }
  }

  selectChatroom(room: ChatroomResponse) {
    this.activeChatroom.set(room);
    this.messageOffset = 0;
    this.hasMoreHistory = true;
    this.isLoadingHistory = false;

    this.socialService.getChatMessages(room.room_id, this.messageOffset).subscribe(msgs => {
      this.chatMessages.set(msgs);
      if (msgs.length < 50) this.hasMoreHistory = false;
      this.scrollToBottom();
    });
  }

  onScroll(event: any) {
    if (this.isLoadingHistory || !this.hasMoreHistory) return;
    if (event.target.scrollTop === 0) {
      this.loadMoreMessages();
    }
  }

  loadMoreMessages() {
    const room = this.activeChatroom();
    if (!room) return;
    
    this.isLoadingHistory = true;
    this.messageOffset += 50;
    
    // Remember the previous scroll height to maintain position
    const previousScrollHeight = this.scrollContainer.nativeElement.scrollHeight;

    this.socialService.getChatMessages(room.room_id, this.messageOffset).subscribe(msgs => {
      if (msgs.length < 50) {
        this.hasMoreHistory = false;
      }
      
      // Prepend messages
      this.chatMessages.update(current => [...msgs, ...current]);
      this.isLoadingHistory = false;
      
      // Restore scroll position
      setTimeout(() => {
        if (this.scrollContainer) {
          const newScrollHeight = this.scrollContainer.nativeElement.scrollHeight;
          this.scrollContainer.nativeElement.scrollTop = newScrollHeight - previousScrollHeight;
        }
      }, 0);
    });
  }

  sendMessage() {
    const room = this.activeChatroom();
    if (room && this.messageContent.trim()) {
      this.chatService.sendMessage(room.room_id, this.messageContent.trim());
      this.messageContent = '';
    }
  }

  getChatMenuItems(friend: UserPublic): MenuItem[] {
    return [
      {
        label: 'Remove Friend',
        icon: 'pi pi-user-minus',
        styleClass: 'text-red-500',
        command: () => this.removeFriend(friend)
      }
    ];
  }

  getOtherMember(room: ChatroomResponse): UserPublic | undefined {
    const currentUserId = this.authService.currentUser()?.user_id;
    return room.members.find(m => m.user_id !== currentUserId);
  }

  private scrollToBottom() {
    setTimeout(() => {
      if (this.scrollContainer) {
        try {
          this.scrollContainer.nativeElement.scrollTop = this.scrollContainer.nativeElement.scrollHeight;
        } catch(err) { }
      }
    }, 100);
  }
}
