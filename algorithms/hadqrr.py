from scheduler_simulator import SchedulerBase
from scheduler_simulator import TaskCycle

class HADQRRScheduler(SchedulerBase):
    def __init__(self, default_time_quantum: int = 20, history_length: int = 10) -> None:
        super().__init__()
        self.ready_que: list[TaskCycle] = []
        self.default_time_quantum = default_time_quantum
        self.history_length = history_length
        self.history : dict[str, list[int]] = {}
        self.run_times: dict[str, int] = {}
        self.mean_burst_times: dict[str, int] = {}

    def add_task_to_ready_queue(self, task_instance: TaskCycle | list[TaskCycle]) -> None:
        if isinstance(task_instance, list):
            self.ready_que.extend(task_instance)
        else:
            self.ready_que.append(task_instance)

    def tick(self, current_time: int) -> int:
        # Check if stage one or two should be used
        is_stage_2 = True
        for ti in self.ready_que:
            if not len(self.history.get(ti.task_name, [])) >= self.history_length / 2:
                is_stage_2 = False
                break

        # Stage One: Use default quantum
        quantum = self.default_time_quantum
        if is_stage_2:
            # Stage Two: Use mean burst times from history
            remaining_bursts = {}
            for ti in self.ready_que:
                run_time = self.run_times.get(ti.task_name, 0)
                mean_burst = self.mean_burst_times[ti.task_name]
                remaining_bursts[ti.task_name] = max(mean_burst - run_time, 0)

            # Sort ready queue based on remaining bursts
            self.ready_que.sort(key=lambda ti: remaining_bursts[ti.task_name])
            quantum = round(self.calculate_mean([self.mean_burst_times[ti.task_name] for ti in self.ready_que]))

        # Run the first task in the ready queue
        selected_task = self.ready_que.pop(0) if self.ready_que else None
        if selected_task:
            # Run the task with the determined quantum
            passed_time = selected_task.execute(current_time, quantum)

            if not selected_task.is_completed():
                # # Task not finished, re-add to ready queue
                self.run_times[selected_task.task_name] = self.run_times.get(selected_task.task_name, 0) + quantum
                self.ready_que.append(selected_task)
            else:
                # Task finished, record the finished task
                self.completed_task_cycles.append(selected_task)

                # Calculate actual burst time
                actual_burst_time = self.run_times.get(selected_task.task_name, 0) + passed_time

                # Remove any run time record because the task is finished
                if selected_task.task_name in self.run_times:
                    del self.run_times[selected_task.task_name]

                # Update history
                task_name = selected_task.task_name
                if task_name not in self.history:
                    self.history[task_name] = []
                self.history[task_name].append(actual_burst_time)

                # Maintain history size
                if len(self.history[task_name]) > self.history_length:
                    self.history[task_name].pop(0)
            
                # Update mean burst time
                self.mean_burst_times[task_name] = round(self.calculate_mean(self.history[task_name]))

            return passed_time
        
        return self.pass_idle_time(current_time)

    def calculate_median(self, data: list[int]) -> float:
        if not data:
            return 0.0
        sorted_data = sorted(data)
        n = len(sorted_data)
        mid = n // 2
        if n % 2 == 0:
            return (sorted_data[mid - 1] + sorted_data[mid]) / 2
        else:
            return sorted_data[mid]
        
    def calculate_mean(self, data: list[int]) -> float:
        if not data:
            return 0.0
        return sum(data) / len(data)
    
    def reset(self) -> None:
        super().reset()
        self.ready_que = []
        self.history = {}

    def remain_task_number(self) -> int:
        return len(self.ready_que)

    def get_name(self) -> str:
        return f"HADQRR"

    def get_configuration(self) -> dict:
        return {"default_time_quantum": self.default_time_quantum, "history_length": self.history_length}
