import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_V1 } from '../config/api.config';

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
  document_id?: string;
}

export interface ChatResponse {
  session_id: string;
  message: string;
  action_taken?: string;
  tool_calls?: string[];
  trace_id?: string;
  decision: AgentDecision;
  agent_trace: AgentTraceStep[];
  agents_involved: string[];
  reviewed: boolean;
}

export interface AgentDecision {
  intent: string;
  action: string;
  objective: string;
  decision_basis: string;
  tool_names: string[];
  success_criteria: string[];
}

export interface AgentTraceStep {
  agent: 'perception' | 'planner' | 'tutor' | 'reviewer' | 'memory';
  phase: 'perceive' | 'plan' | 'act' | 'review' | 'remember';
  summary: string;
  duration_ms: number;
}

export interface SessionInfo {
  session_id: string;
  created_at: string;
  active: boolean;
}

export interface ChatContextOptions {
  extraContext?: string;
  taskId?: string;
  documentId?: string;
}

@Injectable({ providedIn: 'root' })
export class AgentService {
  private http = inject(HttpClient);
  private apiUrl = `${API_V1}/agent`;

  chat(sessionId: string, message: string, options: ChatContextOptions = {}): Observable<ChatResponse> {
    const request: ChatRequest = {
      session_id: sessionId,
      message,
      extra_context: options.extraContext || undefined,
      task_id: options.taskId || undefined,
      document_id: options.documentId || undefined,
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
