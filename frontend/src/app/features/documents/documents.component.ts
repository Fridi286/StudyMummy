import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DocumentsService, DocumentResponse } from '../../core/services/documents.service';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { ToastModule } from 'primeng/toast';
import { FileUploadModule } from 'primeng/fileupload';
import { MessageService } from 'primeng/api';

@Component({
  selector: 'app-documents',
  standalone: true,
  imports: [CommonModule, CardModule, ButtonModule, ToastModule, FileUploadModule],
  providers: [MessageService],
  templateUrl: './documents.component.html',
  styleUrls: ['./documents.component.css']
})
export class DocumentsComponent implements OnInit {
  documentsService = inject(DocumentsService);
  messageService = inject(MessageService);

  documents = signal<DocumentResponse[]>([]);
  isLoading = signal<boolean>(true);
  isUploading = signal<boolean>(false);

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
    
    this.documentsService.uploadDocument(file).subscribe({
      next: (res) => {
        this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Document uploaded successfully!' });
        this.loadDocuments();
        this.isUploading.set(false);
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
    if (!confirm('Are you sure you want to delete this document?')) return;
    
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
}
