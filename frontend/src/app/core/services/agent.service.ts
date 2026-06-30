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

@Injectable({ providedIn: 'root' })
export class AgentService {
  private http = inject(HttpClient);
  private apiUrl = 'http://localhost:8000/api/v1/agent';

  chat(sessionId: string, message: string, taskId?: string): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(`${this.apiUrl}/chat`, {
      session_id: sessionId,
      message,
      task_id: taskId
    });
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
