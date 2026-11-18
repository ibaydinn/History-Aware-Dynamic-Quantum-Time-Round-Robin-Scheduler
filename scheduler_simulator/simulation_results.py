"""Combine existing simulation data into a detached JSON-compatible result."""
from .scheduler_base import SchedulerBase
from .task_definition import TaskDefinition
from .simulator_task_generator import SimulatorTaskGenerator

from copy import deepcopy
from dataclasses import asdict


def build_simulation_results(simulator) -> dict:
    generator: SimulatorTaskGenerator = simulator.task_generator
    scheduler: SchedulerBase = simulator.scheduler
    cycles = [] if scheduler is None else list(scheduler.get_completed_task_cycles())

    return deepcopy({
        "scheduler": None if scheduler is None else {
            "name": scheduler.name,
            "configuration": scheduler.get_configuration(),
        },
        "task_definitions": [] if generator is None else [
            asdict(task) for task in generator.task_definitions
        ],
        "task_cycles": [
            {
                "task_name": cycle.task_name,
                "cycle_number": cycle.cycle_number,
                "arrival_time": cycle.arrival_time,
                "remaining_burst_time": cycle.remaining_burst_time,
                "start_time": None if cycle.start_time == -1 else cycle.start_time,
                "end_time": None if cycle.end_time == -1 else cycle.end_time,
                "execution_intervals": [
                    {"start_time": start, "end_time": end}
                    for start, end in cycle.exec_timeline
                ],
            }
            for cycle in cycles
        ],
        "idle_intervals": [] if scheduler is None else [
            {"start_time": start, "end_time": end}
            for start, end in scheduler.get_idle_times()
        ],
    })
