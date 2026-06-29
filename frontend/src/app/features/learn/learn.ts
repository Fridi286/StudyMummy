import { Component, signal, effect, inject, OnInit, HostListener, viewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MessageService, ConfirmationService } from 'primeng/api';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { MenuModule } from 'primeng/menu';
import { MenuItem } from 'primeng/api';
import { ChatService } from '../../core/services/chat.service';
import { DocumentsService, TaskResponse, QuizResponse, CheatsheetResponse, DocumentResponse, QuizAttemptResponse } from '../../core/services/documents.service';
import { SoundService } from '../../core/services/sound.service';
import { finalize } from 'rxjs/operators';
import confetti from 'canvas-confetti';

import { EditTagsDialog } from '../../shared/components/edit-tags-dialog/edit-tags-dialog';

import { AiChatComponent } from '../ai-chat/ai-chat.component';

import { StudySidebar } from './components/study-sidebar/study-sidebar';
import { QuizTab } from './components/quiz-tab/quiz-tab';
import { TasksTab } from './components/tasks-tab/tasks-tab';
import { CheatsheetsTab } from './components/cheatsheets-tab/cheatsheets-tab';

@Component({
  selector: 'app-learn',
  standalone: true,
  imports: [CommonModule, ToastModule, ConfirmDialogModule, MenuModule, EditTagsDialog, StudySidebar, QuizTab, TasksTab, CheatsheetsTab, AiChatComponent],
  templateUrl: './learn.html',
  styleUrl: './learn.css',
  providers: [ConfirmationService]
})
export class Learn implements OnInit {
  private chatService = inject(ChatService);
  private documentsService = inject(DocumentsService);
  private messageService = inject(MessageService);
  private confirmationService = inject(ConfirmationService);
  private soundService = inject(SoundService);

  activeTab = signal<'quiz' | 'tasks' | 'cheatsheets'>('quiz');

  // Document History
  documents = signal<DocumentResponse[]>([]);
  activeDocument = signal<DocumentResponse | null>(null);
  isLibraryExpanded = signal<boolean>(true);

  // AI Chat Split View State
  isChatExpanded = signal<boolean>(false);
  chatPanelWidth = signal<number>(400);
  isResizing = signal<boolean>(false);
  chatMenuItems = signal<MenuItem[]>([]);
  aiChat = viewChild<AiChatComponent>('aiChat');
  private dragStartX = 0;
  private dragStartWidth = 0;

  // Library Split View State
  libraryPanelWidth = signal<number>(320);
  isLibraryResizing = signal<boolean>(false);
  private libDragStartX = 0;
  private libDragStartWidth = 0;

  // AI Pipeline State
  isAnalyzing = signal<boolean>(false);
  generatedTasks = signal<TaskResponse[]>([]);
  generatedQuizzes = signal<QuizResponse[]>([]);
  generatedCheatsheets = signal<CheatsheetResponse[]>([]);

  // Interactive Quiz State
  selectedAnswers = signal<Record<string, Record<string, string>>>({}); // quizId -> (questionId -> option)
  quizAttempts = signal<Record<string, QuizAttemptResponse[]>>({}); // quizId -> attempts
  isSubmittingQuiz = signal<Record<string, boolean>>({});

  isEditTagsDialogVisible = signal<boolean>(false);
  selectedDocToEdit = signal<DocumentResponse | null>(null);

  constructor() {
    // Listen for WebSocket notification that the document has finished analyzing
    effect(() => {
      const docId = this.chatService.latestDocumentAnalyzed();
      if (docId) {
        this.isAnalyzing.set(false);

        // Refresh documents to show the new one, and select it
        this.fetchDocuments(docId);
      }
    }, { allowSignalWrites: true });

    effect(() => {
      const chat = this.aiChat();
      if (chat) {
        const sessions = chat.sessions();
        const items = sessions.map(s => ({
          label: chat.formatDate(s.created_at),
          icon: 'pi pi-comments',
          command: () => chat.loadSession(s)
        }));
        
        if (items.length === 0) {
          this.chatMenuItems.set([{ label: 'No recent chats', disabled: true }]);
        } else {
          this.chatMenuItems.set(items);
        }
      }
    }, { allowSignalWrites: true });
  }

