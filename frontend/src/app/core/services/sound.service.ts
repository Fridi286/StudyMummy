import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class SoundService {
  private audioCtx: AudioContext | null = null;
  private enabled: boolean = true;

  constructor() { }

  private initContext() {
    if (!this.audioCtx) {
      this.audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
    }
    if (this.audioCtx.state === 'suspended') {
      this.audioCtx.resume();
    }
  }

  toggleSound(enabled: boolean) {
    this.enabled = enabled;
  }

  // Play a short tick for spinning
  playTick() {
    if (!this.enabled) return;
    this.initContext();
    if (!this.audioCtx) return;

    const osc = this.audioCtx.createOscillator();
    const gainNode = this.audioCtx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(800, this.audioCtx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(100, this.audioCtx.currentTime + 0.05);

    gainNode.gain.setValueAtTime(0.1, this.audioCtx.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioCtx.currentTime + 0.05);

    osc.connect(gainNode);
    gainNode.connect(this.audioCtx.destination);

    osc.start();
    osc.stop(this.audioCtx.currentTime + 0.05);
  }

  // Play a bright win chime
  playWin() {
    if (!this.enabled) return;
    this.initContext();
    if (!this.audioCtx) return;

    const notes = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6
    const now = this.audioCtx.currentTime;

    notes.forEach((freq, i) => {
      const osc = this.audioCtx!.createOscillator();
      const gainNode = this.audioCtx!.createGain();
      
      osc.type = 'sine';
      osc.frequency.value = freq;

      const startTime = now + (i * 0.1);
      gainNode.gain.setValueAtTime(0, startTime);
      gainNode.gain.linearRampToValueAtTime(0.2, startTime + 0.05);
      gainNode.gain.exponentialRampToValueAtTime(0.01, startTime + 0.5);

      osc.connect(gainNode);
      gainNode.connect(this.audioCtx!.destination);

      osc.start(startTime);
      osc.stop(startTime + 0.5);
    });
  }

  // Play a huge jackpot sound
  playJackpot() {
    if (!this.enabled) return;
    this.initContext();
    if (!this.audioCtx) return;

    const chords = [
      [523.25, 659.25, 783.99], // C major
      [659.25, 830.61, 987.77], // E major
      [783.99, 987.77, 1174.66], // G major
      [1046.50, 1318.51, 1567.98] // C major octave up
    ];

    const now = this.audioCtx.currentTime;

    chords.forEach((chord, i) => {
      const startTime = now + (i * 0.3);
      chord.forEach(freq => {
        const osc = this.audioCtx!.createOscillator();
        const gainNode = this.audioCtx!.createGain();

        osc.type = 'triangle';
        osc.frequency.value = freq;

        gainNode.gain.setValueAtTime(0, startTime);
        gainNode.gain.linearRampToValueAtTime(0.15, startTime + 0.1);
        gainNode.gain.exponentialRampToValueAtTime(0.01, startTime + 0.8);

        osc.connect(gainNode);
        gainNode.connect(this.audioCtx!.destination);

        osc.start(startTime);
        osc.stop(startTime + 0.8);
      });
    });
  }

  // Play a descending loss tone
  playLoss() {
    if (!this.enabled) return;
    this.initContext();
    if (!this.audioCtx) return;

    const osc = this.audioCtx.createOscillator();
    const gainNode = this.audioCtx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(250, this.audioCtx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(150, this.audioCtx.currentTime + 0.4);

    gainNode.gain.setValueAtTime(0.1, this.audioCtx.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioCtx.currentTime + 0.4);

    osc.connect(gainNode);
    gainNode.connect(this.audioCtx.destination);

    osc.start();
    osc.stop(this.audioCtx.currentTime + 0.4);
  }
}
