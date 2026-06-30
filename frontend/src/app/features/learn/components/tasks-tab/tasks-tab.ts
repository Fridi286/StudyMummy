import { Component, input, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TaskResponse, TaskStatus } from '../../../../core/services/documents.service';

export interface TaskStatusChange {
  task: TaskResponse;
  status: TaskStatus;
}

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
  taskStatusChange = output<TaskStatusChange>();

  statuses: { value: TaskStatus; label: string; icon: string; classes: string }[] = [
    { value: 'open', label: 'Open', icon: 'pi-circle', classes: 'bg-slate-50 text-slate-600 border-slate-200' },
    { value: 'in_progress', label: 'In Progress', icon: 'pi-play-circle', classes: 'bg-sky-50 text-sky-700 border-sky-200' },
    { value: 'solved', label: 'Solved', icon: 'pi-check-circle', classes: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
    { value: 'repeat', label: 'Repeat', icon: 'pi-refresh', classes: 'bg-amber-50 text-amber-700 border-amber-200' }
  ];

  statusMeta(status: TaskStatus) {
    return this.statuses.find(item => item.value === status) ?? this.statuses[0];
  }

  onStatusSelect(task: TaskResponse, event: Event) {
    const status = (event.target as HTMLSelectElement).value as TaskStatus;
    this.taskStatusChange.emit({ task, status });
  }
  taskChat = output<TaskResponse>();
}
