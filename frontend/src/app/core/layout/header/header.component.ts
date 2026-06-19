import { Component, OnInit, OnDestroy, computed, inject, signal, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, Router, NavigationEnd } from '@angular/router';
import { filter } from 'rxjs/operators';
import { AuthService } from '../../auth/auth.service';
import { SocialService, FriendshipResponse } from '../../services/social.service';
import { ChatService } from '../../services/chat.service';
import { ButtonModule } from 'primeng/button';
import { MenuModule } from 'primeng/menu';
import { MenuItem } from 'primeng/api';
import { AvatarModule } from 'primeng/avatar';
import { BadgeModule } from 'primeng/badge';
import { PopoverModule } from 'primeng/popover';
import { AvatarUrlPipe } from '../../../shared/pipes/avatar-url.pipe';
import { InitialsPipe } from '../../../shared/pipes/initials.pipe';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [
    CommonModule, RouterLink, ButtonModule, MenuModule, AvatarModule, BadgeModule, PopoverModule,
    AvatarUrlPipe, InitialsPipe
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
            label: 'Inventory',
            icon: 'pi pi-box',
            routerLink: '/inventory'
          },
          {
            label: 'Shop',
            icon: 'pi pi-shopping-cart',
            routerLink: '/shop'
          },
          {
            separator: true
          },
          {
            label: 'Sign Out',
            icon: 'pi pi-sign-out',
            command: () => this.onLogout()
          }
        ]
      }
    ];
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
