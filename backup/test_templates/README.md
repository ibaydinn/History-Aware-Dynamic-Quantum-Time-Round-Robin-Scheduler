# Topic test files

Each JSON file describes one topic/experimental case:

- `metadata`: topic information, such as `name` and `description`. Additional
  descriptive fields are preserved as provided.
- `tests`: individual workloads belonging to this topic. Each has an explicit `number` and a `tasks` list.
  Numbers must be unique positive integers. Tests execute in array order; the
  supplied number is used for the output folder and report `test_number`.

See `sample_test.json` for the workloads and `schedulers.json` for the separate
scheduler configurations applied to every test. `metadata` replaces `meta`, and
`tests` replaces `test_cases`.

Run from the repository root:

```sh
python3 test_runner.py --input backup/test_templates/sample_test.json --schedulers backup/test_templates/schedulers.json --output output/burst_variation
```

Use a separate output directory for each topic. Each test gets a numbered subdirectory (`index/1`, `index/2`, …),
with separate results and metrics files for each scheduler configuration.
Both files include the topic `metadata` and `test_number`. Existing scheduler
configuration and task input hashes remain available for matching comparisons.
Tests run sequentially, with one simulator created for the current test.

After all tests complete, `scene_summary/` contains one `*_scene.json` report per
scheduler configuration. Load these reports together in the metric viewer to
compare the entire scene. `overall` averages each metric across tests with equal
weight, including switch/miss counts and rates. `per_test_statistics` describes
variation between tests. Tests with no deadline misses contribute zero to average
lateness. Undefined metrics are excluded, with their sample counts recorded.
