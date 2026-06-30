import { Component, input, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CheatsheetResponse } from '../../../../core/services/documents.service';
import { MessageService } from 'primeng/api';
import { MarkdownPipe } from '../../../../shared/pipes/markdown.pipe';

@Component({
  selector: 'app-cheatsheets-tab',
  standalone: true,
  imports: [CommonModule, MarkdownPipe],
  templateUrl: './cheatsheets-tab.html',
  styleUrl: './cheatsheets-tab.css'
})
export class CheatsheetsTab {
  cheatsheets = input.required<CheatsheetResponse[]>();
  private messageService = inject(MessageService, { optional: true });

  copyMarkdown(sheet: CheatsheetResponse) {
    navigator.clipboard.writeText(sheet.content).then(() => {
      if (this.messageService) {
        this.messageService.add({ severity: 'success', summary: 'Copied', detail: 'Markdown copied to clipboard!' });
      }
    }).catch(() => {
      if (this.messageService) {
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to copy markdown.' });
      }
    });
  }

  downloadMarkdown(sheet: CheatsheetResponse) {
    const blob = new Blob([sheet.content], { type: 'text/markdown' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${sheet.title.replace(/\s+/g, '_').toLowerCase()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  }

  onMarkdownClick(event: MouseEvent) {
    const target = event.target as HTMLElement;
    if (target.tagName.toLowerCase() === 'a') {
      const href = target.getAttribute('href');
      if (href && href.startsWith('#')) {
        event.preventDefault(); // Prevent Angular router navigation
        
        let elementId = href.substring(1);
        try {
          // Decode URL encoded characters (e.g., Japanese, special symbols)
          elementId = decodeURIComponent(elementId);
        } catch (e) {
          // Ignore if decode fails
        }
        
        const element = document.getElementById(elementId);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }
    }
  }
}
