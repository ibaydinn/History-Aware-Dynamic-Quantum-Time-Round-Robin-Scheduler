"""Read a saved simulation JSON and print metrics using the shared calculator."""

import argparse
import json
from pathlib import Path

from .calculator import calculate_metrics


def _format(value):
    return "n/a" if value is None else f"{value:.6g}"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Calculate metrics from expected arrival times.")
    parser.add_argument("input", type=Path, help="Simulation results JSON file")
    parser.add_argument("--json", action="store_true", help="Print the complete metrics dictionary as JSON")
    parser.add_argument("--per-cycle", action="store_true", help="Also print each cycle's metrics")
    args = parser.parse_args(argv)
    try:
        report = calculate_metrics(json.loads(args.input.read_text(encoding="utf-8")))
    except (OSError, ValueError, TypeError) as error:
        parser.exit(1, f"Error: {error}\n")
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False))
        return
    overall = report["overall"]
    print(f"Completed cycles: {overall['cycle_count']}")
    print(f"Context switches: {overall['context_switch_count']} (cycle changes and cycle/idle transitions)")
    for name in ("turnaround_time", "response_time", "waiting_time"):
        print(f"Average {name.replace('_', ' ')}: {_format(overall['average_' + name])}")
    print(f"Deadlines missed: {overall['deadline_miss_count']}")
    print(f"Average deadline miss time (missed cycles): {_format(overall['average_deadline_miss_time'])}")
    print(f"Deadline miss rate: {_format(overall['deadline_miss_rate'])}%")
    print(f"Context switches per cycle: {_format(overall['context_switches_per_cycle'])}")
    print("\nOverall cycle statistics (population std dev; interpolated P95):")
    for name, stats in overall["statistics"].items():
        label = name.replace("_", " ")
        if name == "deadline_miss_time":
            label += " (missed cycles only)"
        values = ", ".join(f"{key}={_format(value)}" for key, value in stats.items())
        print(f"  {label}: {values}")
    print("\nPer task (mean times, in simulation units):")
    for item in report["per_task"]:
        print(f"  {item['task_name']}: cycles={item['cycle_count']}, "
              f"turnaround={_format(item['average_turnaround_time'])}, "
              f"response={_format(item['average_response_time'])}, "
              f"waiting={_format(item['average_waiting_time'])}, "
              f"deadlines missed={item['deadline_miss_count']}, "
              f"average deadline miss time={_format(item['average_deadline_miss_time'])}")
    if args.per_cycle:
        print("\nPer cycle:")
        for item in report["per_cycle"]:
            print(f"  {item['task_name']} cycle {item['cycle_number']}: "
                  f"turnaround={_format(item['turnaround_time'])}, "
                  f"response={_format(item['response_time'])}, "
                  f"waiting={_format(item['waiting_time'])}, deadline={_format(item['deadline'])}, "
                  f"deadline miss time={_format(item['deadline_miss_time'])}")
