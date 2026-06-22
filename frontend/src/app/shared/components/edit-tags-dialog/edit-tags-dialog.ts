import { Component, model, input, output, effect, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DialogModule } from 'primeng/dialog';
import { AutoCompleteModule } from 'primeng/autocomplete';
import { ButtonModule } from 'primeng/button';
import { MessageService } from 'primeng/api';
import { DocumentsService, DocumentResponse } from '../../../core/services/documents.service';

@Component({
  selector: 'app-edit-tags-dialog',
  standalone: true,
  imports: [CommonModule, FormsModule, DialogModule, AutoCompleteModule, ButtonModule],
  templateUrl: './edit-tags-dialog.html',
})
export class EditTagsDialog {
  visible = model<boolean>(false);
  document = input<DocumentResponse | null>(null);
  
  tagsUpdated = output<DocumentResponse>();

  documentsService = inject(DocumentsService);
  messageService = inject(MessageService);

  editTagsValue = signal<string[]>([]);
  isSaving = signal<boolean>(false);

  constructor() {
    effect(() => {
      const doc = this.document();
      if (doc && this.visible()) {
        // Reset tags when dialog opens
        this.editTagsValue.set([...doc.tags]);
      }
    }, { allowSignalWrites: true });
  }

  saveTags() {
    const doc = this.document();
    if (!doc) return;

    this.isSaving.set(true);
    this.documentsService.updateDocumentTags(doc.document_id, this.editTagsValue()).subscribe({
      next: (updatedDoc) => {
        this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Tags updated successfully.' });
        this.visible.set(false);
        this.isSaving.set(false);
        this.tagsUpdated.emit(updatedDoc);
      },
      error: (err) => {
        this.isSaving.set(false);
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to update tags.' });
      }
    });
  }
}
