import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-learn',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './learn.html',
  styleUrl: './learn.css',
})
export class Learn {
  activeTab = signal<'quiz' | 'tasks' | 'cheatsheets'>('quiz');

  setTab(tab: 'quiz' | 'tasks' | 'cheatsheets') {
    this.activeTab.set(tab);
  }
}
