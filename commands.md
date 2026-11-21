
## Generate Test Cases

```bash
python3 generate_cases.py --config config_scenarios/base_all.json --output-dir test_cases --repeats 100
````

## Run All Scenarios

```bash
python3 test_runner.py --input test_cases --output output --multiple
```