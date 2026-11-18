from .scheduler_base import SchedulerBase
from .simulator_task_generator import SimulatorTaskGenerator
from .task_definition import TaskDefinition

class Simulator:
    def __init__(self):
        self.scheduler: SchedulerBase | None = None
        self.task_generator: SimulatorTaskGenerator | None = None

    def set_scheduler(self, scheduler: SchedulerBase) -> None:
        if self.task_generator is None:
            raise ValueError("Load task definitions before setting up a scheduler.")
        self.reset_simulator()
        scheduler.reset()
        self.scheduler = scheduler

    def load_task_definitions(self, task_definitions: TaskDefinition | list[TaskDefinition]) -> None:
        if self.task_generator is not None:
            raise ValueError("Task definitions are already loaded. Create a new Simulator for different tasks.")
        self.task_generator = SimulatorTaskGenerator()
        self.task_generator.setup_task_generator(task_definitions)
        self.reset_simulator()

    def reset_simulator(self) -> None:
        """Preserve task definitions and remove the current scheduler."""
        if self.scheduler is not None:
            self.scheduler.reset()
        self.scheduler = None

        if self.task_generator is not None:
            self.task_generator.reset_task_generator()

    def run(self) -> None:
        if self.scheduler is None or self.task_generator is None:
            raise ValueError("Simulator is not properly set up. Please set up the scheduler and task generator before running.")

        # Restart execution without detaching the configured scheduler.
        self.scheduler.reset()
        self.task_generator.reset_task_generator()
        current_time = 0.0
        while self.task_generator.any_task_remain() or self.scheduler.remain_task_number() > 0:
            # Run the task generator tick. It returns the tasks that ready to be added to the scheduler's ready queue at the current time.
            tasks_to_add = self.task_generator.tick(current_time)

            # Add the ready tasks to the scheduler's ready queue
            self.scheduler.add_task_to_ready_queue(tasks_to_add)

            # Execute the scheduler's logic for a single time tick
            passed_time_in_tick = self.scheduler.tick(current_time)

            if passed_time_in_tick == 0:
                # If no time has passed, it means the scheduler is idle. We can increment the current time by a small value (e.g., 1) to avoid an infinite loop.
                print(f"Scheduler is idle at time {current_time}. No tasks to execute.")
                passed_time_in_tick = 1

            # Update the current time based on the time passed in this tick
            current_time += passed_time_in_tick

        print("Simulation completed.")

    def get_results(self):
        task_cycles = list(self.scheduler.get_completed_task_cycles()) if self.scheduler else []
        idle_times = list(self.scheduler.get_idle_times()) if self.scheduler else []
        return task_cycles, idle_times
