import { Pipe, PipeTransform } from '@angular/core';
import { backendAssetUrl } from '../../core/config/api.config';

@Pipe({ name: 'backendAssetUrl', standalone: true })
export class BackendAssetUrlPipe implements PipeTransform {
  transform(value: string | null | undefined): string {
    return value ? backendAssetUrl(value) : '';
  }
}
