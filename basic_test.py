from algorithms import RoundRobinScheduler
from scheduler_simulator import Simulator, TaskDefinition

task_a = TaskDefinition(name="A", arrival_time=0, burst_time=5, actual_burst_times=[5, 5, 5], period=10, cycle_count=3)
task_b = TaskDefinition(name="B", arrival_time=0, burst_time=3, actual_burst_times=[3, 3], period=6, cycle_count=2)

scheduler = RoundRobinScheduler(time_quantum=2)

simulator = Simulator()

simulator.load_task_definitions([task_a, task_b])
simulator.set_scheduler(scheduler)

simulator.run()

results = simulator.get_results()

# Save the results to a JSON file
import json
with open("simulation_results.json", "w") as f:
    json.dump(results, f, indent=4)
