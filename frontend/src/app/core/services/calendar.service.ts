import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface CalendarNote {
  note_id: string;
  user_id: string;
  title: string;
  content: string;
  start_time: string;
  end_time: string;
  created_at: string;
}

export interface CalendarNoteCreate {
  title: string;
  content: string;
  start_time: string;
  end_time: string;
}

@Injectable({
  providedIn: 'root'
})
export class CalendarService {
  private http = inject(HttpClient);
  private apiUrl = 'http://localhost:8000/api/v1/calendar';

  getNotes(): Observable<CalendarNote[]> {
    return this.http.get<CalendarNote[]>(`${this.apiUrl}/`);
  }

  createNote(note: CalendarNoteCreate): Observable<CalendarNote> {
    return this.http.post<CalendarNote>(`${this.apiUrl}/`, note);
  }

  updateNote(noteId: string, note: Partial<CalendarNoteCreate>): Observable<CalendarNote> {
    return this.http.put<CalendarNote>(`${this.apiUrl}/${noteId}`, note);
  }

  deleteNote(noteId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${noteId}`);
  }
}
