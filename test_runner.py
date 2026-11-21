from metrics import calculate_metrics
from scheduler_simulator import Simulator
from scheduler_simulator.task_definition import create_task_from_json
from pathlib import Path
import re
from algorithms import create_scheduler_from_config

import json
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description="Run scheduling simulations with different algorithms.")
    parser.add_argument("--input", type=str, required=True, help="Path to the input JSON file containing task definitions.")
    parser.add_argument("--output", type=str, required=True, help="Path to the output folder where results and metrics will be saved.")
    return parser.parse_args()

def test_runner(input_file: str, output_folder: str) -> None:
    with open(input_file, "r", encoding="utf-8") as f:
        test_data = json.load(f)
    if not isinstance(test_data, dict):
        raise ValueError("Input must be a JSON object.")
    for key in ("schedulers", "tests"):
        if not isinstance(test_data.get(key), list) or not test_data[key]:
            raise ValueError(f"{key} must be a non-empty list.")

    metadata = test_data.get("metadata", {})
    if not isinstance(metadata, dict):
        raise ValueError("metadata must be a JSON object.")

    schedulers = [create_scheduler_from_config(config) for config in test_data["schedulers"]]
    # The index distinguishes configurations even if their names sanitize identically.
    filenames = []
    for index, (config, scheduler) in enumerate(zip(test_data["schedulers"], schedulers), 1):
        label = config.get("name", scheduler.get_name())
        slug = re.sub(r"[^A-Za-z0-9_-]+", "_", label).strip("_")[:80] or "scheduler"
        filenames.append(f"{index:03d}_{slug}")

    tests = test_data["tests"]
    numbers = set()
    for index, test in enumerate(tests, 1):
        if not isinstance(test, dict) or not isinstance(test.get("tasks"), list):
            raise ValueError(f"Test {index} must contain a tasks list.")
        number = test.get("number")
        if type(number) is not int or number < 1 or number in numbers:
            raise ValueError("Each test needs a unique positive integer number.")
        numbers.add(number)

    print(f"Loaded {len(tests)} tests and {len(schedulers)} schedulers from {input_file}.")
    for index, test in enumerate(tests, 1):
        number = test["number"]
        print(f"Running test {number} ({index}/{len(tests)})")
        definitions = [create_task_from_json(task) for task in test["tasks"]]
        simulator = Simulator()
        simulator.load_task_definitions(definitions)
        folder = Path(output_folder) / str(number)
        folder.mkdir(parents=True, exist_ok=True)
        for scheduler, filename in zip(schedulers, filenames):
            print(f"  Using scheduler: {scheduler.get_name()}")
            simulator.set_scheduler(scheduler)
            simulator.run()
            results = simulator.get_results()
            results["metadata"] = metadata
            results["test_number"] = number
            metrics_report = calculate_metrics(results)
            for kind, data in (("results", results), ("metrics", metrics_report)):
                with (folder / f"{filename}_{kind}.json").open("w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False, allow_nan=False)


def main():
    # Parse command-line arguments
    args = parse_arguments()

    # Run the test runner with the provided input and output paths
    test_runner(args.input, args.output)


if __name__ == "__main__":
    main()