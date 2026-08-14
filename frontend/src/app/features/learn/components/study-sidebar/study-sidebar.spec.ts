import { ComponentFixture, TestBed } from '@angular/core/testing';

import { StudySidebar } from './study-sidebar';

describe('StudySidebar', () => {
  let component: StudySidebar;
  let fixture: ComponentFixture<StudySidebar>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StudySidebar],
    }).compileComponents();

    fixture = TestBed.createComponent(StudySidebar);
    fixture.componentRef.setInput('documents', []);
    fixture.componentRef.setInput('activeDocument', null);
    fixture.componentRef.setInput('isAnalyzing', false);
    fixture.componentRef.setInput('isLibraryExpanded', true);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('renders the document actions when the popup menu is opened', async () => {
    fixture.componentRef.setInput('documents', [
      {
        document_id: 'document-1',
        user_id: 'user-1',
        file_name: 'lecture.pdf',
        storage_path: 'uploads/lecture.pdf',
        tags: [],
        uploaded_at: '2026-08-14T10:00:00Z',
      },
    ]);
    fixture.detectChanges();

    const menuButton = fixture.nativeElement.querySelector('[data-testid="document-actions"]') as HTMLButtonElement;
    menuButton.click();
    fixture.detectChanges();
    await fixture.whenStable();

    const menu = document.body.querySelector('[data-testid="action-menu-content"]');
    expect(menu?.textContent).toContain('Edit Tags');
    expect(menu?.textContent).toContain('Download');
    expect(menu?.textContent).toContain('Delete');
  });
});
