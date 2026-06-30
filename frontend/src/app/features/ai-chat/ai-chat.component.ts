import { Component, inject, signal, ViewChild, ElementRef, OnInit, input, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AgentService, ChatMessage, SessionInfo } from '../../core/services/agent.service';
import { AuthService } from '../../core/auth/auth.service';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { AvatarModule } from 'primeng/avatar';
import { ConfirmationService, MessageService } from 'primeng/api';

@Component({
  selector: 'app-ai-chat',
  standalone: true,
  imports: [CommonModule, FormsModule, ButtonModule, InputTextModule, AvatarModule],
  templateUrl: './ai-chat.component.html',
})
export class AiChatComponent implements OnInit {
  agentService = inject(AgentService);
  authService = inject(AuthService);
  confirmationService = inject(ConfirmationService);
  messageService = inject(MessageService);

  @ViewChild('scrollContainer') private scrollContainer!: ElementRef;

  messages = signal<ChatMessage[]>([]);
  sessions = signal<SessionInfo[]>([]);
  messageInput = '';
  isLoading = signal(false);
  sessionId = '';
  activeSessionId = signal('');
  showSessions = input<boolean>(true);
  showHeader = input<boolean>(true);
  extraContext = input<string>('');
  activeTaskId = input<string | undefined>();
  closeChat = output<void>();

  ngOnInit() {
    this.loadSessions();
    this.startNewSession();
  }

  loadSessions() {
    this.agentService.listSessions().subscribe(s => this.sessions.set(s));
  }

  startNewSession() {
    const userId = this.authService.currentUser()?.user_id ?? 'anonymous';
    this.sessionId = `${userId}-${Date.now()}`;
    this.activeSessionId.set(this.sessionId);
    this.messages.set([{
      role: 'assistant',
      content: "👋 Hello! I'm StudyMummy AI, your personal Socratic tutor. Ask me anything!",
      timestamp: new Date(),
    }]);
  }

  loadSession(session: SessionInfo) {
    this.sessionId = session.session_id;
    this.activeSessionId.set(session.session_id);
    this.isLoading.set(true);

    this.agentService.getSessionMessages(session.session_id).subscribe(msgs => {
      this.messages.set(msgs.map(m => ({ ...m, timestamp: new Date(m.timestamp) })));
      this.isLoading.set(false);
      this.scrollToBottom();
    });
  }

  deleteSession(event: Event, session: SessionInfo) {
    event.stopPropagation(); // prevent triggering loadSession
    this.confirmationService.confirm({
      message: 'Are you sure you want to delete this chat session? This will permanently remove the conversation history.',
      header: 'Delete Chat Session',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.agentService.deleteSession(session.session_id).subscribe({
          next: () => {
            this.messageService.add({
              severity: 'success',
              summary: 'Deleted',
              detail: 'Chat session deleted successfully.'
            });
            // If we deleted the active session, start fresh
            if (this.activeSessionId() === session.session_id) {
              this.startNewSession();
            }
            this.loadSessions();
          },
          error: (err) => {
            this.messageService.add({
              severity: 'error',
              summary: 'Error',
              detail: err.error?.detail || 'Failed to delete session'
            });
          }
        });
      }
    });
  }

  sendMessage() {
    const text = this.messageInput.trim();
    if (!text || this.isLoading()) return;

    this.messages.update(msgs => [...msgs, {
      role: 'user',
      content: text,
      timestamp: new Date(),
    }]);
    this.messageInput = '';
    this.isLoading.set(true);
    this.scrollToBottom();

    this.agentService.chat(this.sessionId, text, {
      extraContext: this.extraContext(),
      taskId: this.activeTaskId(),
    }).subscribe({
      next: (res) => {
        this.messages.update(msgs => [...msgs, {
          role: 'assistant',
          content: res.message,
          timestamp: new Date(),
        }]);
        this.isLoading.set(false);
        this.scrollToBottom();
        this.loadSessions(); // Refresh sidebar
      },
      error: () => {
        this.messages.update(msgs => [...msgs, {
          role: 'assistant',
          content: "⚠️ Something went wrong. Please try again.",
          timestamp: new Date(),
        }]);
        this.isLoading.set(false);
        this.scrollToBottom();
      }
    });
  }

  onKeydown(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  formatDate(dateStr: string): string {
    const d = new Date(dateStr);
    const now = new Date();
    const diffDays = Math.floor((now.getTime() - d.getTime()) / 86400000);
    if (diffDays === 0) return 'Today ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    if (diffDays === 1) return 'Yesterday';
    return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
  }

  private scrollToBottom() {
    setTimeout(() => {
      if (this.scrollContainer) {
        try {
          this.scrollContainer.nativeElement.scrollTop = this.scrollContainer.nativeElement.scrollHeight;
        } catch (e) {}
      }
    }, 50);
  }
}
