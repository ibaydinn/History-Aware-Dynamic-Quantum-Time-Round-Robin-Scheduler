from metrics import calculate_metrics
from scheduler_simulator import Simulator, TaskDefinition
from algorithms import create_scheduler_from_config

import json
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description="Run scheduling simulations with different algorithms.")
    parser.add_argument("--input", type=str, required=True, help="Path to the input JSON file containing task definitions.")
    parser.add_argument("--output", type=str, required=True, help="Path to the output folder where results and metrics will be saved.")
    return parser.parse_args()

def main():
    args = parse_arguments()

    # Load test from the input JSON file
    with open(args.input, "r") as f:
        test_data = json.load(f)

    # Create output folder if it doesn't exist
    import os
    if not os.path.exists(args.output):
        os.makedirs(args.output)

    # Create Scheduler instances from the loaded JSON data
    schedulers = [create_scheduler_from_config(scheduler) for scheduler in test_data["schedulers"]]

    # Create a Simulator instance
    simulator = Simulator()

    # Load test cases
    test_cases = test_data["test_cases"]

    print(f"Loaded {len(test_cases)} test cases and {len(schedulers)} schedulers from {args.input}.")

    # Run each test case with each scheduler
    for test_case_number, test_case in enumerate(test_cases, start=1):

        test_case_name = test_case["name"]
        print(f"Running {test_case_number}/{len(test_cases)}: {test_case_name}")

        # Create a subfolder for the test case results
        test_case_output_folder = os.path.join(args.output, test_case_name)
        if not os.path.exists(test_case_output_folder):
            os.makedirs(test_case_output_folder)
        
        # Create TaskDefinition instances from the test case data
        task_definitions = [TaskDefinition(**task) for task in test_case["tasks"]]

        # Load task definitions into the simulator
        simulator.load_task_definitions(task_definitions)

        for scheduler in schedulers:
            print(f"  Using scheduler: {scheduler.get_name()}")
            
            # Set the scheduler for the simulator
            simulator.set_scheduler(scheduler)

            # Run the simulation
            simulator.run()

            # Get results and metrics
            results = simulator.get_results()
            metrics_report = calculate_metrics(results)

            # Save results and metrics to JSON files
            scheduler_name = scheduler.get_name().replace(" ", "_").replace("(", "").replace(")", "").replace("=", "")
            output_results_path = f"{args.output}/{test_case['name']}/{scheduler_name}_results.json"
            output_metrics_path = f"{args.output}/{test_case['name']}/{scheduler_name}_metrics.json"

            with open(output_results_path, "w") as f:
                json.dump(results, f, indent=4)

            with open(output_metrics_path, "w") as f:
                json.dump(metrics_report, f, indent=4)

if __name__ == "__main__":
    main()