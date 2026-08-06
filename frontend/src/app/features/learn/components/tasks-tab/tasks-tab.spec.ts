import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TasksTab } from './tasks-tab';

describe('TasksTab', () => {
  let component: TasksTab;
  let fixture: ComponentFixture<TasksTab>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TasksTab],
    }).compileComponents();

    fixture = TestBed.createComponent(TasksTab);
    fixture.componentRef.setInput('tasks', []);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
