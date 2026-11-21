from scheduler_simulator import SchedulerBase
from scheduler_simulator import TaskCycle

def create_proposed_scheduler_1_from_config(config: dict) -> 'ProposedScheduler_1':
    default_time_quantum = config.get("default_time_quantum", 20)
    alpha = config.get("alpha", 0.5)
    return ProposedScheduler_1(default_time_quantum=default_time_quantum, alpha=alpha)

class ProposedScheduler_1(SchedulerBase):
    def __init__(self, default_time_quantum: int = 20, alpha: float = 0.5) -> None:
        if isinstance(default_time_quantum, bool) or not isinstance(default_time_quantum, int) or default_time_quantum <= 0:
            raise ValueError("Time quantum must be a positive integer.")
        if isinstance(alpha, bool) or not isinstance(alpha, float) or alpha <= 0:
            raise ValueError("Alpha must be a positive float.")

        super().__init__()
        self.ready_que: list[TaskCycle] = []
        self.default_time_quantum = default_time_quantum
        self.alpha = alpha  # Smoothing factor for EMA

        self.ema_burst_times: dict[str, float] = {}  # Store EMA burst times for each task
        self.run_times: dict[str, int] = {}  # Store run times for each task

    def add_task_to_ready_queue(self, task_instance: TaskCycle | list[TaskCycle]) -> None:
        if isinstance(task_instance, list):
            self.ready_que.extend(task_instance)
        else:
            self.ready_que.append(task_instance)

    def reset(self) -> None:
        super().reset()
        self.ready_que = []
        self.ema_burst_times = {}
        self.run_times = {}

    def get_name(self) -> str:
        return f"EMA-One-Stage-Quantum Scheduler, alpha={self.alpha})"

    def get_configuration(self) -> dict:
        return {"default_time_quantum": self.default_time_quantum, "alpha": self.alpha}

    def remain_task_number(self) -> int:
        return len(self.ready_que)
    
    def tick(self, current_time: int) -> int:
        # Sort the ready queue based on priority (remaining burst time)
        self.ready_que.sort(key=self.calculate_priority)
        quantum = self.calculate_quantum()

        selected_task = self.ready_que.pop(0) if self.ready_que else None
        if selected_task:
            passed_time = selected_task.execute(current_time, quantum)

            if not selected_task.is_completed():
                # Task not finished

                # Record the run time for the task
                self.run_times[selected_task.task_name] = self.run_times.get(selected_task.task_name, 0) + passed_time

                # Add the task back to the ready queue for further execution
                self.ready_que.append(selected_task)
            else:
                # Task finished, record the finished task
                self.record_finished_task_cycle(selected_task)

                # Calculate actual burst time
                actual_burst_time = self.run_times.get(selected_task.task_name, 0) + passed_time

                # Delete the run time entry for the completed task
                if selected_task.task_name in self.run_times:
                    del self.run_times[selected_task.task_name]

                # Update EMA burst time for the task
                self.ema_burst_times[selected_task.task_name] = self.calculate_new_ema(selected_task.task_name, actual_burst_time)

            return passed_time

        return self.pass_idle_time(current_time)

    def calculate_new_ema(self, task_name: str, actual_burst_time: int) -> float:
        previous_ema = self.ema_burst_times.get(task_name, actual_burst_time)
        new_ema = (self.alpha * actual_burst_time) + ((1 - self.alpha) * previous_ema)
        return new_ema

    def calculate_quantum(self):
        if not self.ready_que:
            return self.default_time_quantum

        # Calculate the average burst time of the tasks in the ready queue
        burst_times = [self.estimate_remaining_time(task.task_name) for task in self.ready_que]
        
        quantum = self.calculate_mean(burst_times)
        if quantum <= 0:
            pass
        return quantum


    def estimate_busrt_time(self, task_name: str):
        """Estimate the burst time for a task using EMA."""
        if task_name not in self.ema_burst_times:
            # If no previous data, use default quantum as initial estimate
            return self.default_time_quantum
        else:
            return self.ema_burst_times[task_name]

    def estimate_remaining_time(self, task_name: str):
        """Estimate the remaining time for a task based on its EMA burst time and run time."""
        estimated_burst_time = self.estimate_busrt_time(task_name)
        current_run_time = self.run_times.get(task_name, 0)
        remaining_time = max(estimated_burst_time - current_run_time, 1)
        return remaining_time

    def calculate_priority(self, task: TaskCycle) -> float:
        """Calculate the priority of a task based on its estimated remaining time."""
        return self.estimate_remaining_time(task.task_name)

    def calculate_mean(self, data: list[int]) -> int:
        if not data:
            return 0
        return round(sum(data) / len(data))

    def calculate_median(self, data: list[int]) -> int:
        if not data:
            return 0
        sorted_data = sorted(data)
        n = len(sorted_data)
        mid = n // 2
        if n % 2 == 0:
            return round((sorted_data[mid - 1] + sorted_data[mid]) / 2)
        else:
            return sorted_data[mid]
    