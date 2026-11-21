"""Metrics use expected arrival time; no eligibility adjustment is applied."""

from copy import deepcopy
from math import isclose, isfinite
from statistics import mean, median, pstdev


_TIME_METRICS = ("turnaround_time", "response_time", "waiting_time")
_AVERAGED_METRICS = (*_TIME_METRICS, "slowdown")


def _time(value, field):
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not isfinite(value) or value < 0):
        raise ValueError(f"{field} must be a non-negative finite number.")
    return value


def _averages(totals, count):
    return {f"average_{name}": totals[name] / count if count else None
            for name in _AVERAGED_METRICS}


def _statistics(values):
    """Population statistics; P95 interpolates at index (n - 1) * 0.95."""
    values = sorted(values)
    count = len(values)
    if not count:
        return {"count": 0, **dict.fromkeys(("mean", "min", "max", "median", "std_dev", "p95"))}
    position = (count - 1) * 0.95
    lower = int(position)
    upper = min(lower + 1, count - 1)
    p95 = values[lower] + (values[upper] - values[lower]) * (position - lower)
    return {"count": count, "mean": mean(values), "min": values[0], "max": values[-1],
            "median": median(values), "std_dev": pstdev(values), "p95": p95}


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
    totals = dict.fromkeys(_AVERAGED_METRICS, 0)
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
                  "response_time": start - arrival, "waiting_time": waiting,
                  "slowdown": (end - arrival) / actual}
        longest_wait = max([start - arrival] +
                           [right[0] - left[1] for left, right in zip(execution, execution[1:])])
        if name not in deadlines:
            raise ValueError(f"Missing task definition for {name}.")
        deadline = arrival + deadlines[name]
        miss_time = max(0, end - deadline)
        missed = end > deadline
        missed_count += int(missed)
        miss_total += miss_time
        per_cycle.append({"task_name": name, "cycle_number": number, **values,
                          "maximum_continuous_waiting_time": longest_wait,
                          "deadline": deadline, "deadline_missed": missed,
                          "deadline_miss_time": miss_time})
        task = grouped.setdefault(name, {"cycle_count": 0, **dict.fromkeys(_AVERAGED_METRICS, 0)})
        task["deadline_miss_count"] = task.get("deadline_miss_count", 0) + int(missed)
        task["deadline_miss_total"] = task.get("deadline_miss_total", 0) + miss_time
        task["maximum_continuous_waiting_time"] = max(
            task.get("maximum_continuous_waiting_time", 0), longest_wait)
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
    continuous_waiting = _statistics(c["maximum_continuous_waiting_time"] for c in per_cycle)
    slowdown = _statistics(c["slowdown"] for c in per_cycle)
    tardiness = _statistics(c["deadline_miss_time"] for c in per_cycle)
    normalized_tardiness = _statistics(
        c["deadline_miss_time"] / deadlines[c["task_name"]] for c in per_cycle)
    return {
        **{key: deepcopy(results[key]) for key in ("metadata", "test_number") if key in results},
        "scheduler": deepcopy(results.get("scheduler")),
        "task_input_hash": results.get("task_input_hash"),
        "overall": {"cycle_count": count, "context_switch_count": switches,
                    "p95_slowdown": slowdown["p95"],
                    "maximum_continuous_waiting_time": continuous_waiting["max"],
                    **_averages(totals, count), "deadline_miss_count": missed_count,
                    "average_deadline_miss_time": miss_total / missed_count if missed_count else 0,
                    "mean_tardiness_missed_cycles": miss_total / missed_count if missed_count else 0,
                    "mean_tardiness_all_cycles": tardiness["mean"],
                    "p95_tardiness_all_cycles": tardiness["p95"],
                    "maximum_tardiness": tardiness["max"],
                    "mean_normalized_tardiness": normalized_tardiness["mean"],
                    "deadline_miss_rate": 100 * missed_count / count if count else 0,
                    "context_switches_per_cycle": switches / count if count else None,
                    "statistics": {
                        "maximum_continuous_waiting_time": continuous_waiting,
                        "tardiness_all_cycles": tardiness,
                        "normalized_tardiness": normalized_tardiness,
                        **{name: _statistics(c[name] for c in per_cycle) for name in _AVERAGED_METRICS},
                        "deadline_miss_time": _statistics(c["deadline_miss_time"] for c in per_cycle
                                                          if c["deadline_missed"]),
                    }},
        "per_task": [{"task_name": name, "cycle_count": items["cycle_count"],
                      **_averages(items, items["cycle_count"]),
                      "maximum_continuous_waiting_time": items["maximum_continuous_waiting_time"],
                      "deadline_miss_count": items["deadline_miss_count"],
                      "average_deadline_miss_time": (items["deadline_miss_total"] / items["deadline_miss_count"]
                                                     if items["deadline_miss_count"] else 0)}
                     for name, items in sorted(grouped.items())],
        "per_cycle": sorted(per_cycle, key=lambda item: (item["task_name"], item["cycle_number"])),
    }
