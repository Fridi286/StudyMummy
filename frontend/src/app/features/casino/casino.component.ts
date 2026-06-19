import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SlotsComponent } from './components/slots/slots.component';

@Component({
  selector: 'app-casino',
  standalone: true,
  imports: [CommonModule, SlotsComponent],
  templateUrl: './casino.component.html',
  styleUrls: ['./casino.component.css']
})
export class CasinoComponent {
  activeGame = signal<'slots' | null>(null);

  selectGame(game: 'slots') {
    this.activeGame.set(game);
  }

  leaveGame() {
    this.activeGame.set(null);
  }
}
