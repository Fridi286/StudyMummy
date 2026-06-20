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
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
