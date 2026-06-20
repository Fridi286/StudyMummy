import { Component, input, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MenuModule } from 'primeng/menu';
import { MenuItem } from 'primeng/api';
import { DocumentResponse } from '../../../../core/services/documents.service';

@Component({
  selector: 'app-study-sidebar',
  standalone: true,
  imports: [CommonModule, MenuModule],
  templateUrl: './study-sidebar.html',
  styleUrl: './study-sidebar.css'
})
export class StudySidebar {
  documents = input.required<DocumentResponse[]>();
  activeDocument = input.required<DocumentResponse | null>();
  isAnalyzing = input.required<boolean>();
  isLibraryExpanded = input.required<boolean>();

  fileUpload = output<Event>();
  documentSelect = output<DocumentResponse>();
  documentDelete = output<{event: Event, doc: DocumentResponse}>();
  toggleLibrary = output<boolean>();

  getMenuItems(doc: DocumentResponse): MenuItem[] {
    return [
      {
        label: 'Delete',
        icon: 'pi pi-trash',
        command: (event) => {
          this.documentDelete.emit({ event: event.originalEvent!, doc });
        }
      }
    ];
  }
}
