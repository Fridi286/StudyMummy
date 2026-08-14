import { Component, input, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MenuItem } from 'primeng/api';
import { DocumentResponse } from '../../../../core/services/documents.service';
import { ActionMenuComponent } from '../../../../shared/components/action-menu/action-menu';

@Component({
  selector: 'app-study-sidebar',
  standalone: true,
  imports: [CommonModule, ActionMenuComponent],
  templateUrl: './study-sidebar.html',
  styleUrl: './study-sidebar.css'
})
export class StudySidebar {
  documents = input.required<DocumentResponse[]>();
  activeDocument = input.required<DocumentResponse | null>();
  isAnalyzing = input.required<boolean>();
  isLibraryExpanded = input.required<boolean>();
  libraryWidth = input<number>(320);
  isResizing = input<boolean>(false);

  fileUpload = output<Event>();
  documentSelect = output<DocumentResponse>();
  documentDownload = output<DocumentResponse>();
  documentEditTags = output<DocumentResponse>();
  documentDelete = output<{event: Event, doc: DocumentResponse}>();
  toggleLibrary = output<boolean>();
  resizeStart = output<MouseEvent>();

  activeMenuDoc: DocumentResponse | null = null;
  
  menuItems: MenuItem[] = [
    {
      label: 'Edit Tags',
      icon: 'pi pi-tags',
      command: (event) => {
        if (this.activeMenuDoc) {
          this.documentEditTags.emit(this.activeMenuDoc);
        }
      }
    },
    {
      label: 'Download',
      icon: 'pi pi-download',
      command: (event) => {
        if (this.activeMenuDoc) {
          this.documentDownload.emit(this.activeMenuDoc);
        }
      }
    },
    {
      label: 'Delete',
      icon: 'pi pi-trash',
      command: (event) => {
        if (this.activeMenuDoc) {
          this.documentDelete.emit({ event: event.originalEvent!, doc: this.activeMenuDoc });
        }
      }
    }
  ];

  openMenu(event: Event, menu: any, doc: DocumentResponse) {
    this.activeMenuDoc = doc;
    menu.toggle(event);
  }
}
