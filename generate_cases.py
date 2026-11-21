#!/usr/bin/env python3
"""Deterministic cyclic-task test-case generator for Round Robin schedulers.

No third-party packages required. Outputs the user-defined JSON test schema.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import sys
from pathlib import Path
from typing import Any


DEFAULTS: dict[str, Any] = {
    "profile": "utilization",  # utilization | random | mixed
    "repeats": 1,
    "task_count": 8,
    "cycle_count": 30,
    "simulation_duration": None,  # common release cutoff; overrides cycle_count when set
    "period_mode": "random",  # random | fixed | harmonic | prime | choices
    "period_min": 80,
    "period_max": 240,
    "period_step": 20,
    "base_period": 20,
    "period_fixed": 50,
    "arrival_mode": "zero",  # zero | random | clustered
    "cluster_width": 5,
    "min_burst": 5,  # minimum nominal integer burst
    "utilization_percent": 75,
    "utilization_tolerance_percent": 0.5,
    "weight_distribution": "uniform",  # uniform | bimodal
    "short_fraction": 0.7,
    "long_weight": 5,
    "jitter_percent": 0,
    "random_burst_min": 5,
    "random_burst_max": 30,
    "short_burst_min": 1,
    "short_burst_max": 5,
    "long_burst_min": 20,
    "long_burst_max": 40,
}


def positive_int(value: Any, key: str, allow_zero: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{key} must be an integer, got {value!r}")
    if value < (0 if allow_zero else 1):
        raise ValueError(f"{key} must be {'>= 0' if allow_zero else '> 0'}, got {value}")
    return value


def number(value: Any, key: str, *, minimum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError(f"{key} must be a finite number, got {value!r}")
    if minimum is not None and value < minimum:
        raise ValueError(f"{key} must be >= {minimum}, got {value}")
    return float(value)


def effective_seed(master_seed: int, scenario_id: str, repetition: int) -> int:
    """Do not use Python's hash(): it changes between interpreter processes."""
    payload = json.dumps([master_seed, scenario_id, repetition], ensure_ascii=False, separators=(",", ":"))
    return int.from_bytes(hashlib.sha256(payload.encode("utf-8")).digest()[:8], "big")


def task_name(index: int) -> str:
    """Excel style names: A, B, ..., Z, AA, AB, ..."""
    index += 1
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def prime(n: int) -> bool:
    if n < 2:
        return False
    for i in range(2, math.isqrt(n) + 1):
        if n % i == 0:
            return False
    return True


def periods_available(settings: dict[str, Any]) -> list[int]:
    mode = settings["period_mode"]
    lo = positive_int(settings["period_min"], "period_min")
    hi = positive_int(settings["period_max"], "period_max")
    if lo > hi:
        raise ValueError("period_min must be <= period_max")
    if mode == "fixed":
        return [positive_int(settings["period_fixed"], "period_fixed")]
    if mode == "choices":
        options = settings.get("period_choices")
        if not isinstance(options, list) or not options:
            raise ValueError("period_mode=choices requires nonempty period_choices array")
        return sorted(set(positive_int(x, "period_choices[]") for x in options))
    if mode == "harmonic":
        base = positive_int(settings["base_period"], "base_period")
        choices = []
        p = base
        while p <= hi:
            if p >= lo:
                choices.append(p)
            p *= 2
        if not choices:
            raise ValueError("harmonic periods require base_period * 2^k in period range")
        return choices
    if mode == "prime":
        choices = [p for p in range(lo, hi + 1) if prime(p)]
        if not choices:
            raise ValueError("no prime periods in the selected range")
        return choices
    if mode == "random":
        step = positive_int(settings["period_step"], "period_step")
        return list(range(lo, hi + 1, step))
    raise ValueError(f"unknown period_mode {mode!r}")


def random_task_count(settings: dict[str, Any], rng: random.Random) -> int:
    if "task_count_min" in settings or "task_count_max" in settings:
        lo = positive_int(settings.get("task_count_min", settings["task_count"]), "task_count_min")
        hi = positive_int(settings.get("task_count_max", settings["task_count"]), "task_count_max")
        if lo > hi:
            raise ValueError("task_count_min > task_count_max")
        return rng.randint(lo, hi)
    return positive_int(settings["task_count"], "task_count")


def round_positive_int(value: float) -> int:
    """Round half up to one positive time unit; never emit floats."""
    return max(1, math.floor(value + 0.5))


