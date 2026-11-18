from abc import ABC, abstractmethod
from .task_cycle import TaskCycle

class SchedulerBase(ABC):
    name = "BaseScheduler"

    def __init__(self):
        self.completed_task_cycles : list[TaskCycle] = []
        self.idle_times : list[tuple[int, int]] = []  # List of tuples (start_time, end_time) for idle periods

    @abstractmethod
    def add_task_to_ready_queue(self, task_instance: TaskCycle | list[TaskCycle]) -> None:
        """Add a task cycle to the scheduler's ready queue.w"""
        pass

    @abstractmethod
    def tick(self, current_time: float) -> float:
        """Return a positive, finite elapsed duration; idle ticks must also record idle time."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset the scheduler's internal state."""
        self.completed_task_cycles = []
        self.idle_times = []

    @abstractmethod
    def remain_task_number(self) -> int:
        """Return the number of tasks remaining in the scheduler's ready queue."""
        pass

    def pass_idle_time(self, current_time: int):
        idle_time_duration = 1  # Define how long the scheduler should be idle
        self.idle_times.append((current_time, current_time + idle_time_duration))
        return idle_time_duration

    def get_completed_task_cycles(self) -> list[TaskCycle]:
        """Return the list of completed task cycles."""
        return self.completed_task_cycles

    def get_idle_times(self) -> list[tuple[int, int]]:
        """Return the list of idle times."""
        return self.idle_times
