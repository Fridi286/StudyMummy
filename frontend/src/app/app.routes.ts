import { Routes } from '@angular/router';
import { LoginComponent } from './features/auth/login/login.component';
import { RegisterComponent } from './features/auth/register/register.component';
import { DashboardComponent } from './features/dashboard/dashboard.component';
import { ProfileComponent } from './features/profile/profile.component';
import { authGuard } from './core/auth/auth.guard';
import { Social } from './features/social/social';
import { AiChatComponent } from './features/ai-chat/ai-chat.component';
import { InventoryComponent } from './features/inventory/inventory.component';
import { ShopComponent } from './features/shop/shop.component';
import { CasinoComponent } from './features/casino/casino.component';

export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: 'register', component: RegisterComponent },
  { path: 'social', component: Social, canActivate: [authGuard] },
  { path: 'ai-chat', component: AiChatComponent, canActivate: [authGuard] },
  { path: 'profile', component: ProfileComponent, canActivate: [authGuard] },
  { path: 'inventory', component: InventoryComponent, canActivate: [authGuard] },
  { path: 'shop', component: ShopComponent, canActivate: [authGuard] },
  { path: 'casino', component: CasinoComponent, canActivate: [authGuard] },
  { path: '', component: DashboardComponent, canActivate: [authGuard], pathMatch: 'full' },
  { path: '**', redirectTo: '' },
];
