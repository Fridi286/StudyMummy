import { Component, input, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { QuizResponse, QuizAttemptResponse } from '../../../../core/services/documents.service';

@Component({
  selector: 'app-quiz-tab',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './quiz-tab.html',
  styleUrl: './quiz-tab.css'
})
export class QuizTab {
  quizzes = input.required<QuizResponse[]>();
  quizAttempts = input.required<Record<string, QuizAttemptResponse[]>>();
  selectedAnswers = input.required<Record<string, Record<string, string>>>();
  isSubmittingQuiz = input.required<Record<string, boolean>>();

  answerSelect = output<{quizId: string, questionId: string, option: string}>();
  quizSubmit = output<QuizResponse>();
  quizRetake = output<string>();
}
