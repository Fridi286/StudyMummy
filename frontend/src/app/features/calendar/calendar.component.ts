import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CalendarService, CalendarNote } from '../../core/services/calendar.service';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { TextareaModule } from 'primeng/textarea';
import { MessageService, ConfirmationService } from 'primeng/api';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { CarouselModule } from 'primeng/carousel';

import { DailyLoginService, DailyLoginStatus } from '../../core/services/daily-login.service';
import { SoundService } from '../../core/services/sound.service';
import confetti from 'canvas-confetti';
import { AuthService } from '../../core/auth/auth.service';

interface DayCell {
  date: Date;
  isCurrentMonth: boolean;
  notes: CalendarNote[];
  hasLogin: boolean;
  hasPrevLogin: boolean;
  hasNextLogin: boolean;
}

@Component({
  selector: 'app-calendar',
  standalone: true,
  imports: [
    CommonModule, FormsModule, ButtonModule, DialogModule, 
    InputTextModule, TextareaModule, ConfirmDialogModule, CarouselModule
  ],
  providers: [MessageService, ConfirmationService],
  templateUrl: './calendar.component.html'
})
export class CalendarComponent implements OnInit {
  private calendarService = inject(CalendarService);
  private dailyLoginService = inject(DailyLoginService);
  private soundService = inject(SoundService);
  private authService = inject(AuthService);
  private messageService = inject(MessageService);
  private confirmationService = inject(ConfirmationService);

  currentDate = signal(new Date());
  notes = signal<CalendarNote[]>([]);
  loginHistory = signal<string[]>([]);
  dailyStatus = signal<DailyLoginStatus | null>(null);
  claimingLogin = signal(false);
  loading = signal(true);

  streakColorClass = computed(() => {
    const status = this.dailyStatus();
    if (!status) return 'bg-slate-100 text-slate-600 border-slate-200';
    
    const streak = status.current_streak;
    if (streak < 3) return 'bg-slate-100 text-slate-700 border-slate-200';
    if (streak < 7) return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    if (streak < 14) return 'bg-blue-50 text-blue-700 border-blue-200';
    if (streak < 30) return 'bg-purple-50 text-purple-700 border-purple-200';
    return 'bg-orange-50 text-orange-700 border-orange-200';
  });

  // Carousel & Editing State
  showCarouselDialog = signal(false);
  carouselNotes = signal<CalendarNote[]>([]);
  carouselDate = signal<Date | null>(null);
  carouselEditingNoteId = signal<string | null>(null);
  carouselNoteForm = signal({ title: '', content: '' });

  daysOfWeek = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  calendarGrid = computed(() => {
    const year = this.currentDate().getFullYear();
    const month = this.currentDate().getMonth();
    
    const firstDayOfMonth = new Date(year, month, 1);
    const lastDayOfMonth = new Date(year, month + 1, 0);
    
    const startingDayOfWeek = firstDayOfMonth.getDay();
    const totalDays = lastDayOfMonth.getDate();
    
    const grid: DayCell[] = [];
    
    // Previous month padding
    const prevMonthLastDay = new Date(year, month, 0).getDate();
    for (let i = startingDayOfWeek - 1; i >= 0; i--) {
      const d = new Date(year, month - 1, prevMonthLastDay - i);
      grid.push({ date: d, isCurrentMonth: false, notes: this.getNotesForDate(d), hasLogin: false, hasPrevLogin: false, hasNextLogin: false });
    }
    
    // Current month
    for (let i = 1; i <= totalDays; i++) {
      const d = new Date(year, month, i);
      grid.push({ date: d, isCurrentMonth: true, notes: this.getNotesForDate(d), hasLogin: false, hasPrevLogin: false, hasNextLogin: false });
    }
    
    // Next month padding
    const remainingCells = 42 - grid.length; // 6 rows * 7 days
    for (let i = 1; i <= remainingCells; i++) {
      const d = new Date(year, month + 1, i);
      grid.push({ date: d, isCurrentMonth: false, notes: this.getNotesForDate(d), hasLogin: false, hasPrevLogin: false, hasNextLogin: false });
    }
    
    // Check logins logic
    const historySet = new Set(this.loginHistory());
    
    // Add logic to check prev and next
    const finalGrid = grid.map(cell => {
      const year = cell.date.getFullYear();
      const month = String(cell.date.getMonth() + 1).padStart(2, '0');
      const day = String(cell.date.getDate()).padStart(2, '0');
      const dateStr = `${year}-${month}-${day}`;
      
      const prev = new Date(cell.date);
      prev.setDate(prev.getDate() - 1);
      const pYear = prev.getFullYear();
      const pMonth = String(prev.getMonth() + 1).padStart(2, '0');
      const pDay = String(prev.getDate()).padStart(2, '0');
      
      const next = new Date(cell.date);
      next.setDate(next.getDate() + 1);
      const nYear = next.getFullYear();
      const nMonth = String(next.getMonth() + 1).padStart(2, '0');
      const nDay = String(next.getDate()).padStart(2, '0');
      
      return {
        ...cell,
        hasLogin: historySet.has(dateStr),
        hasPrevLogin: historySet.has(`${pYear}-${pMonth}-${pDay}`),
        hasNextLogin: historySet.has(`${nYear}-${nMonth}-${nDay}`)
      };
    });
    
    return finalGrid;
  });

  ngOnInit() {
    this.loadNotes();
    this.loadHistory();
    this.checkDailyLogin();
  }

  loadHistory() {
    this.dailyLoginService.getHistory().subscribe({
      next: (res) => this.loginHistory.set(res.history),
      error: () => console.error('Failed to load login history')
    });
  }

