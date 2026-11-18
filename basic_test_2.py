from algorithms import RoundRobinScheduler, HADQRRScheduler
from metrics import calculate_metrics
from scheduler_simulator import Simulator, TaskDefinition

import json

task_a = TaskDefinition(name="A", arrival_time=0, burst_time=5, actual_burst_times=[5, 5, 5], period=10, cycle_count=3)
task_b = TaskDefinition(name="B", arrival_time=0, burst_time=3, actual_burst_times=[3, 3], period=6, cycle_count=2)
task_c = TaskDefinition(name="C", arrival_time=5, burst_time=4, actual_burst_times=[2, 2, 2], period=12, cycle_count=3)


scheduler_1 = RoundRobinScheduler(time_quantum=2)
scheduler_2 = HADQRRScheduler(default_time_quantum=2, history_length=2)


schesd = [scheduler_1,
    scheduler_2
]

simulator = Simulator()

simulator.load_task_definitions([task_a, task_b, task_c])

output_folder = "simulation_results"
# create the output folder if it doesn't exist
import os
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

for scheduler in schesd:
    simulator.set_scheduler(scheduler)
    simulator.run()

    results = simulator.get_results()

    with open(f"{output_folder}/simulation_results_{scheduler.get_name().replace(' ', '_').replace('(', '').replace(')', '').replace('=', '')}.json", "w") as f:
        json.dump(results, f, indent=4)

    metrics_report = calculate_metrics(results)

    with open(f"{output_folder}/simulation_metrics_{scheduler.get_name().replace(' ', '_').replace('(', '').replace(')', '').replace('=', '')}.json", "w") as f:
        json.dump(metrics_report, f, indent=4)