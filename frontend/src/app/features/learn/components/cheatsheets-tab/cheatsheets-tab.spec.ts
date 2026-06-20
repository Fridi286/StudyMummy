import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CheatsheetsTab } from './cheatsheets-tab';

describe('CheatsheetsTab', () => {
  let component: CheatsheetsTab;
  let fixture: ComponentFixture<CheatsheetsTab>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CheatsheetsTab],
    }).compileComponents();

    fixture = TestBed.createComponent(CheatsheetsTab);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
