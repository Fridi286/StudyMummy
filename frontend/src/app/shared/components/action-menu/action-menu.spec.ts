import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { vi } from 'vitest';

import { ActionMenuComponent } from './action-menu';

describe('ActionMenuComponent', () => {
  let component: ActionMenuComponent;
  let fixture: ComponentFixture<ActionMenuComponent>;
  let anchor: HTMLButtonElement;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ActionMenuComponent],
      providers: [provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(ActionMenuComponent);
    component = fixture.componentInstance;
    anchor = document.createElement('button');
    fixture.nativeElement.appendChild(anchor);
  });

  afterEach(() => fixture.destroy());

  it('renders grouped items and executes their commands', async () => {
    const command = vi.fn();
    fixture.componentRef.setInput('model', [
      {
        label: 'Account',
        items: [
          { label: 'Profile', icon: 'pi pi-user', command },
          { label: 'Documents', icon: 'pi pi-file' },
        ],
      },
      {
        label: 'Actions',
        items: [{ label: 'Sign Out', icon: 'pi pi-sign-out' }],
      },
    ]);
    fixture.detectChanges();

    anchor.addEventListener('click', (event) => component.toggle(event));
    anchor.click();
    fixture.detectChanges();
    await fixture.whenStable();

    const content = document.body.querySelector('[data-testid="action-menu-content"]');
    expect(content?.textContent).toContain('Account');
    expect(content?.textContent).toContain('Profile');
    expect(content?.textContent).toContain('Documents');
    expect(content?.textContent).toContain('Actions');
    expect(content?.textContent).toContain('Sign Out');

    const profileButton = [...(content?.querySelectorAll('button') ?? [])]
      .find((button) => button.textContent?.includes('Profile')) as HTMLButtonElement;
    profileButton.click();
    expect(command).toHaveBeenCalledOnce();
  });
});