def utilization_bursts(periods: list[int], settings: dict[str, Any], rng: random.Random) -> list[int]:
    """Assign integer burst times while approximating the requested nominal utilization."""
    minimum = positive_int(settings["min_burst"], "min_burst")
    target = number(settings["utilization_percent"], "utilization_percent", minimum=0.000001) / 100
    tolerance = number(settings["utilization_tolerance_percent"],
                       "utilization_tolerance_percent", minimum=0) / 100
    floor_load = sum(minimum / p for p in periods)
    if floor_load > target + tolerance:
        raise ValueError(
            f"minimum integer bursts already produce {floor_load*100:.3f}% load, above "
            f"requested {target*100:.3f}%; increase period or lower task_count/min_burst"
        )

    mode = settings["weight_distribution"]
    if mode == "uniform":
        weights = [rng.uniform(0.5, 1.5) for _ in periods]
    elif mode == "bimodal":
        short_fraction = number(settings["short_fraction"], "short_fraction", minimum=0)
        if short_fraction > 1:
            raise ValueError("short_fraction must be <= 1")
        long_weight = number(settings["long_weight"], "long_weight", minimum=0.001)
        count_short = min(len(periods), max(0, round(len(periods) * short_fraction)))
        labels = [1.0] * count_short + [long_weight] * (len(periods) - count_short)
        rng.shuffle(labels)
        weights = [v * rng.uniform(0.85, 1.15) for v in labels]
    else:
        raise ValueError(f"unknown weight_distribution {mode!r}")

    remaining = max(0.0, target - floor_load)
    weight_sum = sum(weights)
    raw = [minimum + remaining * weight / weight_sum * p
           for weight, p in zip(weights, periods)]
    bursts = [max(minimum, math.floor(x + 0.5)) for x in raw]
    actual = sum(b / p for b, p in zip(bursts, periods))

    # Greedy integer correction, deterministic tie-breaking by task index.
    for _ in range(100000):
        if abs(actual - target) <= tolerance + 1e-12:
            break
        best_i = None
        best_error = abs(actual - target)
        direction = 1 if actual < target else -1
        for i, p in enumerate(periods):
            if direction < 0 and bursts[i] <= minimum:
                continue
            candidate_error = abs(actual + direction / p - target)
            if candidate_error < best_error - 1e-12:
                best_i, best_error = i, candidate_error
        if best_i is None:
            break
        bursts[best_i] += direction
        actual += direction / periods[best_i]

    if abs(actual - target) > tolerance + 1e-9:
        raise ValueError(
            f"Unable to represent {target*100:.3f}% utilization with whole time units "
            f"for periods={periods}; achieved {actual*100:.3f}%. "
            "Increase utilization_tolerance_percent, period values or task_count."
        )
    return bursts


def random_bursts(n: int, settings: dict[str, Any], rng: random.Random) -> list[int | float]:
    lo = positive_int(settings["random_burst_min"], "random_burst_min")
    hi = positive_int(settings["random_burst_max"], "random_burst_max")
    if lo > hi:
        raise ValueError("random_burst_min > random_burst_max")
    return [rng.randint(lo, hi) for _ in range(n)]


def mixed_bursts(n: int, settings: dict[str, Any], rng: random.Random) -> list[int | float]:
    fraction = number(settings["short_fraction"], "short_fraction", minimum=0)
    if fraction > 1:
        raise ValueError("short_fraction must be <= 1")
    short_min = positive_int(settings["short_burst_min"], "short_burst_min")
    short_max = positive_int(settings["short_burst_max"], "short_burst_max")
    long_min = positive_int(settings["long_burst_min"], "long_burst_min")
    long_max = positive_int(settings["long_burst_max"], "long_burst_max")
    if short_min > short_max or long_min > long_max:
        raise ValueError("mixed burst minimum must be <= maximum")
    flags = [True] * round(n * fraction) + [False] * (n - round(n * fraction))
    rng.shuffle(flags)
    return [rng.randint(short_min, short_max) if short else rng.randint(long_min, long_max) for short in flags]


def arrival_offset(period: int, settings: dict[str, Any], rng: random.Random) -> int:
    mode = settings["arrival_mode"]
    if mode == "zero":
        return 0
    if mode == "random":
        return rng.randrange(period)
    if mode == "clustered":
        width = positive_int(settings["cluster_width"], "cluster_width", allow_zero=True)
        return rng.randint(0, min(width, period - 1))
    raise ValueError(f"unknown arrival_mode {mode!r}")


