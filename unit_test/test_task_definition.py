import unittest

from scheduler_simulator import TaskDefinition


class TaskDefinitionValidationTest(unittest.TestCase):
    def test_single_shot_accepts_one_burst(self):
        task = TaskDefinition("A", 0, 5, [5])
        self.assertEqual(task.actual_burst_times, [5])
        self.assertEqual(task.cycle_count, 1)

    def test_cyclic_task_accepts_one_burst_per_cycle(self):
        task = TaskDefinition("A", 0, 5, [5, 3, 7], period=10, cycle_count=3)
        self.assertEqual(task.actual_burst_times, [5, 3, 7])
        self.assertEqual(task.burst_time, 5)

    def test_burst_times_are_required(self):
        with self.assertRaises(TypeError):
            TaskDefinition(name="A", arrival_time=0, burst_time=5)

    def test_rejects_non_list_bursts(self):
        for value in (None, 5, "5", (5,), True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                TaskDefinition("A", 0, 5, value)

    def test_burst_count_must_match_cycle_count(self):
        for count, bursts in ((1, []), (1, [1, 2]), (3, [1, 2]), (2, [1, 2, 3])):
            with self.subTest(count=count, bursts=bursts), self.assertRaises(ValueError):
                TaskDefinition("A", 0, 5, bursts, period=10, cycle_count=count)

    def test_bursts_must_be_positive_integers(self):
        for value in (0, -1, True, False, 1.5, "5", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                TaskDefinition("A", 0, 5, [value])

    def test_constructor_copies_input_list(self):
        bursts = [5]
        task = TaskDefinition("A", 0, 5, bursts)
        bursts[0] = 9
        self.assertEqual(task.actual_burst_times, [5])

    def test_rejects_invalid_names(self):
        for name in ("", " ", None, 1):
            with self.subTest(name=name), self.assertRaises(ValueError):
                TaskDefinition(name, 0, 5, [5])

    def test_integer_fields_validate_type_and_range(self):
        for field, values in (
            ("arrival_time", (-1, True, 1.5, None)),
            ("burst_time", (0, -1, True, 1.5, None)),
            ("period", (-1, True, 1.5, None)),
            ("cycle_count", (0, -1, True, 1.5, None)),
        ):
            for value in values:
                args = dict(name="A", arrival_time=0, burst_time=5, actual_burst_times=[5])
                args[field] = value
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    TaskDefinition(**args)

    def test_multiple_cycles_require_positive_period(self):
        with self.assertRaises(ValueError):
            TaskDefinition("A", 0, 5, [5, 5], period=0, cycle_count=2)


if __name__ == "__main__":
    unittest.main()
