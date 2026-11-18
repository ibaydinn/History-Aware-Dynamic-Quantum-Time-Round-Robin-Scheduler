from .task_definition import TaskDefinition
from .task_cycle import TaskCycle


class SimulatorTaskGenerator:
    def __init__(self) -> None:
        self.task_definitions: list[TaskDefinition] = []
        self.task_to_current_cycle: dict[str, int] = {}
        self.in_flight: dict[str, TaskCycle] = {}
        
        self.reset_task_generator()

    def setup_task_generator(
        self, task_definition: TaskDefinition | list[TaskDefinition]
    ) -> None:
        definitions = (
            task_definition
            if isinstance(task_definition, list)
            else [task_definition]
        )

        for task in definitions:
            self.task_definitions.append(task)
            self.task_to_current_cycle[task.name] = 0

    def reset_task_generator(self) -> None:
        self.task_definitions: list[TaskDefinition] = []
        self.task_to_current_cycle: dict[str, int] = {}
        self.in_flight: dict[str, TaskCycle] = {}

    def tick(self, current_time: float) -> list[TaskCycle]:
        released_cycles: list[TaskCycle] = []

        for task in self.task_definitions:
            cycle_number = self.task_to_current_cycle[task.name]

            # If the task has completed all its cycles or is already in flight, skip it.
            if cycle_number >= task.cycle_count or task.name in self.in_flight:
                continue

            # Get the scheduled arrival time for this cycle of the task
            scheduled_arrival = task.arrival_time + cycle_number * task.period

            # If the scheduled arrival time is in the future, skip this task for now.
            if scheduled_arrival > current_time:
                continue

            # Create a new TaskCycle for this task and cycle number
            cycle = TaskCycle.createTaskCycle(
                task_name=task.name,
                cycle_number=cycle_number,
                arrival_time=scheduled_arrival,
                remaining_time=task.burst_times_per_cycle[cycle_number],
                on_complete_callback=self.callback,
            )

            self.in_flight[task.name] = cycle
            released_cycles.append(cycle)

        return released_cycles

    def callback(self, task_cycle: TaskCycle) -> None:
        task_name = task_cycle.task_name

        if self.in_flight.get(task_name) is task_cycle:
            del self.in_flight[task_name]
            self.task_to_current_cycle[task_name] += 1
        else:
            raise ValueError(
                f"Callback received for task cycle {task_cycle.task_name} "
                f"which is not in flight."
                f"This indicates a logic error in the task generator or scheduler."
            )

    def any_task_remain(self) -> bool:
        # Check if any task has remaining cycles to be released.
        return any(
            self.task_to_current_cycle[task.name] < task.cycle_count for task in self.task_definitions
        )