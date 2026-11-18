"""Metrics use expected arrival time; no eligibility adjustment is applied."""

from math import isclose, isfinite


_TIME_METRICS = ("turnaround_time", "response_time", "waiting_time")


def _time(value, field):
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not isfinite(value) or value < 0):
        raise ValueError(f"{field} must be a non-negative finite number.")
    return value


def _averages(totals, count):
    return {f"average_{name}": totals[name] / count if count else None
            for name in _TIME_METRICS}


def calculate_metrics(results: dict) -> dict:
    """Return overall, per-task, and per-cycle metrics without modifying results.

    Turnaround = completion - expected arrival.
    Response = first execution - expected arrival.
    Waiting = turnaround - actual execution duration.
    Context switches count changes between (task name, cycle number) identities
    and transitions to/from idle. First dispatch and contiguous intervals of the
    same cycle do not count.
    Empty inputs have zero switches and None for undefined averages.
    """
    if not isinstance(results, dict) or not isinstance(results.get("task_cycles"), list):
        raise ValueError("results must contain a task_cycles list.")
    definitions = results.get("task_definitions", [])
    if not isinstance(definitions, list):
        raise ValueError("task_definitions must be a list.")
    deadlines = {}
    for definition in definitions:
        if not isinstance(definition, dict):
            raise ValueError("Task definitions must be dictionaries.")
        name = definition.get("name")
        if not isinstance(name, str) or not name.strip() or name in deadlines:
            raise ValueError("Task definitions need unique non-empty names.")
        period = _time(definition.get("period"), "period")
        burst = _time(definition.get("burst_time"), "burst_time")
        if burst <= 0:
            raise ValueError("burst_time must be positive.")
        deadlines[name] = period if period > 0 else burst
    missed_count, miss_total = 0, 0
    timeline, identities, grouped = [], set(), {}
    totals = dict.fromkeys(_TIME_METRICS, 0)
    count = 0
    per_cycle = []
    for cycle in results["task_cycles"]:
        if not isinstance(cycle, dict):
            raise ValueError("Each task cycle must be a dictionary.")
        name, number = cycle.get("task_name"), cycle.get("cycle_number")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("task_name must be a non-empty string.")
        if isinstance(number, bool) or not isinstance(number, int) or number < 0:
            raise ValueError("cycle_number must be a non-negative integer.")
        if (name, number) in identities:
            raise ValueError(f"Duplicate cycle: {name}, {number}.")
        identities.add((name, number))
        arrival = _time(cycle.get("arrival_time"), "arrival_time")
        start = _time(cycle.get("start_time"), "start_time")
        end = _time(cycle.get("end_time"), "end_time")
        if cycle.get("remaining_burst_time", 0) != 0:
            raise ValueError("Metrics require completed cycles.")
        intervals = cycle.get("execution_intervals")
        if not isinstance(intervals, list) or not intervals:
            raise ValueError("Completed cycles must have execution_intervals.")
        execution = []
        for interval in intervals:
            if not isinstance(interval, dict):
                raise ValueError("Execution intervals must be dictionaries.")
            a = _time(interval.get("start_time"), "interval start_time")
            b = _time(interval.get("end_time"), "interval end_time")
            if b <= a:
                raise ValueError("Execution intervals must have positive duration.")
            execution.append((a, b))
        execution.sort()
        if start != execution[0][0] or end != execution[-1][1] or start < arrival:
            raise ValueError("Cycle start/end/arrival times do not match its execution timeline.")
        if any(right[0] < left[1] for left, right in zip(execution, execution[1:])):
            raise ValueError("Execution intervals overlap within a cycle.")
        actual = sum(b - a for a, b in execution)
        waiting = end - arrival - actual
        if waiting < 0 and isclose(waiting, 0, abs_tol=1e-9):
            waiting = 0
        if waiting < 0:
            raise ValueError("Actual execution exceeds turnaround time.")
        values = {"turnaround_time": end - arrival,
                  "response_time": start - arrival, "waiting_time": waiting}
        if name not in deadlines:
            raise ValueError(f"Missing task definition for {name}.")
        deadline = arrival + deadlines[name]
        miss_time = max(0, end - deadline)
        missed = end > deadline
        missed_count += int(missed)
        miss_total += miss_time
        per_cycle.append({"task_name": name, "cycle_number": number, **values,
                          "deadline": deadline, "deadline_missed": missed,
                          "deadline_miss_time": miss_time})
        task = grouped.setdefault(name, {"cycle_count": 0, **dict.fromkeys(_TIME_METRICS, 0)})
        task["deadline_miss_count"] = task.get("deadline_miss_count", 0) + int(missed)
        task["deadline_miss_total"] = task.get("deadline_miss_total", 0) + miss_time
        task["cycle_count"] += 1
        count += 1
        for metric, value in values.items():
            task[metric] += value
            totals[metric] += value
        timeline.extend((a, b, (name, number)) for a, b in execution)
    idle_intervals = results.get("idle_intervals", [])
    if not isinstance(idle_intervals, list):
        raise ValueError("idle_intervals must be a list.")
    for interval in idle_intervals:
        if not isinstance(interval, dict):
            raise ValueError("Idle intervals must be dictionaries.")
        a = _time(interval.get("start_time"), "idle start_time")
        b = _time(interval.get("end_time"), "idle end_time")
        if b <= a:
            raise ValueError("Idle intervals must have positive duration.")
        timeline.append((a, b, None))
    timeline.sort(key=lambda interval: (interval[0], interval[1]))
    # A CPU gap is idle even if a producer omitted explicit idle records.
    switches = int(bool(timeline) and timeline[0][0] > 0 and timeline[0][2] is not None)
    for previous, current in zip(timeline, timeline[1:]):
        if current[0] < previous[1]:
            raise ValueError("Execution intervals overlap on the single CPU.")
        if current[0] > previous[1]:
            switches += int(previous[2] is not None) + int(current[2] is not None)
        elif current[2] != previous[2]:
            switches += 1
    return {
        "overall": {"cycle_count": count, "context_switch_count": switches,
                    **_averages(totals, count), "deadline_miss_count": missed_count,
                    "average_deadline_miss_time": miss_total / missed_count if missed_count else 0},
        "per_task": [{"task_name": name, "cycle_count": items["cycle_count"],
                      **_averages(items, items["cycle_count"]),
                      "deadline_miss_count": items["deadline_miss_count"],
                      "average_deadline_miss_time": (items["deadline_miss_total"] / items["deadline_miss_count"]
                                                     if items["deadline_miss_count"] else 0)}
                     for name, items in sorted(grouped.items())],
        "per_cycle": sorted(per_cycle, key=lambda item: (item["task_name"], item["cycle_number"])),
    }
