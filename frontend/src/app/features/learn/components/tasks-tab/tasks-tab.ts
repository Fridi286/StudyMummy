import { Component, input, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TaskResponse } from '../../../../core/services/documents.service';

@Component({
  selector: 'app-tasks-tab',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './tasks-tab.html',
  styleUrl: './tasks-tab.css'
})
export class TasksTab {
  tasks = input.required<TaskResponse[]>();
  taskToggle = output<TaskResponse>();
  taskChat = output<TaskResponse>();
}
