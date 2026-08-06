import { Component, signal, inject, OnInit, OnDestroy, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { InputNumberModule } from 'primeng/inputnumber';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';
import { AuthService } from '../../../../core/auth/auth.service';
import { CasinoService } from '../../../../core/services/casino.service';
import { SoundService } from '../../../../core/services/sound.service';
import confetti from 'canvas-confetti';

const EMOJIS = ['📚', '🎓', '✏️', '☕', '🧠'];

@Component({
  selector: 'app-slots',
  standalone: true,
  imports: [CommonModule, FormsModule, ButtonModule, InputNumberModule, ToastModule],
  templateUrl: './slots.component.html'
})
export class SlotsComponent implements OnInit, OnDestroy {
  @Output() leave = new EventEmitter<void>();

  authService = inject(AuthService);
  casinoService = inject(CasinoService);
  messageService = inject(MessageService);
  soundService = inject(SoundService);

  reels = signal<string[]>(['📚', '🎓', '☕']);
  betAmount = signal<number>(10);
  userCoins = signal<number>(0);
  isSpinning = signal<boolean>(false);
  spinInterval: any;

  ngOnInit() {
    const user = this.authService.currentUser();
    if (user) {
      this.authService.fetchProfile(user.user_id).subscribe({
        next: (profile) => this.userCoins.set(profile.coins)
      });
    }
  }

  ngOnDestroy() {
    this.stopAnimation();
  }

  onLeave() {
    this.leave.emit();
  }

  setBet(amount: number) {
    if (this.isSpinning()) return;
    this.betAmount.set(amount);
  }

  spin() {
    if (this.isSpinning()) return;
    const user = this.authService.currentUser();
    if (!user) return;
    
    if (this.betAmount() > this.userCoins()) {
      this.messageService.add({ severity: 'error', summary: 'Error', detail: "You don't have enough Study Coins!" });
      return;
    }
    
    if (this.betAmount() <= 0) {
      this.messageService.add({ severity: 'error', summary: 'Error', detail: "Bet must be greater than 0!" });
      return;
    }

    this.isSpinning.set(true);
    this.startAnimation();

    this.casinoService.playSlotMachine(this.betAmount()).subscribe({
      next: (res) => {
        // Keep spinning for suspense
        setTimeout(() => {
          this.stopAnimation();
          this.setFinalReels(res.result);
          
          this.userCoins.set(res.new_balance);

          if (res.result === 'jackpot') {
            this.messageService.add({ severity: 'success', summary: 'JACKPOT!', detail: res.message });
          } else if (res.result === 'small_win') {
            this.messageService.add({ severity: 'info', summary: 'Winner!', detail: res.message });
          } else {
            this.messageService.add({ severity: 'secondary', summary: 'Oops!', detail: res.message });
          }
          this.isSpinning.set(false);
        }, 1500);
      },
      error: (err) => {
        this.stopAnimation();
        this.isSpinning.set(false);
        this.messageService.add({ severity: 'error', summary: 'Error', detail: err.error?.detail || 'Failed to spin' });
      }
    });
  }

  startAnimation() {
    this.spinInterval = setInterval(() => {
      this.reels.set([
        EMOJIS[Math.floor(Math.random() * EMOJIS.length)],
        EMOJIS[Math.floor(Math.random() * EMOJIS.length)],
        EMOJIS[Math.floor(Math.random() * EMOJIS.length)]
      ]);
      this.soundService.playTick();
    }, 100);
  }

  stopAnimation() {
    if (this.spinInterval) {
      clearInterval(this.spinInterval);
      this.spinInterval = null;
    }
  }

  setFinalReels(result: string) {
    if (result === 'jackpot') {
      const emoji = EMOJIS[Math.floor(Math.random() * EMOJIS.length)];
      this.reels.set([emoji, emoji, emoji]);
      this.soundService.playJackpot();
      this.fireConfetti(true);
    } else if (result === 'small_win') {
      const match = EMOJIS[Math.floor(Math.random() * EMOJIS.length)];
      let diff = match;
      while (diff === match) {
        diff = EMOJIS[Math.floor(Math.random() * EMOJIS.length)];
      }
      const arr = [match, match, diff];
      arr.sort(() => Math.random() - 0.5);
      this.reels.set(arr);
      this.soundService.playWin();
      this.fireConfetti(false);
    } else {
      const shuffled = [...EMOJIS].sort(() => Math.random() - 0.5);
      this.reels.set([shuffled[0], shuffled[1], shuffled[2]]);
      this.soundService.playLoss();
    }
  }

  private fireConfetti(isJackpot: boolean) {
    if (isJackpot) {
      const duration = 3000;
      const end = Date.now() + duration;

      const frame = () => {
        confetti({
          particleCount: 5,
          angle: 60,
          spread: 55,
          origin: { x: 0 },
          colors: ['#4f46e5', '#7c3aed', '#fbbf24']
        });
        confetti({
          particleCount: 5,
          angle: 120,
          spread: 55,
          origin: { x: 1 },
          colors: ['#4f46e5', '#7c3aed', '#fbbf24']
        });

        if (Date.now() < end) {
          requestAnimationFrame(frame);
        }
      };
      frame();
    } else {
      confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.6 },
        colors: ['#4f46e5', '#7c3aed', '#fbbf24']
      });
    }
  }
}
