import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DocumentsService, DocumentResponse } from '../../core/services/documents.service';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { ToastModule } from 'primeng/toast';
import { FileUploadModule } from 'primeng/fileupload';
import { AutoCompleteModule } from 'primeng/autocomplete';
import { FormsModule } from '@angular/forms';
import { MessageService, ConfirmationService } from 'primeng/api';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { EditTagsDialog } from '../../shared/components/edit-tags-dialog/edit-tags-dialog';

@Component({
  selector: 'app-documents',
  standalone: true,
  imports: [CommonModule, CardModule, ButtonModule, ToastModule, FileUploadModule, AutoCompleteModule, FormsModule, ConfirmDialogModule, EditTagsDialog],
  providers: [MessageService, ConfirmationService],
  templateUrl: './documents.component.html',
  styleUrls: ['./documents.component.css']
})
export class DocumentsComponent implements OnInit {
  documentsService = inject(DocumentsService);
  messageService = inject(MessageService);
  confirmationService = inject(ConfirmationService);

  documents = signal<DocumentResponse[]>([]);
  isLoading = signal<boolean>(true);
  isUploading = signal<boolean>(false);
  uploadTags = signal<string[]>([]);

  isEditTagsDialogVisible = signal<boolean>(false);
  selectedDocToEdit = signal<DocumentResponse | null>(null);

  ngOnInit() {
    this.loadDocuments();
  }

  loadDocuments() {
    this.isLoading.set(true);
    this.documentsService.getDocuments().subscribe({
      next: (docs) => {
        this.documents.set(docs);
        this.isLoading.set(false);
      },
      error: (err) => {
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to load documents' });
        this.isLoading.set(false);
      }
    });
  }

  onUpload(event: any, fileUpload: any) {
    if (!event.files || event.files.length === 0) return;
    
    const file = event.files[0];
    this.isUploading.set(true);
    
    this.messageService.add({
      severity: 'info',
      summary: 'Uploading...',
      detail: 'Uploading and analyzing your document. This may take a minute...',
      sticky: true
    });
    
    this.documentsService.uploadDocument(file, this.uploadTags()).subscribe({
      next: (res) => {
        this.loadDocuments();
        this.isUploading.set(false);
        this.uploadTags.set([]);
        fileUpload.clear();
      },
      error: (err) => {
        this.messageService.add({ 
          severity: 'error', 
          summary: 'Upload Failed', 
          detail: err.error?.detail || 'An error occurred while uploading the document.' 
        });
        this.isUploading.set(false);
        fileUpload.clear();
      }
    });
  }

  downloadDocument(doc: DocumentResponse) {
    this.documentsService.downloadDocument(doc.document_id, doc.file_name);
  }

  deleteDocument(doc: DocumentResponse) {
    this.confirmationService.confirm({
      message: 'Are you sure you want to delete this document?',
      header: 'Confirm Deletion',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.documentsService.deleteDocument(doc.document_id).subscribe({
          next: () => {
            this.messageService.add({ severity: 'success', summary: 'Deleted', detail: 'Document deleted successfully.' });
            this.loadDocuments();
          },
          error: (err) => {
            this.messageService.add({ severity: 'error', summary: 'Delete Failed', detail: err.error?.detail || 'Could not delete document.' });
          }
        });
      }
    });
  }

  openEditTags(doc: DocumentResponse) {
    this.selectedDocToEdit.set(doc);
    this.isEditTagsDialogVisible.set(true);
  }
}
