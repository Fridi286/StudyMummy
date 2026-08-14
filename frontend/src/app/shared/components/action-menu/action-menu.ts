import { CommonModule } from '@angular/common';
import { Component, ViewChild, computed, input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { MenuItem } from 'primeng/api';
import { Popover, PopoverModule } from 'primeng/popover';

interface ActionMenuSection {
  label?: string;
  items: MenuItem[];
}

@Component({
  selector: 'app-action-menu',
  standalone: true,
  imports: [CommonModule, RouterLink, PopoverModule],
  templateUrl: './action-menu.html',
})
export class ActionMenuComponent {
  readonly model = input<MenuItem[]>([]);
  readonly styleClass = input('w-52');
  readonly ariaLabel = input('Actions');

  @ViewChild('popover') private popover?: Popover;

  readonly sections = computed<ActionMenuSection[]>(() => {
    const sections: ActionMenuSection[] = [];
    let ungrouped: MenuItem[] = [];

    const flushUngrouped = () => {
      if (ungrouped.length > 0) {
        sections.push({ items: ungrouped });
        ungrouped = [];
      }
    };

    for (const item of this.model()) {
      if (item.visible === false) continue;

      if (item.items?.length) {
        flushUngrouped();
        sections.push({
          label: item.label,
          items: item.items.filter((child) => child.visible !== false),
        });
      } else if (!item.separator) {
        ungrouped.push(item);
      }
    }

    flushUngrouped();
    return sections;
  });

  toggle(event: Event): void {
    this.popover?.toggle(event);
  }

  select(event: Event, item: MenuItem): void {
    if (item.disabled) {
      event.preventDefault();
      return;
    }

    item.command?.({ originalEvent: event, item });
    this.popover?.hide();
  }
}
