from __future__ import annotations
from dataclasses import dataclass

def create_task_from_json(json_data: dict) -> TaskDefinition:
    """Construct a validated task, rejecting missing and unknown fields."""
    if not isinstance(json_data, dict):
        raise ValueError("Each task must be a JSON object.")
    try:
        return TaskDefinition(**json_data)
    except TypeError as error:
        raise ValueError(f"Invalid task fields: {error}") from error


@dataclass
class TaskDefinition:
    name: str
    arrival_time: int
    burst_time: int  # Requested execution duration, independent of actual cycle durations.
    actual_burst_times: list[int]  # Required actual execution duration for every cycle.
    period: int = 0 # Period is 0 for single-shot tasks, and can be greater than 0 for cyclic tasks.
    cycle_count: int = 1 # Cycle count is at least 1 for single-shot tasks, and can be greater than 1 for cyclic tasks.

    def __post_init__(self) -> None:
        self.validate()
        self.actual_burst_times = list(self.actual_burst_times)

    def validate(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Task name must be a non-empty string.")
        for field, minimum in (("arrival_time", 0), ("burst_time", 1),
                               ("period", 0), ("cycle_count", 1)):
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
                raise ValueError(f"{field} must be an integer greater than or equal to {minimum}.")
        if self.cycle_count > 1 and self.period == 0:
            raise ValueError("Period must be positive for tasks with multiple cycles.")
        self._validate_burst_times(self.actual_burst_times)

    def _validate_burst_times(self, burst_times: list[int]) -> None:
        if not isinstance(burst_times, list):
            raise ValueError("actual_burst_times must be a list of positive integers.")
        if len(burst_times) != self.cycle_count:
            raise ValueError("Length of actual_burst_times must match cycle_count.")
        if any(isinstance(burst, bool) or not isinstance(burst, int) or burst <= 0
               for burst in burst_times):
            raise ValueError("actual_burst_times must contain positive integers.")
