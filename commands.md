
## Generate Test Cases

```bash
python3 generate_cases.py --config config_scenarios/base_all.json --output-dir test_cases --repeats 100
```

## Run All Scenarios

```bash
python3 test_runner.py --input test_cases --schedulers config_schedulers/default.json --output output --multiple
```
## Run One Scenario

```bash
python3 test_runner.py --input test_cases/SCENARIO.json --schedulers config_schedulers/default.json --output output/SCENARIO
```

Scenario JSON files contain `metadata` and numbered `tests`. Scheduler settings
live in `config_schedulers/default.json` under a `schedulers` list. The selected
scheduler file is used for every scenario in a batch. Existing scenario files
with embedded scheduler settings still load, but those embedded settings are
ignored; `--schedulers` is the source used by the runner.

Python usage: `test_runner(input_file, output_folder, schedulers_file)`.
