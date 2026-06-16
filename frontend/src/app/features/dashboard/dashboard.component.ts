import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { InputTextModule } from 'primeng/inputtext';
import { SelectModule } from 'primeng/select';
import { CheckboxModule } from 'primeng/checkbox';
import { ProgressBarModule } from 'primeng/progressbar';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    FormsModule,
    ButtonModule,
    CardModule,
    InputTextModule,
    SelectModule,
    CheckboxModule,
    ProgressBarModule,
  ],
  templateUrl: './dashboard.component.html',
})
export class DashboardComponent {
  // Component State
  textValue = '';
  selectedCity: any = null;
  checked = false;
  progressValue = 75;

  // Mock Data
  cities = [
    { name: 'New York', code: 'NY' },
    { name: 'Rome', code: 'RM' },
    { name: 'London', code: 'LDN' },
    { name: 'Istanbul', code: 'IST' },
    { name: 'Paris', code: 'PRS' },
  ];
}
