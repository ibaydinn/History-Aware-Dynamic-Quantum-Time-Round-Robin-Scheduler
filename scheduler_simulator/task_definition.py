from __future__ import annotations
from dataclasses import dataclass

@dataclass
class TaskDefinition:
    name: str
    arrival_time: int
    burst_time: int
    period: int | None = None  # Period is relevant for cyclic tasks; for single-shot tasks, this can be None
    cycle_count: int = 1 # Cycle count is at least 1 for single-shot tasks, and can be greater than 1 for cyclic tasks.

    # Calculate from the beginning
    burst_times_per_cycle: list[int] | None = None  # Specific burst times for each cycle

    def set_burst_times_per_cycle(self, burst_times: list[int]):
        if len(burst_times) != self.cycle_count:
            raise ValueError("Length of burst_times must match cycle_count.")
        if any(isinstance(burst, bool) or not isinstance(burst, int) or burst <= 0
               for burst in burst_times):
            raise ValueError("burst_times must contain positive integers.")
        self.burst_times_per_cycle = list(burst_times)