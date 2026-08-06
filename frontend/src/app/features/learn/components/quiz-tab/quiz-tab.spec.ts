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
    fixture.componentRef.setInput('quizzes', []);
    fixture.componentRef.setInput('quizAttempts', {});
    fixture.componentRef.setInput('selectedAnswers', {});
    fixture.componentRef.setInput('isSubmittingQuiz', {});
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
