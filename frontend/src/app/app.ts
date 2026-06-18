import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AuthService } from './core/auth/auth.service';
import { HeaderComponent } from './core/layout/header/header.component';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, HeaderComponent, ToastModule, ConfirmDialogModule],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  constructor(public authService: AuthService) {}
}
