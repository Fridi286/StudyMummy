import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface ChatRequest {
  session_id: string;
  message: string;
  extra_context?: string;
  task_id?: string;
}

export interface ChatResponse {
  session_id: string;
  message: string;
  action_taken?: string;
  tool_calls?: string[];
  trace_id?: string;
}

export interface SessionInfo {
  session_id: string;
  created_at: string;
  active: boolean;
}

export interface ChatContextOptions {
  extraContext?: string;
  taskId?: string;
}

@Injectable({ providedIn: 'root' })
export class AgentService {
  private http = inject(HttpClient);
  private apiUrl = 'http://localhost:8000/api/v1/agent';

  chat(sessionId: string, message: string, options: ChatContextOptions = {}): Observable<ChatResponse> {
    const request: ChatRequest = {
      session_id: sessionId,
      message,
      extra_context: options.extraContext || undefined,
      task_id: options.taskId || undefined,
    };

    return this.http.post<ChatResponse>(`${this.apiUrl}/chat`, request);
  }

  listSessions(): Observable<SessionInfo[]> {
    return this.http.get<SessionInfo[]>(`${this.apiUrl}/sessions`);
  }

  getSessionMessages(sessionId: string): Observable<ChatMessage[]> {
    return this.http.get<ChatMessage[]>(`${this.apiUrl}/sessions/${sessionId}/messages`);
  }

  deleteSession(sessionId: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/sessions/${sessionId}`);
  }
}
