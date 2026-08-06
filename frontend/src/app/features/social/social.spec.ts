import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Social } from './social';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { MessageService, ConfirmationService } from 'primeng/api';

describe('Social', () => {
  let component: Social;
  let fixture: ComponentFixture<Social>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Social],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([]), MessageService, ConfirmationService],
    }).compileComponents();

    fixture = TestBed.createComponent(Social);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
