# Simulation metrics

All delays use **expected arrival** (`task_cycles[].arrival_time`). No eligibility or
generator-delay correction is applied. Waiting time therefore includes any delay
caused by the preceding cycle.

- Turnaround time = `end_time - arrival_time`.
- Response time = `start_time - arrival_time` (time until first execution).
- Waiting time = turnaround minus the sum of execution-interval durations.
  This uses actual CPU execution, not the requested `burst_time`.
- Context-switch count = changes between `(task_name, cycle_number)` identities
  plus cycle-to-idle and idle-to-cycle transitions in the chronological CPU timeline.
  Switching from one cycle to another counts even for the same task without an idle gap.
  Consecutive intervals of the same cycle do not count unless an idle interval
  separates them (two switches).
  Idle-to-idle does not count. The first dispatch at time zero does not count;
  an initial idle period followed by a task counts once. Gaps are treated as idle,
  including the gap from time zero to the first recorded interval. No terminal
  idle transition is invented after the final recorded interval. Explicit trailing
  idle does count. This is a transition count, not a measurement of switching cost.

## Python

```python
from metrics import calculate_metrics

simulator.run()
report = calculate_metrics(simulator.get_results())
print(report["overall"])
print(report["per_task"])
print(report["per_cycle"])
```

The calculator does not mutate the input or depend on a scheduling algorithm.
`overall` provides cycle count, context-switch count, and mean turnaround/response/
waiting times. `per_task` provides cycle counts and means. `per_cycle` provides
turnaround, response, and waiting times for each cycle, sorted by task name and cycle number. Overall means weight every cycle equally, not every task equally.
For zero cycles, switch count is zero and averages are `None` (`null` in JSON).

## Command line

From the project root:

```sh
python3 -m metrics outputs/simulation_results.json
python3 tools/calculate_metrics.py outputs/simulation_results.json --per-cycle
python3 -m metrics outputs/simulation_results.json --json
```

Both commands use the same calculator. The input must contain completed cycles
with valid, non-overlapping single-CPU execution intervals. Cycle and interval
list order does not affect the calculations. Times use the simulation's units.

Deadline: expected cycle arrival + period. For period zero, use expected arrival
+ requested `burst_time` (not actual execution duration). Completion exactly at
the deadline is on time; the final cycle also has a deadline.

Metrics include `deadline_miss_count` and `average_deadline_miss_time` overall
and per task. The average includes only missed cycles and is zero if none miss.
Each cycle includes `deadline`, `deadline_missed`, and `deadline_miss_time`.
Task definitions must be present for every completed task.
The viewer shows dashed deadline markers labeled d0, d1, etc.; red markers
with ! indicate misses. Markers are included in SVG and PNG exports.

Reports also preserve `scheduler` (name and configuration) and `task_input_hash`
from the simulation results for comparisons. Missing metadata is represented by
`null`. Open `tools/results_viewer.html` to load multiple saved reports and compare
overall values or percentage improvement against a selected baseline.
