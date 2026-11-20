from math import isfinite
from .task_definition import TaskDefinition

class TaskCycle:

    def __init__(self):
        # Preset values for the task cycle
        self.task_name: str = ""
        self.cycle_number: int = 0
        self.definition: TaskDefinition = None
        self.remaining_burst_time: int = -1
        self.arrival_time: int = -1

        # Track the execution timeline for this cycle
        self.start_time: int = -1
        self.end_time: int = -1

        # Record this cycle's execution instances
        self.exec_timeline : list[tuple[int, int]] = []  # List of tuples (start_time, end_time) for each execution instance

        # Callback for when the task cycle completes
        self.on_complete_callback = None
    
    @staticmethod
    def createTaskCycle(task_name: str, cycle_number: int, arrival_time: int, remaining_time: int, task_definition: TaskDefinition, on_complete_callback=None) -> 'TaskCycle':
        task_cycle = TaskCycle()
        task_cycle.task_name = task_name
        task_cycle.cycle_number = cycle_number
        task_cycle.arrival_time = arrival_time
        task_cycle.remaining_burst_time = remaining_time
        task_cycle.definition = task_definition
        task_cycle.on_complete_callback = on_complete_callback
        return task_cycle

    def execute(self, current_time: int, duration: int) -> int:
        if (isinstance(current_time, bool)
                or not isinstance(current_time, (int, float))
                or (isinstance(current_time, float) and not isfinite(current_time))
                or current_time < 0):
            raise ValueError("current_time must be a non-negative, finite number.")
        if current_time < self.arrival_time:
            raise ValueError("Cannot execute before the task's arrival time.")
        if self.exec_timeline and current_time < self.exec_timeline[-1][1]:
            raise ValueError("Execution cannot overlap a previous interval.")

        if isinstance(duration, bool) or not isinstance(duration, int) or duration <= 0:
            raise ValueError("Execution duration must be a positive integer.")
        if self.is_completed():
            raise ValueError("Cannot execute a completed task cycle.")
        if self.remaining_burst_time < 0:
            raise ValueError("Task cycle has not been initialized with a valid burst time.")
        # Execute the task cycle for the given duration.
        # If duration is greater than the remaining burst time,
        # Return the passed time in here.
        
        # If first time executing, set the start time
        if self.start_time == -1:
            self.start_time = current_time

        passed_time_in_here = duration

        if self.remaining_burst_time <= duration:
            # Task Cycle completes
            self.end_time = current_time + self.remaining_burst_time
            passed_time_in_here = self.remaining_burst_time
            self.remaining_burst_time = 0
        else:
            # Task Cycle does not complete
            self.remaining_burst_time -= duration
            passed_time_in_here = duration  

        # Record this execution instance
        self.exec_timeline.append((current_time, current_time + passed_time_in_here))

        # Notify observers only after all completion state has been recorded.
        if self.is_completed() and self.on_complete_callback is not None:
            self.on_complete_callback(self)
        
        return passed_time_in_here

    def is_completed(self) -> bool:
        return self.remaining_burst_time == 0

    def get_execution_timeline(self) -> list[tuple[int, int]]:
        """Return the execution timeline for this task cycle."""
        return self.exec_timeline
