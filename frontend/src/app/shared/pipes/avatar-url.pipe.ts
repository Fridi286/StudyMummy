import { Pipe, PipeTransform } from '@angular/core';
import { getStaticBaseUrl } from '../../core/config/api.config';

@Pipe({
  name: 'avatarUrl',
  standalone: true
})
export class AvatarUrlPipe implements PipeTransform {
  private static sessionCacheBuster = Date.now();

  transform(value?: string | null): string | undefined {
    if (!value) return undefined;
    if (value.startsWith('http')) return value;
    return `${getStaticBaseUrl()}${value}?v=${AvatarUrlPipe.sessionCacheBuster}`;
  }
}