def phase_multiplier(release_time: int, settings: dict[str, Any]) -> float:
    phases = settings.get("load_phases")
    if phases is None:
        return 1.0
    if not isinstance(phases, list) or not phases:
        raise ValueError("load_phases must be a nonempty list")
    last_until = -1
    for index, phase in enumerate(phases):
        if not isinstance(phase, dict) or "multiplier" not in phase:
            raise ValueError("every load phase must have multiplier")
        mult = number(phase["multiplier"], "load_phases[].multiplier", minimum=0.000001)
        until = phase.get("until")
        if until is None:
            if index != len(phases) - 1:
                raise ValueError("only final load phase may omit until")
            return mult
        if not isinstance(until, int) or until <= last_until:
            raise ValueError("load_phases[].until must be increasing positive integers")
        last_until = until
        if release_time < until:
            return mult
    raise ValueError("last load phase must not have until")


def actual_bursts(base: int, arrival: int, period: int, cycle_count: int,
                  settings: dict[str, Any], rng: random.Random) -> list[int]:
    """Generate integer bursts. Jitter is a MAXIMUM, not a fixed deviation.

    For each cycle, independently sample a whole-number burst in the interval
    [ceil(rounded_phase_burst * (1-jitter)),
     floor(rounded_phase_burst * (1+jitter))].
    This prevents rounding from exceeding the configured relative limit.
    E.g. base=10 and jitter_percent=20 -> any integer from 8 to 12.
    When integer quantization leaves only one admissible value, that cycle
    necessarily has zero variation (e.g. base=2, jitter=20%).
    """
    jitter = number(settings["jitter_percent"], "jitter_percent", minimum=0)
    if jitter >= 100:
        raise ValueError("jitter_percent must be < 100 (bursts must stay positive)")
    multipliers = settings.get("cycle_multipliers")
    if multipliers is not None:
        if "load_phases" in settings:
            raise ValueError("choose cycle_multipliers OR load_phases, not both")
        if not isinstance(multipliers, list) or len(multipliers) != cycle_count:
            raise ValueError("cycle_multipliers length must equal cycle_count")

    result: list[int] = []
    for cycle in range(cycle_count):
        if multipliers is not None:
            mult = number(multipliers[cycle], "cycle_multipliers[]", minimum=0.000001)
        else:
            mult = phase_multiplier(arrival + cycle * period, settings)
        reference = round_positive_int(base * mult)
        if jitter == 0:
            result.append(reference)
            continue

        min_allowed = max(1, math.ceil(reference * (1.0 - jitter / 100) - 1e-10))
        max_allowed = math.floor(reference * (1.0 + jitter / 100) + 1e-10)
        result.append(rng.randint(min_allowed, max_allowed))
    return result


def validate_settings(s: dict[str, Any]) -> None:
    # Reject old fractional precision inputs rather than silently accepting floats.
    for legacy in ("burst_precision", "actual_burst_precision"):
        if legacy in s and s[legacy] not in (None, 0):
            raise ValueError(f"{legacy} must be 0 or omitted: all bursts are integer time units")
    positive_int(s["min_burst"], "min_burst")
    positive_int(s["cycle_count"], "cycle_count")
    if s["simulation_duration"] is not None:
        positive_int(s["simulation_duration"], "simulation_duration")
    positive_int(s["repeats"], "repeats")
    number(s["jitter_percent"], "jitter_percent", minimum=0)
    if s["jitter_percent"] >= 100:
        raise ValueError("jitter_percent must be < 100")
    if s["profile"] not in {"utilization", "random", "mixed"}:
        raise ValueError(f"unknown profile {s['profile']!r}")
    periods_available(s)


