import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'avatarUrl',
  standalone: true
})
export class AvatarUrlPipe implements PipeTransform {
  private static sessionCacheBuster = Date.now();

  transform(value?: string | null): string | undefined {
    if (!value) return undefined;
    if (value.startsWith('http')) return value;
    return `http://localhost:8000${value}?v=${AvatarUrlPipe.sessionCacheBuster}`;
  }
}
