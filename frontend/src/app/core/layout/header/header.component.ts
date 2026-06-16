import { Component, OnInit, computed } from '@angular/core';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../auth/auth.service';
import { ButtonModule } from 'primeng/button';
import { MenuModule } from 'primeng/menu';
import { MenuItem } from 'primeng/api';
import { AvatarModule } from 'primeng/avatar';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [RouterLink, ButtonModule, MenuModule, AvatarModule],
  templateUrl: './header.component.html',
})
export class HeaderComponent implements OnInit {
  menuItems: MenuItem[] | undefined;

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

  constructor(public authService: AuthService) {}

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

  onLogout() {
    this.authService.logout();
  }
}
