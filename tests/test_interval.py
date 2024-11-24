from src.interval import Interval
import unittest


class TestInterval(unittest.TestCase):
    delta = 1e-12

    def test_constructor_and_bounds(self):
        interval = Interval(1.0, 5.0)
        self.assertAlmostEqual(interval.get_left(), 1.0, delta=self.delta)
        self.assertAlmostEqual(interval.get_right(), 5.0, delta=self.delta)

    def test_length(self):
        interval = Interval(1.0, 5.0)
        self.assertAlmostEqual(interval.length(), 4.0, delta=self.delta)

    def test_intersection(self):
        interval1 = Interval(1.0, 5.2137681235678)
        interval2 = Interval(5.2137681235677, 7.0)
        interval3 = Interval(6.0, 8.0)
        self.assertTrue(interval1.intersects(interval2))
        self.assertFalse(interval1.intersects(interval3))

    def test_intersection_at_bounds(self):
        interval1 = Interval(1.0, 5.0)
        interval2 = Interval(5.0, 10.0)
        self.assertTrue(interval1.intersects(interval2))
        self.assertTrue(interval2.intersects(interval1))

    def test_containment(self):
        interval1 = Interval(1.0, 5.0)
        interval2 = Interval(2.0, 4.0)
        self.assertTrue(interval1.contains_interval(interval2))
        self.assertFalse(interval2.contains_interval(interval1))

    def test_containment_for_same_interval(self):
        interval1 = Interval(2.0, 4.0)
        self.assertTrue(interval1.contains_interval(interval1))

    def test_equality(self):
        interval1 = Interval(1.0, 5.0)
        interval2 = Interval(1.0, 5.0)
        interval3 = Interval(2.0, 5.0)
        self.assertEqual(interval1, interval2)
        self.assertNotEqual(interval1, interval3)

    def test_equality_for_zero_length_intervals(self):
        interval1 = Interval(3.0, 3.0)
        interval2 = Interval(3.0, 3.0)
        interval3 = Interval(2.0, 2.0)
        self.assertEqual(interval1, interval2)
        self.assertNotEqual(interval1, interval3)

    def test_contains_value(self):
        interval = Interval(1.0, 5.0)
        self.assertTrue(interval.contains_value(3.0))
        self.assertFalse(interval.contains_value(0.5))
        self.assertFalse(interval.contains_value(5.5))

    def test_contains_value_at_bounds(self):
        interval = Interval(2.0, 7.0)
        self.assertTrue(interval.contains_value(2.0))
        self.assertTrue(interval.contains_value(7.0))

    def test_non_overlapping_intervals(self):
        interval1 = Interval(1.0, 2.0)
        interval2 = Interval(3.0, 4.0)
        self.assertFalse(interval1.intersects(interval2))
        self.assertFalse(interval2.intersects(interval1))

    def test_large_intervals_containment(self):
        interval1 = Interval(-float('inf'), float('inf'))
        interval2 = Interval(-1e6, 1e6)
        self.assertTrue(interval1.contains_interval(interval2))
        self.assertFalse(interval2.contains_interval(interval1))
