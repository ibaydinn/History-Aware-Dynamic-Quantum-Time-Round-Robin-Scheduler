from scheduler_simulator import SchedulerBase
from scheduler_simulator import TaskCycle


class EnhancedRR(SchedulerBase):
    name = "Enhanced Round Robin"

    def __init__(self):
        super().__init__()
        self.ready_que : list[TaskCycle] = []
        self.run_same_task_again = False
        self.first_time = True
        
    def add_task_to_ready_queue(self, task_instance: list[TaskCycle] | TaskCycle) -> None:
        """Add a task instance to the scheduler's ready queue."""
        if isinstance(task_instance, list):
            self.ready_que.extend(task_instance)
        else:
            self.ready_que.append(task_instance)

    def tick(self, current_time: int) -> int:
        # Sort the ready queue based on execution time (shortest first)
        if not self.run_same_task_again and self.first_time:
            self.ready_que.sort(key=lambda task: task.definition.burst_time)
            self.first_time = False
    
        if len(self.ready_que) == 0:
            return self.pass_idle_time(current_time)
        
        median_burst_time = self.calculate_median([task.definition.burst_time for task in self.ready_que])

        selected_task = self.ready_que.pop(0)
        if selected_task:
            time_consumed = selected_task.execute(current_time, median_burst_time)

            if not selected_task.is_completed():
                # Check if the task's remaining time is less than or equal to the median burst time
                if selected_task.remaining_burst_time <= median_burst_time:
                    # If yes, add it to the front of the ready queue
                    # self.run_this_task = selected_task
                    self.ready_que.insert(0, selected_task)
                    self.run_same_task_again = True
                else:
                    # If not, add it to the end of the ready queue
                    self.ready_que.append(selected_task)
                    self.run_same_task_again = False
            
            else:
                # If the task is finished, collect its timeline.
                self.record_finished_task_cycle(selected_task)
                
            return time_consumed
        
        # No task was executed, delta time executed. Return 0 carry-over.
        return self.pass_idle_time(current_time)
    
    def reset(self):
        return super().reset()
    
    def info(self) -> str:
        return f"{self.name} - Enhanced Scheduling based on Median Burst Time)"

    def calculate_median(self, data: list[int]) -> float:
        if not data:
            return 0.0
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