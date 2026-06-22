import { Component, effect, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AuthService } from './core/auth/auth.service';
import { HeaderComponent } from './core/layout/header/header.component';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { ChatService } from './core/services/chat.service';
import { MessageService } from 'primeng/api';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, HeaderComponent, ToastModule, ConfirmDialogModule],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  private chatService = inject(ChatService);
  private messageService = inject(MessageService);

  constructor(public authService: AuthService) {
    effect(() => {
      const docId = this.chatService.latestDocumentAnalyzed();
      if (docId) {
        this.messageService.clear(); // Clear the sticky uploading toast
        this.messageService.add({
          severity: 'success',
          summary: 'Analysis Complete',
          detail: 'Your AI learning materials have been generated successfully!',
        });
        
        // Clear the signal after a tiny delay to ensure other components like learn.ts can process the docId first
        setTimeout(() => {
          this.chatService.latestDocumentAnalyzed.set(null);
        }, 100);
      }
    });
  }
}