  checkDailyLogin() {
    this.dailyLoginService.getStatus().subscribe({
      next: (status) => this.dailyStatus.set(status),
      error: () => console.error('Failed to get daily login status')
    });
  }

  claimDailyLogin() {
    if (this.claimingLogin()) return;
    this.claimingLogin.set(true);
    this.dailyLoginService.claimReward().subscribe({
      next: (res) => {
        this.soundService.playWin();
        confetti({
          particleCount: 150,
          spread: 80,
          origin: { y: 0.6 },
          colors: ['#fbbf24', '#f59e0b', '#d97706']
        });
        this.messageService.add({ severity: 'success', summary: 'Daily Reward Claimed!', detail: res.message });
        
        const user = this.authService.currentUser();
        if (user) {
          this.authService.fetchProfile(user.user_id).subscribe();
        }
        
        const currentStatus = this.dailyStatus();
        if (currentStatus) {
          this.dailyStatus.set({
            ...currentStatus,
            can_claim_today: false,
            current_streak: res.current_streak
          });
        }
        
        // Refresh history to update visual streak immediately
        this.loadHistory();
        
        this.claimingLogin.set(false);
      },
      error: (err) => {
        this.claimingLogin.set(false);
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Could not claim daily reward.' });
      }
    });
  }

  loadNotes() {
    this.loading.set(true);
    this.calendarService.getNotes().subscribe({
      next: (data) => {
        this.notes.set(data);
        this.loading.set(false);
      },
      error: () => {
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Could not load notes.' });
        this.loading.set(false);
      }
    });
  }

  getNotesForDate(date: Date): CalendarNote[] {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const dateStr = `${year}-${month}-${day}`;
    return this.notes().filter(n => n.start_time.startsWith(dateStr));
  }

  prevMonth() {
    const d = new Date(this.currentDate());
    d.setMonth(d.getMonth() - 1);
    this.currentDate.set(d);
  }

  nextMonth() {
    const d = new Date(this.currentDate());
    d.setMonth(d.getMonth() + 1);
    this.currentDate.set(d);
  }

  onDayClick(cell: DayCell) {
    this.carouselDate.set(cell.date);
    if (cell.notes.length > 0) {
      this.carouselNotes.set(cell.notes);
      this.carouselEditingNoteId.set(null);
    } else {
      const newNote: CalendarNote = { note_id: 'NEW_NOTE', title: '', content: '', start_time: '', end_time: '', user_id: '', created_at: new Date().toISOString() };
      this.carouselNotes.set([newNote]);
      this.carouselEditingNoteId.set('NEW_NOTE');
      this.carouselNoteForm.set({ title: '', content: '' });
    }
    this.showCarouselDialog.set(true);
  }

  editNoteFromCarousel(note: CalendarNote) {
    this.carouselEditingNoteId.set(note.note_id);
    this.carouselNoteForm.set({ title: note.title, content: note.content });
  }

  cancelEditFromCarousel(note: CalendarNote) {
    if (note.note_id === 'NEW_NOTE') {
      this.carouselNotes.update(notes => notes.filter(n => n.note_id !== 'NEW_NOTE'));
      if (this.carouselNotes().length === 0) {
        this.showCarouselDialog.set(false);
      }
    }
    this.carouselEditingNoteId.set(null);
  }

  saveNoteFromCarousel(note: CalendarNote) {
    if (note.note_id === 'NEW_NOTE') {
      const date = this.carouselDate();
      if (!date) return;
      const start_time = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate())).toISOString();
      const end_time = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate(), 23, 59, 59)).toISOString();

      this.calendarService.createNote({
        title: this.carouselNoteForm().title,
        content: this.carouselNoteForm().content,
        start_time,
        end_time
      }).subscribe({
        next: () => {
          this.messageService.add({ severity: 'success', summary: 'Saved', detail: 'Note created.' });
          this.carouselEditingNoteId.set(null);
          this.calendarService.getNotes().subscribe(data => {
            this.notes.set(data);
            this.carouselNotes.set(this.getNotesForDate(date));
          });
        },
        error: () => this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Creation failed.' })
      });
    } else {
      this.calendarService.updateNote(note.note_id, this.carouselNoteForm()).subscribe({
        next: () => {
          this.messageService.add({ severity: 'success', summary: 'Saved', detail: 'Note updated.' });
          this.carouselEditingNoteId.set(null);
          this.loadNotes();
          this.carouselNotes.update(notes => 
            notes.map(n => n.note_id === note.note_id ? { ...n, title: this.carouselNoteForm().title, content: this.carouselNoteForm().content } : n)
          );
        },
        error: () => this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Update failed.' })
      });
    }
  }

  addNoteFromCarousel() {
    if (this.carouselEditingNoteId() === 'NEW_NOTE') return;
    const newNote: CalendarNote = { note_id: 'NEW_NOTE', title: '', content: '', start_time: '', end_time: '', user_id: '', created_at: new Date().toISOString() };
    this.carouselNotes.update(notes => [newNote, ...notes]);
    this.carouselEditingNoteId.set('NEW_NOTE');
    this.carouselNoteForm.set({ title: '', content: '' });
  }

  deleteNote(event: Event, noteId: string) {
    event.stopPropagation();
    this.confirmationService.confirm({
      target: event.target as EventTarget,
      message: 'Are you sure you want to delete this note?',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.calendarService.deleteNote(noteId).subscribe({
          next: () => {
            this.messageService.add({ severity: 'success', summary: 'Deleted', detail: 'Note removed.' });
            this.loadNotes();
          },
          error: () => this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Deletion failed.' })
        });
      }
    });
  }
}
