import { Pipe, PipeTransform } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { marked } from 'marked';
import { gfmHeadingId } from 'marked-gfm-heading-id';
import DOMPurify from 'dompurify';

marked.use(gfmHeadingId());

@Pipe({
  name: 'markdown',
  standalone: true
})
export class MarkdownPipe implements PipeTransform {
  constructor(private sanitizer: DomSanitizer) {}

  transform(value: string | null | undefined): SafeHtml {
    if (!value) return '';
    const parsed = marked.parse(value) as string;
    const cleanHtml = DOMPurify.sanitize(parsed);
    return this.sanitizer.bypassSecurityTrustHtml(cleanHtml);
  }
}
