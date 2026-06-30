import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import confetti from 'canvas-confetti';
import { MessageService } from 'primeng/api';

import {
  DocumentResponse,
  DocumentsService,
  PracticeAnswerResponse,
  PracticeTaskResponse,
} from '../../core/services/documents.service';
import { SoundService } from '../../core/services/sound.service';
import { AiChatComponent } from '../ai-chat/ai-chat.component';

@Component({
  selector: 'app-practice',
  standalone: true,
  imports: [CommonModule, FormsModule, AiChatComponent],
  templateUrl: './practice.component.html',
  styleUrl: './practice.component.css',
})
export class PracticeComponent implements OnInit {
  private documentsService = inject(DocumentsService);
  private messageService = inject(MessageService);
  private soundService = inject(SoundService);

  documents = signal<DocumentResponse[]>([]);
  isLoadingDocuments = signal<boolean>(true);
  textFilter = signal<string>('');
  selectedTagFilters = signal<string[]>([]);
  selectedDocumentIds = signal<string[]>([]);
  difficulty = signal<number>(3);

  hasStarted = signal<boolean>(false);
  currentTask = signal<PracticeTaskResponse | null>(null);
  answer = signal<string>('');
  feedback = signal<PracticeAnswerResponse | null>(null);
  isGenerating = signal<boolean>(false);
  isSubmitting = signal<boolean>(false);

  availableTags = computed(() => {
    const tags = new Set<string>();
    this.documents().forEach(doc => {
      (doc.tags || []).forEach(tag => {
        const clean = tag.trim();
        if (clean) tags.add(clean);
      });
    });
    return Array.from(tags).sort((a, b) => a.localeCompare(b));
  });

  filteredDocuments = computed(() => {
    const query = this.textFilter().trim().toLowerCase();
    const activeTags = this.selectedTagFilters();

    return this.documents().filter(doc => {
      const docTags = doc.tags || [];
      const matchesTags = activeTags.length === 0 || activeTags.every(tag => docTags.includes(tag));
      const haystack = `${doc.file_name} ${docTags.join(' ')}`.toLowerCase();
      const matchesText = !query || haystack.includes(query);
      return matchesTags && matchesText;
    });
  });

  selectedDocuments = computed(() => {
    const selected = new Set(this.selectedDocumentIds());
    return this.documents().filter(doc => selected.has(doc.document_id));
  });

  selectedFilteredCount = computed(() => {
    const selected = new Set(this.selectedDocumentIds());
    return this.filteredDocuments().filter(doc => selected.has(doc.document_id)).length;
  });

  allFilteredSelected = computed(() => {
    const filtered = this.filteredDocuments();
    return filtered.length > 0 && filtered.every(doc => this.selectedDocumentIds().includes(doc.document_id));
  });

  canSubmit = computed(() => {
    const task = this.currentTask();
    const alreadySolved = this.feedback()?.correct === true;
    return !!task && !alreadySolved && this.answer().trim().length > 0 && !this.isSubmitting();
  });

  currentTutorContext = computed(() => {
    const task = this.currentTask();
    if (!task) return '';

    const selectedDocs = this.selectedDocuments()
      .map(doc => `- ${doc.file_name}${doc.tags?.length ? ` (Tags: ${doc.tags.join(', ')})` : ''}`)
      .join('\n');
    const options = task.options.length ? `\nAntwortoptionen:\n${task.options.map(option => `- ${option}`).join('\n')}` : '';
    const currentAnswer = this.answer().trim() ? `\nAktuelle Nutzerantwort:\n${this.answer().trim()}` : '';
    const feedback = this.feedback() ? `\nBisheriges Feedback:\n${this.feedback()!.feedback}` : '';

    return [
      'Du unterstützt den Nutzer bei der aktuell angezeigten Practice-Aufgabe.',
      'Gib sokratische Hinweise und erkläre Konzepte, aber verrate die Lösung nicht direkt, solange der Nutzer noch übt.',
      `Aufgabentyp: ${task.task_type === 'multiple_choice' ? 'Multiple Choice' : 'Textaufgabe'}`,
      `Schwierigkeit: ${task.difficulty}/5`,
      task.context_excerpt ? `Sichtbare Grundlagen der aktuellen Aufgabe:\n${task.context_excerpt}` : '',
      `Aktuelle Aufgabe:\n${task.question}`,
      options,
      currentAnswer,
      feedback,
      selectedDocs ? `Ausgewählte Dokumente:\n${selectedDocs}` : '',
    ].filter(Boolean).join('\n\n');
  });