  // --- Resizable Split-View Logic ---
  onResizeStart(event: MouseEvent) {
    event.preventDefault(); // Prevent text selection
    this.isResizing.set(true);
    this.dragStartX = event.clientX;
    this.dragStartWidth = this.chatPanelWidth();
  }

  onLibResizeStart(event: MouseEvent) {
    event.preventDefault();
    this.isLibraryResizing.set(true);
    this.libDragStartX = event.clientX;
    this.libDragStartWidth = this.libraryPanelWidth();
  }

  @HostListener('document:mousemove', ['$event'])
  onResizeDrag(event: MouseEvent) {
    // Calculate dynamic container constraints
    const containerWidth = Math.min(window.innerWidth, 1400);
    const gapSpace = (this.isLibraryExpanded() ? 32 : 0) + (this.isChatExpanded() ? 32 : 0);
    const minCenterWidth = 400; // Guarantee at least 400px for central study content

    if (this.isResizing()) {
      const deltaX = this.dragStartX - event.clientX;
      const newWidth = this.dragStartWidth + deltaX;
      
      const maxAvailableWidth = containerWidth - gapSpace - minCenterWidth - (this.isLibraryExpanded() ? this.libraryPanelWidth() : 0);
      const actualMax = Math.min(800, Math.max(300, maxAvailableWidth));

      if (newWidth >= 300 && newWidth <= actualMax) {
        this.chatPanelWidth.set(newWidth);
      } else if (newWidth > actualMax) {
        this.chatPanelWidth.set(actualMax);
      } else if (newWidth < 300) {
        this.chatPanelWidth.set(300);
      }
    } else if (this.isLibraryResizing()) {
      const deltaX = event.clientX - this.libDragStartX;
      const newWidth = this.libDragStartWidth + deltaX;
      
      const maxAvailableWidth = containerWidth - gapSpace - minCenterWidth - (this.isChatExpanded() ? this.chatPanelWidth() : 0);
      const actualMax = Math.min(600, Math.max(250, maxAvailableWidth));
      
      if (newWidth >= 250 && newWidth <= actualMax) {
        this.libraryPanelWidth.set(newWidth);
      } else if (newWidth > actualMax) {
        this.libraryPanelWidth.set(actualMax);
      } else if (newWidth < 250) {
        this.libraryPanelWidth.set(250);
      }
    }
  }

  @HostListener('document:mouseup')
  onResizeEnd() {
    if (this.isResizing()) {
      this.isResizing.set(false);
    }
    if (this.isLibraryResizing()) {
      this.isLibraryResizing.set(false);
    }
  }

  ngOnInit() {
    this.fetchDocuments();
  }

  fetchDocuments(selectDocId?: string) {
    this.documentsService.getDocuments().subscribe(docs => {
      this.documents.set(docs);
      if (docs.length > 0) {
        if (selectDocId) {
          const toSelect = docs.find(d => d.document_id === selectDocId);
          if (toSelect) this.selectDocument(toSelect);
        } else if (!this.activeDocument()) {
          // Select the first (most recent) document
          this.selectDocument(docs[0]);
        }
      }
    });
  }

  selectDocument(doc: DocumentResponse) {
    this.activeDocument.set(doc);
    this.fetchGeneratedArtifacts(doc.document_id);
  }

  setTab(tab: 'quiz' | 'tasks' | 'cheatsheets') {
    this.activeTab.set(tab);
  }

