import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Learn } from './learn';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { MessageService, ConfirmationService } from 'primeng/api';

describe('Learn', () => {
  let component: Learn;
  let fixture: ComponentFixture<Learn>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Learn],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([]), MessageService, ConfirmationService],
    }).compileComponents();

    fixture = TestBed.createComponent(Learn);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
