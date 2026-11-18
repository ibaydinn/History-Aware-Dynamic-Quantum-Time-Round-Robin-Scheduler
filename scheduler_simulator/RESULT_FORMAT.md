# Simulation results

`Simulator.get_results()` returns a detached dictionary with four sections:

- `scheduler`: name and configuration, or `null` when no scheduler is attached.
- `task_definitions`: input definitions, including requested `burst_time` and `actual_burst_times`.
- `task_cycles`: completed cycles in completion order. Each contains its task name, cycle number, arrival time, remaining burst, start/end, and execution intervals.
- `idle_intervals`: scheduler-recorded idle start/end times.

Call `get_results()` after `run()` finishes. Cycle numbers start at zero. `arrival_time` is the scheduled arrival. Intervals are `[start_time, end_time)`. In-flight cycles are internal generator state and are not exported.

The result is assembled from existing objects. No separate event history or per-step log is maintained. Callbacks and internal generator state are excluded. Eligibility and actual generation timestamps are not exported.

Results can be serialized with `json.dumps(result, indent=2, allow_nan=False)`. They remain independent of subsequent execution, edits to the returned dictionary, and resets. Saving, metrics, and visualization belong to later modules.
