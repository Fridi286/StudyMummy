import { Component, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../../core/auth/auth.service';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { PasswordModule } from 'primeng/password';
import { FloatLabelModule } from 'primeng/floatlabel';
import { CardModule } from 'primeng/card';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [
    FormsModule,
    RouterLink,
    ButtonModule,
    InputTextModule,
    PasswordModule,
    FloatLabelModule,
    CardModule,
  ],
  templateUrl: './register.component.html',
})
export class RegisterComponent {
  userData = {
    username: '',
    first_name: '',
    last_name: '',
    email: '',
    password: '',
  };

  loading = signal(false);
  errorMessage = signal('');

  constructor(
    private authService: AuthService,
    private router: Router,
  ) {}

  onRegister() {
    if (!this.userData.username || !this.userData.email || !this.userData.password) return;

    this.loading.set(true);
    this.errorMessage.set('');

    this.authService.register(this.userData).subscribe({
      next: () => {
        // Auto login after registration
        this.authService.login(this.userData.username, this.userData.password).subscribe({
          next: () => {
            this.loading.set(false);
            this.router.navigate(['/']);
          },
          error: () => {
            this.loading.set(false);
            this.router.navigate(['/login']);
          },
        });
      },
      error: (err) => {
        this.loading.set(false);
        this.errorMessage.set(err.error?.detail || 'Registration failed. Please try again.');
      },
    });
  }
}
