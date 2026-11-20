from scheduler_simulator import SchedulerBase
from scheduler_simulator import TaskCycle


class EnhancedRR(SchedulerBase):
    """ERRBTQ for an initial batch with known definition.burst_time values.

    Later arrivals/cycles append to the queue and use the same quantum until
    reset. This arrival policy extends the paper's initial-batch model.
    """
    name = "Enhanced Round Robin"

    def __init__(self):
        super().__init__()
        self.ready_que : list[TaskCycle] = []
        self.time_quantum: int | None = None
        
    def add_task_to_ready_queue(self, task_instance: list[TaskCycle] | TaskCycle) -> None:
        """Add a task instance to the scheduler's ready queue."""
        if isinstance(task_instance, list):
            self.ready_que.extend(task_instance)
        else:
            self.ready_que.append(task_instance)

    def tick(self, current_time: int) -> int:
        if not self.ready_que:
            return self.pass_idle_time(current_time)

        # ERRBTQ initializes once from the first non-empty batch. Use the
        # declared burst times as the known bursts, not actual cycle durations.
        if self.time_quantum is None:
            self.ready_que.sort(key=lambda task: task.definition.burst_time)
            self.time_quantum = self.calculate_median(
                [task.definition.burst_time for task in self.ready_que]
            )

        selected_task = self.ready_que.pop(0)
        time_consumed = selected_task.execute(current_time, self.time_quantum)
        if selected_task.is_completed():
            self.record_finished_task_cycle(selected_task)
        elif selected_task.remaining_burst_time <= self.time_quantum:
            # Continue this cycle before switching to another process.
            self.ready_que.insert(0, selected_task)
        else:
            self.ready_que.append(selected_task)
        return time_consumed

    def reset(self) -> None:
        super().reset()
        self.ready_que.clear()
        self.time_quantum = None

    def info(self) -> str:
        return f"{self.name} - Enhanced Scheduling based on Median Burst Time)"

    def calculate_median(self, data: list[int]) -> int:
        """Integer-time adaptation: nearest integer, with half ties to even."""
        if not data:
            raise ValueError("Cannot calculate a quantum from an empty batch.")
        sorted_data = sorted(data)
        n = len(sorted_data)
        mid = n // 2
        if n % 2 == 0:
            return round((sorted_data[mid - 1] + sorted_data[mid]) / 2)
        else:
            return sorted_data[mid]

    def get_name(self) -> str:
        return self.name

    def get_configuration(self) -> dict:
        return { }

    def remain_task_number(self) -> int:
        """Return the number of tasks remaining in the scheduler's ready queue."""
        return len(self.ready_que)
