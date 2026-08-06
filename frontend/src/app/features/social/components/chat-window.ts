import { Component, Input, Output, EventEmitter, inject, signal, ViewChild, ElementRef, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { AvatarModule } from 'primeng/avatar';
import { InputTextModule } from 'primeng/inputtext';
import { MenuModule } from 'primeng/menu';
import { MenuItem } from 'primeng/api';
import { ChatroomResponse, UserPublic, SocialService } from '../../../core/services/social.service';
import { ChatService } from '../../../core/services/chat.service';
import { AuthService } from '../../../core/auth/auth.service';
import { AvatarUrlPipe } from '../../../shared/pipes/avatar-url.pipe';
import { InitialsPipe } from '../../../shared/pipes/initials.pipe';

@Component({
  selector: 'app-chat-window',
  standalone: true,
  imports: [CommonModule, FormsModule, ButtonModule, AvatarModule, InputTextModule, MenuModule, AvatarUrlPipe, InitialsPipe],
  templateUrl: './chat-window.html'
})
export class ChatWindowComponent {
  socialService = inject(SocialService);
  chatService = inject(ChatService);
  authService = inject(AuthService);

  @ViewChild('scrollContainer') private scrollContainer!: ElementRef;

  @Output() openTrade = new EventEmitter<UserPublic>();
  @Output() removeFriend = new EventEmitter<UserPublic>();
  @Output() backToFriends = new EventEmitter<void>();

  _room: ChatroomResponse | null = null;
  chatMenuItems: MenuItem[] = [];

  @Input() set room(value: ChatroomResponse | null) {
    this._room = value;
    if (value) {
      this.loadInitialMessages(value);
      const currentUserId = this.authService.currentUser()?.user_id;
      const other = value.members.find(m => m.user_id !== currentUserId);
      if (other) {
        this.chatMenuItems = [
          { label: 'Propose Trade', icon: 'pi pi-arrow-right-arrow-left', command: () => this.openTrade.emit(other) },
          { label: 'Remove Friend', icon: 'pi pi-user-minus', styleClass: 'text-red-500', command: () => this.removeFriend.emit(other) }
        ];
      }
    } else {
      this.chatMessages.set([]);
      this.chatMenuItems = [];
    }
  }
  get room() { return this._room; }

  chatMessages = signal<any[]>([]);
  messageContent = '';
  
  isLoadingHistory = false;
  hasMoreHistory = true;
  messageOffset = 0;

  constructor() {
    effect(() => {
      const msg = this.chatService.latestMessage();
      if (msg && this.room && msg.room_id === this.room.room_id) {
        this.chatMessages.update(msgs => [...msgs, msg]);
        this.scrollToBottom();
      }
    });
  }

  loadInitialMessages(room: ChatroomResponse) {
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
    const r = this.room;
    if (!r) return;
    
    this.isLoadingHistory = true;
    this.messageOffset += 50;
    
    const previousScrollHeight = this.scrollContainer.nativeElement.scrollHeight;

    this.socialService.getChatMessages(r.room_id, this.messageOffset).subscribe(msgs => {
      if (msgs.length < 50) this.hasMoreHistory = false;
      this.chatMessages.update(current => [...msgs, ...current]);
      this.isLoadingHistory = false;
      
      setTimeout(() => {
        if (this.scrollContainer) {
          const newScrollHeight = this.scrollContainer.nativeElement.scrollHeight;
          this.scrollContainer.nativeElement.scrollTop = newScrollHeight - previousScrollHeight;
        }
      }, 0);
    });
  }

  sendMessage() {
    const r = this.room;
    if (r && this.messageContent.trim()) {
      this.chatService.sendMessage(r.room_id, this.messageContent.trim());
      this.messageContent = '';
    }
  }

  getOtherMember(): UserPublic | undefined {
    if (!this.room) return undefined;
    const currentUserId = this.authService.currentUser()?.user_id;
    return this.room.members.find(m => m.user_id !== currentUserId);
  }



  getPresence(userId: string): string {
    return this.chatService.userPresence()[userId] || 'offline';
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
