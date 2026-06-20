import { ComponentFixture, TestBed } from '@angular/core/testing';

import { QuizTab } from './quiz-tab';

describe('QuizTab', () => {
  let component: QuizTab;
  let fixture: ComponentFixture<QuizTab>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [QuizTab],
    }).compileComponents();

    fixture = TestBed.createComponent(QuizTab);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
