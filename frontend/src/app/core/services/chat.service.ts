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

  // Presence mapping: user_id -> 'online' | 'away' | 'offline'
  public userPresence = signal<Record<string, string>>({});

  // A signal to hold the latest incoming message
  public latestMessage = signal<ChatMessageResponse | null>(null);

  // A signal to hold the latest notification (e.g. FRIEND_REQUEST)
  public latestNotification = signal<any | null>(null);

  // A signal to trigger trade refreshes
  public latestTradeUpdate = signal<number>(0);

  // A signal to notify when a document finishes analyzing
  public latestDocumentAnalyzed = signal<string | null>(null);

  // A signal to hold the latest reward gained event
  public latestReward = signal<any | null>(null);

  // A signal to notify when background document analysis fails
  public latestDocumentAnalysisFailed = signal<{ documentId: string | null; message: string } | null>(null);

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
        const data = JSON.parse(event.data);
        if (data.type === 'CHAT_MESSAGE' && data.message) {
          this.latestMessage.set(data.message);
        } else if (data.type === 'FRIEND_REQUEST' || data.type === 'FRIEND_ACCEPTED') {
          this.latestNotification.set(data);
        } else if (data.type === 'TRADE_UPDATE') {
          this.latestTradeUpdate.update(v => v + 1);
        } else if (data.type === 'DOCUMENT_ANALYZED') {
          this.latestDocumentAnalyzed.set(data.message);
        } else if (data.type === 'DOCUMENT_ANALYSIS_FAILED') {
          this.latestDocumentAnalysisFailed.set({
            documentId: data.document_id ?? null,
            message: data.message || 'Document analysis failed.'
          });
        } else if (data.type === 'REWARD_GAINED') {
          this.latestReward.set(data);
        } else if (data.type === 'PRESENCE_STATE') {
          this.userPresence.set(data.message || {});
        } else if (data.type === 'PRESENCE_UPDATE') {
          this.userPresence.update(prev => ({
            ...prev,
            [data.user_id]: data.message
          }));
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

  public setStatus(status: 'online' | 'away') {
    if (this.ws && this.connected()) {
      this.ws.send(JSON.stringify({
        type: 'PRESENCE_SET',
        status: status
      }));
    }
  }
}
