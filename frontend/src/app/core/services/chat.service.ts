import { Injectable, inject, signal, effect } from '@angular/core';
import { AuthService } from '../auth/auth.service';
import { ChatMessageResponse } from './social.service';

export interface WebSocketMessage {
  type: string;
  from_user_id?: string;
  from_username?: string;
  user_id?: string;
  username?: string;
  session_id?: string;
  message?: ChatMessageResponse;
}

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private authService = inject(AuthService);
  private ws: WebSocket | null = null;

  public connected = signal<boolean>(false);
  
  // A signal to hold the latest incoming message
  public latestMessage = signal<ChatMessageResponse | null>(null);
  
  // A signal to hold the latest notification (e.g. FRIEND_REQUEST)
  public latestNotification = signal<any | null>(null);

  constructor() {
    effect(() => {
      const user = this.authService.currentUser();
      if (user) {
        // Run connect outside of reactive context to avoid infinite loops if signals change
        setTimeout(() => this.connect(), 0);
      } else {
        this.disconnect();
      }
    });
  }

  private connect() {
    if (this.ws) return;
    
    const token = localStorage.getItem('access_token');
    if (!token) return;

    // Determine ws protocol based on current origin
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Assume backend is on port 8000 for local dev if frontend is 4200, otherwise relative
    const host = window.location.port === '4200' ? 'localhost:8000' : window.location.host;
    
    const wsUrl = `${protocol}//${host}/api/v1/chat?token=${token}`;
    
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      this.connected.set(true);
    };

    this.ws.onmessage = (event) => {
      try {
        const data: WebSocketMessage = JSON.parse(event.data);
        if (data.type === 'CHAT_MESSAGE' && data.message) {
          this.latestMessage.set(data.message);
        } else if (data.type === 'FRIEND_REQUEST' || data.type === 'FRIEND_ACCEPTED') {
          this.latestNotification.set(data);
        }
      } catch (e) {
        console.error('Failed to parse WebSocket message', e);
      }
    };

    this.ws.onclose = () => {
      this.connected.set(false);
      this.ws = null;
      // Auto reconnect after 5 seconds
      setTimeout(() => this.connect(), 5000);
    };
  }

  private disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
      this.connected.set(false);
    }
  }

  public sendMessage(roomId: string, content: string) {
    if (this.ws && this.connected()) {
      this.ws.send(JSON.stringify({
        type: 'CHAT_MESSAGE',
        room_id: roomId,
        content: content
      }));
    } else {
      console.error('WebSocket is not connected');
    }
  }
}
