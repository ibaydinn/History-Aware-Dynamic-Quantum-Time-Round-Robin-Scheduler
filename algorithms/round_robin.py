from scheduler_simulator import SchedulerBase
from scheduler_simulator import TaskCycle

class RoundRobinScheduler(SchedulerBase):
    name = "RoundRobinScheduler"

    def __init__(self, time_quantum: int = 10) -> None:
        super().__init__()
        self.ready_que: list[TaskCycle] = []
        self.time_quantum = time_quantum
        self.new_tasks_added : list[TaskCycle] = []  # Track newly added tasks in the current tick
        self.pending_requeue: TaskCycle | None = None

    @property
    def time_quantum(self) -> int:
        return self._time_quantum

    @time_quantum.setter
    def time_quantum(self, value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError("Time quantum must be a positive integer.")
        self._time_quantum = value

    def add_task_to_ready_queue(self, task_instance: TaskCycle | list[TaskCycle]) -> None:
        if isinstance(task_instance, list):
            self.new_tasks_added.extend(task_instance)
        else:
            self.new_tasks_added.append(task_instance)

    def tick(self, current_time: int) -> int:
        # Add newly added tasks to the ready queue
        if self.new_tasks_added:
            self.ready_que.extend(self.new_tasks_added)
            self.new_tasks_added.clear()

        # Arrivals during the previous quantum precede its unfinished task.
        if self.pending_requeue is not None:
            self.ready_que.append(self.pending_requeue)
            self.pending_requeue = None

        # Get first task from the ready queue (FIFO)
        selected_task = self.ready_que.pop(0) if self.ready_que else None

        if selected_task:
            # Execute the selected task for the time quantum or until it completes
            passed_time = selected_task.execute(current_time, self.time_quantum)
            if selected_task.is_completed():
                self.completed_task_cycles.append(selected_task)
            else:
                self.pending_requeue = selected_task

            return passed_time

        # Task queue is empty, pass idle time
        return self.pass_idle_time(current_time)
        
    def reset(self) -> None:
        super().reset()
        self.ready_que = []
        self.new_tasks_added = []
        self.pending_requeue = None

    def remain_task_number(self) -> int:
        return (len(self.ready_que) + len(self.new_tasks_added)
                + int(self.pending_requeue is not None))

    def get_configuration(self) -> dict:
        return {"time_quantum": self.time_quantum}
