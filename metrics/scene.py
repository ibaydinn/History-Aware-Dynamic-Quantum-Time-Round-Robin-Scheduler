"""Combine completed-test metrics without retaining simulation timelines."""
from copy import deepcopy
import hashlib
import json

from .calculator import _statistics


def aggregate_scene_metrics(reports):
    """Aggregate an iterable of metric reports for one scheduler configuration.

    Every scalar metric is averaged with equal weight per test.
    Undefined values are excluded; zero-miss tests contribute zero lateness.
    """
    scheduler = metadata = None
    tests = {}
    per_test = {}
    for report in reports:
        number = report.get('test_number')
        if type(number) is not int or number < 1 or number in tests:
            raise ValueError('Scene reports require unique positive test numbers.')
        input_hash = report.get('task_input_hash')
        if not isinstance(input_hash, str) or not input_hash:
            raise ValueError('Each test needs a task_input_hash.')
        if not tests:
            scheduler = deepcopy(report['scheduler'])
            metadata = deepcopy(report.get('metadata', {}))
        elif report['scheduler'] != scheduler or report.get('metadata', {}) != metadata:
            raise ValueError('Scene reports must share metadata and scheduler configuration.')
        overall = report['overall']
        tests[number] = input_hash
        for name, value in overall.items():
            if name != 'statistics':
                values = per_test.setdefault(name, [])
                if value is not None:
                    values.append(value)
    if not tests:
        raise ValueError('At least one test report is required.')
    statistics = {name: _statistics(values) for name, values in per_test.items()}
    signature = json.dumps(sorted(tests.items()), separators=(',', ':')).encode('utf-8')
    return {
        'scope': 'scene', 'metadata': metadata, 'scheduler': scheduler,
        'test_count': len(tests), 'test_numbers': sorted(tests),
        'scene_input_hash': 'sha256:' + hashlib.sha256(signature).hexdigest(),
        'aggregation': 'equal_weight_tests',
        'overall': {name: stats['mean'] for name, stats in statistics.items()},
        'per_test_statistics': statistics,
    }