  ngOnInit() {
    this.loadDocuments();
  }

  loadDocuments() {
    this.isLoadingDocuments.set(true);
    this.documentsService.getDocuments().subscribe({
      next: docs => {
        this.documents.set(docs);
        this.isLoadingDocuments.set(false);
      },
      error: () => {
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to load documents.' });
        this.isLoadingDocuments.set(false);
      },
    });
  }

  setTextFilter(value: string) {
    this.textFilter.set(value);
  }

  toggleTag(tag: string) {
    this.selectedTagFilters.update(tags => {
      if (tags.includes(tag)) {
        return tags.filter(t => t !== tag);
      }
      return [...tags, tag];
    });
  }

  clearFilters() {
    this.textFilter.set('');
    this.selectedTagFilters.set([]);
  }

  toggleDocument(doc: DocumentResponse) {
    this.selectedDocumentIds.update(ids => {
      if (ids.includes(doc.document_id)) {
        return ids.filter(id => id !== doc.document_id);
      }
      return [...ids, doc.document_id];
    });
  }

  selectAllFiltered() {
    const filteredIds = this.filteredDocuments().map(doc => doc.document_id);
    this.selectedDocumentIds.update(ids => Array.from(new Set([...ids, ...filteredIds])));
  }

  clearSelection() {
    this.selectedDocumentIds.set([]);
  }

  startPractice() {
    if (this.selectedDocumentIds().length === 0) {
      this.messageService.add({ severity: 'warn', summary: 'No Documents', detail: 'Select at least one document.' });
      return;
    }

    this.hasStarted.set(true);
    this.generateNextTask();
  }

  backToSetup() {
    this.hasStarted.set(false);
    this.currentTask.set(null);
    this.answer.set('');
    this.feedback.set(null);
  }

  generateNextTask() {
    if (this.selectedDocumentIds().length === 0 || this.isGenerating()) return;

    this.isGenerating.set(true);
    this.currentTask.set(null);
    this.answer.set('');
    this.feedback.set(null);

    this.documentsService.generatePracticeTask({
      document_ids: this.selectedDocumentIds(),
      difficulty: this.difficulty(),
      tags: this.selectedTagFilters(),
      text_filter: this.textFilter(),
    }).subscribe({
      next: task => {
        this.currentTask.set(task);
        this.isGenerating.set(false);
      },
      error: err => {
        this.messageService.add({
          severity: 'error',
          summary: 'Practice Error',
          detail: err.error?.detail || 'Failed to generate a practice task.',
        });
        this.isGenerating.set(false);
      },
    });
  }

  setAnswer(value: string) {
    this.answer.set(value);
    if (this.feedback()?.correct === false) {
      this.feedback.set(null);
    }
  }

  submitAnswer() {
    const task = this.currentTask();
    if (!task || !this.canSubmit()) return;

    this.isSubmitting.set(true);
    this.documentsService.submitPracticeAnswer(task.practice_task_id, this.answer()).subscribe({
      next: result => {
        this.feedback.set(result);
        this.isSubmitting.set(false);

        if (result.correct && result.awarded_coins > 0) {
          this.soundService.playWin();
          confetti({
            particleCount: 90,
            spread: 65,
            origin: { y: 0.65 },
            colors: ['#7c3aed', '#4f46e5', '#fbbf24'],
          });
        } else if (result.correct === false) {
          this.soundService.playLoss();
        }
      },
      error: err => {
        this.messageService.add({
          severity: 'error',
          summary: 'Practice Error',
          detail: err.error?.detail || 'Failed to submit your answer.',
        });
        this.isSubmitting.set(false);
      },
    });
  }
}
