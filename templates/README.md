# Topic test files

Each JSON file describes one topic/experimental case:

- `metadata`: topic information, such as `name` and `description`. Additional
  descriptive fields are preserved as provided.
- `schedulers`: configurations to run against every test.
- `tests`: individual workloads belonging to this topic. Each has an explicit `number` and a `tasks` list.
  Numbers must be unique positive integers. Tests execute in array order; the
  supplied number is used for the output folder and report `test_number`.

See `sample_test.json` for a complete example. `metadata` replaces `meta`, and
`tests` replaces `test_cases`.

Run from the repository root:

```sh
python3 test_runner.py --input templates/sample_test.json --output output/burst_variation
```

Use a separate output directory for each topic. Each test gets a numbered subdirectory (`1`, `2`, …),
with separate results and metrics files for each scheduler configuration.
Both files include the topic `metadata` and `test_number`. Existing scheduler
configuration and task input hashes remain available for matching comparisons.
Tests run sequentially, with one simulator created for the current test.

Cross-test averages are not calculated yet. These identities let a later
aggregation module group tests by topic and scheduler configuration without
combining different schedulers or confusing individual test results.
