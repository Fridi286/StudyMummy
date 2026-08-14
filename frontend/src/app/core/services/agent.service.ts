import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_V1 } from '../config/api.config';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  masRun?: MasRunSummary;
}

export interface MasRunSummary {
  agents: string[];
  coordinationRounds: number;
  reviewed: boolean;
  messageKinds: string[];
  toolOutcomes: string[];
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
  tool_observations: ToolObservation[];
  trace_id?: string;
  decision: AgentDecision;
  agent_trace: AgentTraceStep[];
  communications: AgentCommunication[];
  agent_states: AgentLocalState[];
  agents_involved: string[];
  coordination_rounds: number;
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
  agent: 'environment' | 'planner' | 'tutor' | 'reviewer' | 'coordinator' | 'memory';
  phase: 'perceive' | 'plan' | 'replan' | 'act' | 'revise' | 'review' | 'coordinate' | 'remember';
  summary: string;
  duration_ms: number;
  round: number;
  message_id?: string;
}

export interface ToolObservation {
  tool_name: string;
  status: 'succeeded' | 'failed' | 'blocked' | 'invalid_arguments';
  result_preview: string;
}

export interface AgentCommunication {
  message_id: string;
  sender: 'user' | 'planner' | 'tutor' | 'reviewer' | 'coordinator';
  recipient: 'user' | 'planner' | 'tutor' | 'reviewer' | 'coordinator';
  performative: 'request' | 'delegate' | 'propose' | 'critique' | 'accept' | 'inform';
  kind: 'plan_request' | 'execute_plan' | 'review_request' | 'revision_request' | 'replan_request' | 'final_response';
  round: number;
  summary: string;
}

export interface AgentLocalState {
  agent: 'planner' | 'tutor' | 'reviewer';
  objective: string;
  capabilities: string[];
  messages_received: number;
  messages_sent: number;
  decisions_made: number;
  last_message_kind?: string;
  last_decision: string;
  local_memory: Record<string, string>;
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
