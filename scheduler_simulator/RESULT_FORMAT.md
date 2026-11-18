# Simulation results

`Simulator.get_results()` returns a detached dictionary with these fields:

- `task_input_hash`: SHA-256 fingerprint of the task definitions, prefixed with `sha256:`; `null` before tasks are loaded.
- `scheduler`: name and configuration, or `null` when no scheduler is attached.
- `task_definitions`: input definitions, including requested `burst_time` and `actual_burst_times`.
- `task_cycles`: completed cycles in completion order. Each contains its task name, cycle number, arrival time, remaining burst, start/end, and execution intervals.
- `idle_intervals`: scheduler-recorded idle start/end times.

Call `get_results()` after `run()` finishes. Cycle numbers start at zero. `arrival_time` is the scheduled arrival. Intervals are `[start_time, end_time)`. In-flight cycles are internal generator state and are not exported.

The result is assembled from existing objects. No separate event history or per-step log is maintained. Callbacks and internal generator state are excluded. Eligibility and actual generation timestamps are not exported.

Results can be serialized with `json.dumps(result, indent=2, allow_nan=False)`. They remain independent of subsequent execution, edits to the returned dictionary, and resets. Saving, metrics, and visualization belong to later modules.

The input hash includes every task-definition field and preserves task order (which
can affect tie-breaking) and actual-burst order. It excludes the scheduler, its
configuration, execution results, and filenames. Identical inputs therefore have
the same hash across schedulers and repeated runs. JSON object-key order and
formatting do not affect it. Explicitly loading an empty task list produces the
hash of `[]`, distinct from the unloaded `null` value.

To verify a saved file, recompute with
`calculate_task_input_hash(result["task_definitions"])` from
`scheduler_simulator.simulation_results` and compare it with `task_input_hash`.
This identifies matching workloads, not matching simulator versions or authenticity.

`scheduler.name` comes from the required `SchedulerBase.get_name()` method. Each
scheduler implements its own display name, for example `Round Robin (q=2)`.
Viewers use this name directly; `configuration` remains separate reproducibility
data and is not automatically added to the displayed name.
