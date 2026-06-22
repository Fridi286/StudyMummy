import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface DocumentResponse {
  document_id: string;
  user_id: string;
  file_name: string;
  storage_path: string;
  tags: string[];
  uploaded_at: string;
}

export interface TaskResponse {
  task_id: string;
  document_id: string;
  difficulty: number;
  task_text: string;
  key_concepts: string[];
  status: string;
  created_at: string;
}

export interface QuizQuestionResponse {
  question_id: string;
  quiz_id: string;
  question_text: string;
  options: string[];
  correct_answer: string;
  explanation: string;
  key_concepts: string[];
}

export interface QuizResponse {
  quiz_id: string;
  document_id: string;
  title: string;
  created_at: string;
  questions: QuizQuestionResponse[];
}

export interface CheatsheetResponse {
  cheatsheet_id: string;
  document_id: string;
  title: string;
  content: string;
  key_concepts: string[];
  created_at: string;
}

export interface TaskStatusUpdate {
  status: string;
}

export interface QuizAttemptRequest {
  answers: Record<string, string>;
}

export interface QuizAttemptResponse {
  attempt_id: string;
  quiz_id: string;
  score: number;
  total_questions: number;
  answers: Record<string, string>;
  created_at: string;
}

@Injectable({
  providedIn: 'root'
})
export class DocumentsService {
  private http = inject(HttpClient);
  private apiUrl = 'http://localhost:8000/api/v1/documents';

  getDocuments(): Observable<DocumentResponse[]> {
    return this.http.get<DocumentResponse[]>(`${this.apiUrl}/`);
  }

  uploadDocument(file: File, tags: string[] = []): Observable<DocumentResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (tags.length > 0) {
      formData.append('tags_string', tags.join(','));
    }
    return this.http.post<DocumentResponse>(`${this.apiUrl}/`, formData);
  }

  downloadDocument(documentId: string, fileName: string): void {
    this.http.get(`${this.apiUrl}/${documentId}/download`, { responseType: 'blob' }).subscribe(blob => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    });
  }

  deleteDocument(documentId: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/${documentId}`);
  }

  updateDocumentTags(documentId: string, tags: string[]): Observable<DocumentResponse> {
    return this.http.put<DocumentResponse>(`${this.apiUrl}/${documentId}/tags`, { tags });
  }

  getDocumentTasks(documentId: string): Observable<TaskResponse[]> {
    return this.http.get<TaskResponse[]>(`${this.apiUrl}/${documentId}/tasks`);
  }

  getDocumentQuizzes(documentId: string): Observable<QuizResponse[]> {
    return this.http.get<QuizResponse[]>(`${this.apiUrl}/${documentId}/quizzes`);
  }

  getDocumentCheatsheets(documentId: string): Observable<CheatsheetResponse[]> {
    return this.http.get<CheatsheetResponse[]>(`${this.apiUrl}/${documentId}/cheatsheets`);
  }

  updateTaskStatus(taskId: string, status: string): Observable<TaskResponse> {
    return this.http.put<TaskResponse>(`${this.apiUrl}/tasks/${taskId}/status`, { status });
  }

  submitQuizAttempt(quizId: string, answers: Record<string, string>): Observable<QuizAttemptResponse> {
    return this.http.post<QuizAttemptResponse>(`${this.apiUrl}/quizzes/${quizId}/attempts`, { answers });
  }

  getQuizAttempts(quizId: string): Observable<QuizAttemptResponse[]> {
    return this.http.get<QuizAttemptResponse[]>(`${this.apiUrl}/quizzes/${quizId}/attempts`);
  }
}
