import { Component, OnInit, OnDestroy, computed, inject, signal, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterLinkActive, Router, NavigationEnd } from '@angular/router';
import { filter } from 'rxjs/operators';
import { AuthService } from '../../auth/auth.service';
import { SocialService, FriendshipResponse } from '../../services/social.service';
import { ChatService } from '../../services/chat.service';
import { ButtonModule } from 'primeng/button';
import { MenuItem } from 'primeng/api';
import { AvatarModule } from 'primeng/avatar';
import { BadgeModule } from 'primeng/badge';
import { PopoverModule } from 'primeng/popover';
import { AvatarUrlPipe } from '../../../shared/pipes/avatar-url.pipe';
import { InitialsPipe } from '../../../shared/pipes/initials.pipe';
import { ActionMenuComponent } from '../../../shared/components/action-menu/action-menu';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [
    CommonModule, RouterLink, RouterLinkActive, ButtonModule, AvatarModule, BadgeModule, PopoverModule,
    AvatarUrlPipe, InitialsPipe, ActionMenuComponent
  ],
  templateUrl: './header.component.html',
})
export class HeaderComponent implements OnInit, OnDestroy {
  authService = inject(AuthService);
  socialService = inject(SocialService);
  chatService = inject(ChatService);
  router = inject(Router);

  menuItems: MenuItem[] | undefined;
  
  pendingRequests = signal<FriendshipResponse[]>([]);
  currentTime = signal(new Date());
  isCasinoPage = signal(false);
  clockInterval: any;

  userInitials = computed(() => {
    const user = this.authService.currentUser();
    if (!user) return 'SM';
    
    if (user.first_name && user.last_name) {
      return `${user.first_name[0]}${user.last_name[0]}`.toUpperCase();
    }
    
    if (user.username) {
      return user.username.substring(0, 2).toUpperCase();
    }
    
    return 'SM';
  });

  fullAvatarUrl = computed(() => {
    return this.authService.cachedAvatarUrl();
  });

  constructor() {
    // React to incoming WebSocket friend request notifications
    effect(() => {
      const notification = this.chatService.latestNotification();
      if (notification) {
        if (notification.type === 'FRIEND_REQUEST') {
          this.loadPendingRequests();
        }
      }
    });

    // React to auth state - load pending requests as soon as user is authenticated,
    // even on page refresh where auth might resolve after component init
    effect(() => {
      const user = this.authService.currentUser();
      if (user) {
        this.loadPendingRequests();
      } else {
        this.pendingRequests.set([]);
      }
    });

    this.router.events.pipe(
      filter(event => event instanceof NavigationEnd)
    ).subscribe((event: any) => {
      this.isCasinoPage.set(event.urlAfterRedirects.includes('/casino'));
    });

    // Initial check
    setTimeout(() => {
      this.isCasinoPage.set(this.router.url.includes('/casino'));
    }, 0);

    this.clockInterval = setInterval(() => {
      this.currentTime.set(new Date());
    }, 1000);
  }

  ngOnDestroy() {
    if (this.clockInterval) {
      clearInterval(this.clockInterval);
    }
  }

  ngOnInit() {
    this.menuItems = [
      {
        label: 'Account',
        items: [
          {
            label: 'Profile',
            icon: 'pi pi-user',
            routerLink: '/profile'
          },
          {
            label: 'Documents',
            icon: 'pi pi-file',
            routerLink: '/documents'
          },
          {
            label: 'Calendar',
            icon: 'pi pi-calendar',
            routerLink: '/calendar'
          },
          {
            label: 'Inventory',
            icon: 'pi pi-box',
            routerLink: '/inventory'
          }
        ]
      },
      {
        label: 'Status',
        items: [
          {
            label: '<div class="flex items-center gap-2"><div class="w-2.5 h-2.5 rounded-full bg-green-500"></div><span>Set Online</span></div>',
            escape: false,
            command: () => this.chatService.setStatus('online')
          },
          {
            label: '<div class="flex items-center gap-2"><div class="w-2.5 h-2.5 rounded-full bg-yellow-500"></div><span>Set Away</span></div>',
            escape: false,
            command: () => this.chatService.setStatus('away')
          }
        ]
      },
      {
        label: 'Actions',
        items: [
          {
            label: 'Sign Out',
            icon: 'pi pi-sign-out',
            command: () => this.onLogout()
          }
        ]
      }
    ];
  }

  get myPresence(): string {
    const user = this.authService.currentUser();
    if (!user) return 'offline';
    return this.chatService.userPresence()[user.user_id] || 'online'; // assume online if connected
  }

  loadPendingRequests() {
    this.socialService.getFriends().subscribe(res => {
      this.pendingRequests.set(res.pending_incoming);
    });
  }

  acceptRequest(req: FriendshipResponse) {
    this.socialService.acceptFriendRequest(req.friendship_id).subscribe(() => {
      this.loadPendingRequests();
    });
  }

  declineRequest(req: FriendshipResponse) {
    this.socialService.declineFriendRequest(req.friendship_id).subscribe(() => {
      this.loadPendingRequests();
    });
  }

  onLogout() {
    this.authService.logout();
  }

}