def generate_test(settings: dict[str, Any], base_rng: random.Random,
                  arrival_rng: random.Random, actual_rng: random.Random) -> dict[str, Any]:
    validate_settings(settings)
    n = random_task_count(settings, base_rng)
    cycle_count = settings["cycle_count"]
    choices = periods_available(settings)
    periods = [base_rng.choice(choices) for _ in range(n)]

    profile = settings["profile"]
    if profile == "utilization":
        bursts = utilization_bursts(periods, settings, base_rng)
    elif profile == "random":
        bursts = random_bursts(n, settings, base_rng)
    else:
        bursts = mixed_bursts(n, settings, base_rng)

    tasks = []
    for i, (p, burst) in enumerate(zip(periods, bursts)):
        arrival = arrival_offset(p, settings, arrival_rng)
        cutoff = settings["simulation_duration"]
        task_cycle_count = cycle_count if cutoff is None else max(0, (cutoff - 1 - arrival) // p + 1)
        if task_cycle_count == 0:
            raise ValueError(f"task {task_name(i)} has no releases before simulation_duration; increase cutoff")
        task = {
            "name": task_name(i),
            "arrival_time": arrival,
            "burst_time": burst,
            "actual_burst_times": actual_bursts(burst, arrival, p, task_cycle_count, settings, actual_rng),
            "period": p,
            "cycle_count": task_cycle_count,
        }
        tasks.append(task)
    return {"tasks": tasks}


def manifest_info(test: dict[str, Any], scenario: str, repeat: int, derived_seed: int,
                  workload_group: str | None) -> dict[str, Any]:
    tasks = test["tasks"]
    nominal_u = sum(t["burst_time"] / t["period"] for t in tasks) * 100
    avg_demand = sum((sum(t["actual_burst_times"]) / t["cycle_count"]) / t["period"] for t in tasks) * 100
    return {
        "test_number": test["number"],
        "scenario": scenario,
        "repeat_index": repeat,
        "base_task_seed": derived_seed,
        "workload_group": workload_group,
        "task_count": len(tasks),
        "total_cycles": sum(t["cycle_count"] for t in tasks),
        "nominal_utilization_percent": round(nominal_u, 6),
        "mean_cycle_demand_percent": round(avg_demand, 6),
    }


def build(config: dict[str, Any], override_seed: int | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    seed = override_seed if override_seed is not None else config.get("seed", 42)
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    metadata = config.get("metadata")
    if not isinstance(metadata, dict) or not all(isinstance(metadata.get(k), str) for k in ("name", "description")):
        raise ValueError("metadata requires name and description strings")
    schedulers = config.get("schedulers")
    if not isinstance(schedulers, list) or not schedulers:
        raise ValueError("schedulers must be a nonempty list")
    scenarios = config.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError("scenarios must be a nonempty list")
    defaults = config.get("defaults", {})
    if not isinstance(defaults, dict):
        raise ValueError("defaults must be an object")

    result = {"metadata": {"name": metadata["name"], "description": metadata["description"]},
              "schedulers": schedulers, "tests": []}
    manifest = {"seed": seed, "tests": []}
    used_ids: set[str] = set()
    # Each repetition in a workload group must have a distinct NOMINAL task set.
    # Paired scenarios sharing workload_group intentionally reuse the same one.
    chosen_base_seeds: dict[tuple[str, int], int] = {}
    seen_base_workloads: dict[str, set[tuple[tuple[int, int], ...]]] = {}
    for raw in scenarios:
        if not isinstance(raw, dict):
            raise ValueError("each scenario must be an object")
        scenario_id = raw.get("id")
        if not isinstance(scenario_id, str) or not scenario_id:
            raise ValueError("each scenario must have a unique, nonempty string id")
        if scenario_id in used_ids:
            raise ValueError(f"duplicate scenario id: {scenario_id}")
        used_ids.add(scenario_id)
        settings = {**DEFAULTS, **defaults, **{k: v for k, v in raw.items() if k != "id"}}
        validate_settings(settings)
        workload_group = settings.get("workload_group")
        if workload_group is not None and (not isinstance(workload_group, str) or not workload_group):
            raise ValueError("workload_group must be a nonempty string when specified")
        for repetition in range(settings["repeats"]):
            # Matching workload_group => identical periods and nominal bursts even when
            # arrival_mode or jitter differs. Those random streams are separate.
            base_key = f"group:{workload_group}" if workload_group else f"scenario:{scenario_id}"
            arrival_seed = effective_seed(seed, f"arrival:{scenario_id}", repetition)
            actual_seed = effective_seed(seed, f"actual:{scenario_id}", repetition)
            pair_key = (base_key, repetition)
            if pair_key in chosen_base_seeds:
                # The companion scenario (e.g. fixed vs jitter) gets the same
                # periods and nominal bursts for its corresponding repetition.
                derived_seed = chosen_base_seeds[pair_key]
                test = generate_test(settings, random.Random(derived_seed),
                                     random.Random(arrival_seed), random.Random(actual_seed))
            else:
                seen = seen_base_workloads.setdefault(base_key, set())
                for attempt in range(1000):
                    retry_key = base_key if attempt == 0 else f"{base_key}:retry:{attempt}"
                    derived_seed = effective_seed(seed, retry_key, repetition)
                    test = generate_test(settings, random.Random(derived_seed),
                                         random.Random(arrival_seed), random.Random(actual_seed))
                    signature = tuple((t["period"], t["burst_time"]) for t in test["tasks"])
                    if signature not in seen:
                        seen.add(signature)
                        chosen_base_seeds[pair_key] = derived_seed
                        break
                else:
                    raise ValueError(
                        f"Cannot generate distinct nominal task sets for scenario {scenario_id!r} "
                        f"at repeat {repetition + 1}; increase period/burst variability "
                        "or reduce repeats."
                    )
            test["number"] = len(result["tests"]) + 1
            # Preserve exact field order from the example: number, then tasks.
            test = {"number": test["number"], "tasks": test["tasks"]}
            result["tests"].append(test)
            manifest["tests"].append(manifest_info(test, scenario_id, repetition, derived_seed, workload_group))
    return result, manifest



def write_scenario_output(
    generated: dict[str, Any],
    manifest: dict[str, Any],
    output_dir: Path,
    manifest_path: Path | None = None,
) -> list[Path]:
    """Write ONE simulator configuration per scenario, with ALL repeats in `tests`.

    Example: output_dir/util75_fixed.json with tests numbered 1, 2, ..., repeats.
    All configured schedulers appear once at the top of each scenario file.
    """
    if len(generated["tests"]) != len(manifest["tests"]):
        raise ValueError("generated tests and manifest have different lengths")

    # Validate names and build all output payloads before writing any files.
    grouped: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = {}
    for test, info in zip(generated["tests"], manifest["tests"]):
        scenario_id = info["scenario"]
        if re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]*", scenario_id) is None:
            raise ValueError(
                f"scenario id {scenario_id!r} cannot be used as an output filename; "
                "use letters, digits, underscores, or dashes"
            )
        grouped.setdefault(scenario_id, []).append((test, info))

    planned: list[tuple[Path, dict[str, Any]]] = []
    for scenario_id, entries in grouped.items():
        # Stable numbering within each scenario, independent from the combined output.
        scenario_tests = []
        for test, info in entries:
            local_number = len(scenario_tests) + 1
            scenario_tests.append({"number": local_number, "tasks": test["tasks"]})
            info["file"] = f"{scenario_id}.json"
            info["simulator_test_number"] = local_number
        scenario_config = {
            "metadata": {
                "name": f"{generated['metadata']['name']} | {scenario_id}",
                "description": generated["metadata"]["description"],
            },
            "schedulers": generated["schedulers"],
            "tests": scenario_tests,
        }
        planned.append((output_dir / f"{scenario_id}.json", scenario_config))

    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for destination, scenario_config in planned:
        destination.write_text(
            json.dumps(scenario_config, indent=4, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        written.append(destination)

    sidecar = manifest_path if manifest_path is not None else output_dir / "manifest.json"
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    sidecar.write_text(json.dumps(manifest, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")
    return written


# Backward-compatible Python API alias (the output semantics are now per scenario).
write_split_output = write_scenario_output


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate reproducible cyclic scheduler test JSON.")
    ap.add_argument("--config", "-c", type=Path, required=True, help="Generator configuration JSON")
    destination = ap.add_mutually_exclusive_group(required=True)
    destination.add_argument("--output", "-o", type=Path, help="Single combined JSON (legacy behavior)")
    destination.add_argument("--output-dir", "-d", type=Path, help="One simulator-ready JSON per scenario; all repeats inside tests[]")
    ap.add_argument("--seed", type=int, help="Override the config seed")
    ap.add_argument("--manifest", type=Path, help="Optional sidecar manifest of utilization and derived seeds")
    ap.add_argument("--only", help="Comma-separated scenario IDs to generate (e.g. util75_fixed,util75_jitter)")
    ap.add_argument("--repeats", type=int, help="Override repeats for all selected scenarios")
    args = ap.parse_args()
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        if args.only:
            requested = set(x.strip() for x in args.only.split(","))
            if "" in requested:
                raise ValueError("--only requires nonempty comma-separated scenario IDs")
            known = {s["id"] for s in config["scenarios"]}
            if requested - known:
                raise ValueError(f"unknown --only scenario IDs: {sorted(requested - known)}")
            config["scenarios"] = [s for s in config["scenarios"] if s["id"] in requested]
        if args.repeats is not None:
            positive_int(args.repeats, "--repeats")
            config["scenarios"] = [{**s, "repeats": args.repeats} for s in config["scenarios"]]
        generated, manifest = build(config, args.seed)
        if args.output_dir:
            written = write_scenario_output(generated, manifest, args.output_dir, args.manifest)
            print(f"Wrote {len(written)} scenario configs ({len(generated['tests'])} total tests) to: {args.output_dir}")
            print(f"Manifest: {args.manifest or args.output_dir / 'manifest.json'}")
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(generated, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")
            if args.manifest:
                args.manifest.parent.mkdir(parents=True, exist_ok=True)
                args.manifest.write_text(json.dumps(manifest, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"Combined output: {args.output}")
            if args.manifest:
                print(f"Manifest: {args.manifest}")
        print(f"Generated {len(generated['tests'])} cyclic tests ({sum(len(t['tasks']) for t in generated['tests'])} task definitions).")
        print(f"Master seed: {manifest['seed']}")
        return 0
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