  onFileUpload(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      const file = input.files[0];

      this.isAnalyzing.set(true);
      this.messageService.add({
        severity: 'info',
        summary: 'Uploading...',
        detail: 'Uploading and analyzing your document. This may take a minute...',
        sticky: true
      });

      this.documentsService.uploadDocument(file).subscribe({
        next: (doc) => {
          // Document uploaded successfully, the backend background task is now running.
          // We wait for the WebSocket event to trigger `fetchGeneratedArtifacts`.
        },
        error: (err) => {
          this.isAnalyzing.set(false);
          this.messageService.add({
            severity: 'error',
            summary: 'Upload Failed',
            detail: err.error?.detail || 'Failed to upload document.',
          });
        }
      });

      // Clear the input value so the same file can be selected again if needed
      input.value = '';
    }
  }

  private fetchGeneratedArtifacts(documentId: string) {
    this.documentsService.getDocumentTasks(documentId).subscribe(tasks => {
      // Sort tasks: open first, completed last
      const sorted = [...tasks].sort((a, b) => {
        if (a.status === 'completed' && b.status !== 'completed') return 1;
        if (a.status !== 'completed' && b.status === 'completed') return -1;
        return 0;
      });
      this.generatedTasks.set(sorted);
    });

    this.documentsService.getDocumentQuizzes(documentId).subscribe(quizzes => {
      this.generatedQuizzes.set(quizzes);

      // Fetch past attempts for each quiz
      quizzes.forEach(quiz => {
        this.documentsService.getQuizAttempts(quiz.quiz_id).subscribe(attempts => {
          this.quizAttempts.update(prev => ({
            ...prev,
            [quiz.quiz_id]: attempts
          }));

          // Clear selected answers when loading new attempts to start fresh
          this.selectedAnswers.update(prev => {
            const newAnswers = { ...prev };
            newAnswers[quiz.quiz_id] = {};
            return newAnswers;
          });
        });
      });
    });

    this.documentsService.getDocumentCheatsheets(documentId).subscribe(cheatsheets => {
      this.generatedCheatsheets.set(cheatsheets);
    });
  }

  // --- Task Logic ---
  toggleTaskCompletion(task: TaskResponse) {
    const newStatus = task.status === 'completed' ? 'open' : 'completed';
    // Optimistically update
    this.generatedTasks.update(tasks => tasks.map(t => t.task_id === task.task_id ? { ...t, status: newStatus } : t));

    this.documentsService.updateTaskStatus(task.task_id, newStatus).subscribe({
      next: (updatedTask) => {
        // Only fire confetti if completing the task
        if (newStatus === 'completed') {
          this.fireConfetti('good');
        }
        // Update the task with backend state (which includes is_rewarded if applicable)
        this.generatedTasks.update(tasks => tasks.map(t => t.task_id === task.task_id ? updatedTask : t));
      },
      error: () => {
        // Revert on error
        this.generatedTasks.update(tasks => tasks.map(t => t.task_id === task.task_id ? { ...t, status: task.status } : t));
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to update task status' });
      }
    });
  }

  // --- Quiz Logic ---
  selectAnswer(quizId: string, questionId: string, option: string) {
    // If the latest attempt is completed, we don't let them select answers unless they reset
    const attempts = this.quizAttempts()[quizId] || [];
    if (attempts.length > 0) {
      // For now, if there is an attempt, we can assume they are viewing results.
      // But wait, what if they clicked "Retake"? If they clicked retake, we'd clear attempts temporarily or clear selected answers.
      // We will handle this in UI: if attempts exist, show results. If they click "Retake", we set a flag.
      // Let's just track an isRetaking state if needed. But for simplicity, we can let them select if they want.
    }

    this.selectedAnswers.update(prev => {
      const quizAns = prev[quizId] || {};
      return {
        ...prev,
        [quizId]: { ...quizAns, [questionId]: option }
      };
    });
  }

  submitQuiz(quiz: QuizResponse) {
    const answers = this.selectedAnswers()[quiz.quiz_id] || {};
    if (Object.keys(answers).length < quiz.questions.length) {
      this.messageService.add({ severity: 'warn', summary: 'Incomplete', detail: 'Please answer all questions before submitting.' });
      return;
    }

    this.isSubmittingQuiz.update(prev => ({ ...prev, [quiz.quiz_id]: true }));

    this.documentsService.submitQuizAttempt(quiz.quiz_id, answers)
      .pipe(finalize(() => this.isSubmittingQuiz.update(prev => ({ ...prev, [quiz.quiz_id]: false }))))
      .subscribe({
        next: (attempt) => {
          this.messageService.add({ severity: 'success', summary: 'Quiz Submitted', detail: `You scored ${attempt.score} out of ${attempt.total_questions}!` });

          this.quizAttempts.update(prev => {
            const existing = prev[quiz.quiz_id] || [];
            return {
              ...prev,
              [quiz.quiz_id]: [attempt, ...existing]
            };
          });
          
          let performance: 'perfect' | 'good' | 'bad' = 'bad';
          if (attempt.score === attempt.total_questions) {
            performance = 'perfect';
          } else if (attempt.score >= attempt.total_questions / 2) {
            performance = 'good';
          }
          
          this.fireConfetti(performance);
        },
        error: () => {
          this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to submit quiz' });
        }
      });
  }

  retakeQuiz(quizId: string) {
    // Clear the selected answers for this quiz
    this.selectedAnswers.update(prev => {
      const newAnswers = { ...prev };
      newAnswers[quizId] = {};
      return newAnswers;
    });
    // And optionally clear the local attempts so it switches back to input mode.
    // Let's just hide the attempt UI by creating a special retaking state.
    // Or simpler: We just let `quizAttempts` stay, but use `selectedAnswers` emptiness to determine if they are retaking.
    // Actually, it's easier to just temporarily clear `quizAttempts` local array for this quiz.
    this.quizAttempts.update(prev => {
      const newAttempts = { ...prev };
      newAttempts[quizId] = [];
      return newAttempts;
    });
  }

  // --- Document Menu & Deletion ---

  downloadDocument(doc: DocumentResponse) {
    this.documentsService.downloadDocument(doc.document_id, doc.file_name);
  }

  deleteDocument(event: Event, doc: DocumentResponse) {
    event.stopPropagation();

    this.confirmationService.confirm({
      target: event.target as EventTarget,
      message: `Are you sure you want to delete "${doc.file_name}"? All associated Tasks, Quizzes, and Cheatsheets will be permanently removed.`,
      header: 'Confirm Deletion',
      icon: 'pi pi-exclamation-triangle',
      acceptButtonStyleClass: 'p-button-danger',
      rejectButtonStyleClass: 'p-button-text',
      accept: () => {
        this.documentsService.deleteDocument(doc.document_id).subscribe({
          next: () => {
            this.messageService.add({ severity: 'success', summary: 'Deleted', detail: 'Document deleted successfully' });
            this.documents.update(docs => docs.filter(d => d.document_id !== doc.document_id));

            if (this.activeDocument()?.document_id === doc.document_id) {
              const remaining = this.documents();
              if (remaining.length > 0) {
                this.selectDocument(remaining[0]);
              } else {
                this.activeDocument.set(null);
                this.generatedTasks.set([]);
                this.generatedQuizzes.set([]);
                this.generatedCheatsheets.set([]);
              }
            }
          },
          error: () => {
            this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to delete document' });
          }
        });
      }
    });
  }

  openEditTags(doc: DocumentResponse) {
    this.selectedDocToEdit.set(doc);
    this.isEditTagsDialogVisible.set(true);
  }

  private fireConfetti(performance: 'perfect' | 'good' | 'bad') {
    if (performance === 'perfect') {
      this.soundService.playJackpot();
      const duration = 3000;
      const end = Date.now() + duration;

      const frame = () => {
        confetti({
          particleCount: 5,
          angle: 60,
          spread: 55,
          origin: { x: 0 },
          colors: ['#4f46e5', '#7c3aed', '#fbbf24']
        });
        confetti({
          particleCount: 5,
          angle: 120,
          spread: 55,
          origin: { x: 1 },
          colors: ['#4f46e5', '#7c3aed', '#fbbf24']
        });

        if (Date.now() < end) {
          requestAnimationFrame(frame);
        }
      };
      frame();
    } else if (performance === 'good') {
      this.soundService.playWin();
      confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.6 },
        colors: ['#4f46e5', '#7c3aed', '#fbbf24']
      });
    } else {
      this.soundService.playLoss();
    }
  }
}
