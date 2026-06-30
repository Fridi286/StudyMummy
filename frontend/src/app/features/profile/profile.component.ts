import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { forkJoin, of, concatMap } from 'rxjs';
import { AuthService, UserResponse } from '../../core/auth/auth.service';
import { CardModule } from 'primeng/card';
import { AvatarModule } from 'primeng/avatar';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { BadgeModule } from 'primeng/badge';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { PasswordModule } from 'primeng/password';
import { FloatLabelModule } from 'primeng/floatlabel';
import { ToastModule } from 'primeng/toast';
import { FileUploadModule } from 'primeng/fileupload';
import { DialogModule } from 'primeng/dialog';
import { ProgressBarModule } from 'primeng/progressbar';
import { MessageService } from 'primeng/api';
import { ImageCropperComponent, ImageCroppedEvent, LoadedImage } from 'ngx-image-cropper';

import { LEVEL_TITLES } from '../../shared/constants/levels';
@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [
    CommonModule, FormsModule, CardModule, AvatarModule, ProgressSpinnerModule,
    BadgeModule, ButtonModule, InputTextModule, PasswordModule,
    FloatLabelModule, ToastModule, FileUploadModule, DialogModule,
    ImageCropperComponent, ProgressBarModule
  ],
  providers: [MessageService],
  templateUrl: './profile.component.html'
})
export class ProfileComponent implements OnInit {
  profileData = signal<UserResponse | null>(null);
  loading = signal<boolean>(true);
  error = signal<string | null>(null);

  isEditing = signal<boolean>(false);
  editData = signal<any>({});
  saving = signal<boolean>(false);

  avatarPreviewUrl = signal<string | null>(null);
  selectedAvatarFile = signal<File | null>(null);

  // Cropper State
  showCropperDialog = signal<boolean>(false);
  imageFileToCrop = signal<File | null>(null);
  croppedImageBlob = signal<Blob | null>(null);

  constructor(
    private authService: AuthService,
    private messageService: MessageService
  ) { }

  ngOnInit(): void {
    const user = this.authService.currentUser();
    if (user && user.user_id) {
      this.authService.fetchProfile(user.user_id).subscribe({
        next: (data) => {
          this.profileData.set(data);
          this.loading.set(false);
        },
        error: (err) => {
          this.error.set('Failed to load profile data.');
          this.loading.set(false);
        }
      });
    } else {
      this.error.set('No user logged in.');
      this.loading.set(false);
    }
  }

  get initials(): string {
    const data = this.profileData();
    if (!data) return 'SM';
    if (data.first_name && data.last_name) {
      return `${data.first_name[0]}${data.last_name[0]}`.toUpperCase();
    }
    return data.username.substring(0, 2).toUpperCase();
  }

  get fullAvatarUrl(): string | null {
    return this.authService.cachedAvatarUrl();
  }

  get expProgress(): number {
    const xp = this.profileData()?.experience || 0;
    return xp % 100;
  }

  get levelTitle(): string {
    const lvl = this.profileData()?.level || 1;
    if (lvl >= 1 && lvl <= 100) {
      return LEVEL_TITLES[lvl];
    }
    return lvl > 100 ? "Level Cap Reached" : LEVEL_TITLES[0];
  }

  onAvatarSelect(event: any): void {
    const files = event.files || (event.target && event.target.files);
    if (files && files.length > 0) {
      this.imageFileToCrop.set(files[0]);
      this.showCropperDialog.set(true);
    }
  }

  imageCropped(event: ImageCroppedEvent) {
    if (event.blob) {
      this.croppedImageBlob.set(event.blob);
    }
  }

  saveCrop() {
    const blob = this.croppedImageBlob();
    if (blob) {
      // Create a File from Blob
      const file = new File([blob], 'avatar.png', { type: 'image/png' });
      this.selectedAvatarFile.set(file);

      // Update preview
      const reader = new FileReader();
      reader.onload = (e: any) => {
        this.avatarPreviewUrl.set(e.target.result);
      };
      reader.readAsDataURL(blob);
    }
    this.showCropperDialog.set(false);
  }

  cancelCrop() {
    this.showCropperDialog.set(false);
    this.imageFileToCrop.set(null);
    this.croppedImageBlob.set(null);
  }

  toggleEdit(): void {
    if (!this.isEditing()) {
      const current = this.profileData();
      this.editData.set({
        first_name: current?.first_name || '',
        last_name: current?.last_name || '',
        username: current?.username || '',
        email: '',
        confirm_email: '',
        password: '',
        confirm_password: ''
      });
      this.avatarPreviewUrl.set(null);
      this.selectedAvatarFile.set(null);
    }
    this.isEditing.set(!this.isEditing());
  }

  onSave(): void {
    const user = this.authService.currentUser();
    if (!user || !user.user_id) return;

    this.saving.set(true);

    const updatePayload: any = {};
    const currentEdit = this.editData();

    // Validation
    if (currentEdit.email !== currentEdit.confirm_email) {
      this.messageService.add({ severity: 'warn', summary: 'Validation Error', detail: 'Email addresses do not match' });
      return;
    }

    if (currentEdit.password || currentEdit.confirm_password) {
      if (currentEdit.password !== currentEdit.confirm_password) {
        this.messageService.add({ severity: 'warn', summary: 'Validation Error', detail: 'Passwords do not match' });
        return;
      }
    }

    for (const key in currentEdit) {
      if (key !== 'confirm_email' && key !== 'confirm_password' && currentEdit[key] !== '') {
        updatePayload[key] = currentEdit[key];
      }
    }

    let update$ = of<any>(null);
    if (Object.keys(updatePayload).length > 0) {
      update$ = this.authService.updateProfile(user.user_id, updatePayload);
    }

    const avatarFile = this.selectedAvatarFile();

    if (Object.keys(updatePayload).length === 0 && !avatarFile) {
      this.saving.set(false);
      this.isEditing.set(false);
      return;
    }

    update$.pipe(
      concatMap((res) => {
        if (avatarFile) {
          return this.authService.uploadAvatar(user.user_id, avatarFile);
        }
        return of(res);
      })
    ).subscribe({
      next: () => {
        const currentUser = this.authService.currentUser();
        if (currentUser) {
          this.authService.fetchProfile(currentUser.user_id).subscribe(data => {
            this.profileData.set(data);
            this.isEditing.set(false);
            this.saving.set(false);
            this.avatarPreviewUrl.set(null);
            this.selectedAvatarFile.set(null);
            this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Profile updated successfully' });
          });
        }
      },
      error: (err) => {
        console.error(err);
        this.saving.set(false);
        let errorMsg = 'Failed to update profile';
        const errorData = err.error;
        if (errorData && errorData.detail) {
          if (Array.isArray(errorData.detail)) {
            errorMsg = errorData.detail.map((d: any) => {
              const field = d.loc && d.loc.length > 1 ? d.loc[1] : '';
              const msg = d.msg || 'Invalid value';
              return field ? `${field}: ${msg}` : msg;
            }).join(', ');
          } else {
            errorMsg = errorData.detail;
          }
        }
        this.messageService.add({ severity: 'error', summary: 'Error', detail: errorMsg });
      }
    });
  }
}
