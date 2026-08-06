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
});
