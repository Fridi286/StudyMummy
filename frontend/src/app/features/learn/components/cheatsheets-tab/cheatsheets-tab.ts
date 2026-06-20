import { Component, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CheatsheetResponse } from '../../../../core/services/documents.service';

@Component({
  selector: 'app-cheatsheets-tab',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './cheatsheets-tab.html',
  styleUrl: './cheatsheets-tab.css'
})
export class CheatsheetsTab {
  cheatsheets = input.required<CheatsheetResponse[]>();
}
