import { Component, effect, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChatService } from '../../../core/services/chat.service';
import { LEVEL_TITLES } from '../../constants/levels';

@Component({
  selector: 'app-reward-popup',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './reward-popup.html'
})
export class RewardPopupComponent {
  chatService = inject(ChatService);
  
  visible = signal<boolean>(false);
  rewardData = signal<any>(null);
  progressValue = signal<number>(0);
  
  isLevelUp = signal<boolean>(false);
  newRole = signal<string>('');
  newLevelNum = signal<number>(1);
  
  private hideTimeout: any;
  
  constructor() {
    effect(() => {
      const reward = this.chatService.latestReward();
      if (reward) {
        // Clear any existing timeout if rewards happen back-to-back
        if (this.hideTimeout) clearTimeout(this.hideTimeout);

        this.rewardData.set(reward);
        this.visible.set(true);
        
        const totalExp = reward.total_experience || 0;
        const previousExp = totalExp - (reward.experience || 0);
        
        const prevLevel = Math.floor(previousExp / 100) + 1;
        const newLevel = Math.floor(totalExp / 100) + 1;
        
        if (newLevel > prevLevel) {
          this.isLevelUp.set(true);
          this.newLevelNum.set(newLevel);
          this.newRole.set(LEVEL_TITLES[newLevel] || LEVEL_TITLES[LEVEL_TITLES.length - 1]);
        } else {
          this.isLevelUp.set(false);
        }
        
        // Start animation at the previous percentage
        this.progressValue.set(previousExp % 100);
        
        // Trigger the filling animation to the new percentage
        setTimeout(() => {
          this.progressValue.set(totalExp % 100);
        }, 50);
        
        // Auto hide after 4 seconds
        this.hideTimeout = setTimeout(() => {
          this.visible.set(false);
        }, 4000);
      }
    });
  }
}
