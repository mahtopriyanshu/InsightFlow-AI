"""Focused unit tests for deterministic comparison safety."""
from datetime import date
import math
import unittest

import pandas as pd

from streamlit_app.insights.comparisons import (
    absolute_change, percentage_change, percentage_point_change,
    previous_comparable_period, safe_float,
)
from streamlit_app.utils.filters import FilterState
from streamlit_app.insights.engine import product_insights, seller_insights


class ComparisonTests(unittest.TestCase):
    def test_equal_duration_previous_period(self):
        selected = FilterState(date(2018, 1, 1), date(2018, 6, 30))
        result = previous_comparable_period(selected, date(2016, 9, 4))
        self.assertTrue(result.available)
        self.assertEqual(result.previous.end_date, date(2017, 12, 31))
        self.assertEqual(
            (result.previous.end_date - result.previous.start_date).days,
            (selected.end_date - selected.start_date).days,
        )

    def test_single_day_period(self):
        selected = FilterState(date(2018, 5, 2), date(2018, 5, 2), ("SP",))
        result = previous_comparable_period(selected, date(2016, 9, 4))
        self.assertEqual(result.previous.start_date, date(2018, 5, 1))
        self.assertEqual(result.previous.end_date, date(2018, 5, 1))
        self.assertEqual(result.previous.states, ("SP",))

    def test_partial_history_is_unavailable(self):
        selected = FilterState(date(2016, 9, 4), date(2016, 9, 10))
        result = previous_comparable_period(selected, date(2016, 9, 4))
        self.assertFalse(result.available)
        self.assertIsNone(result.previous)

    def test_zero_previous_has_no_percentage_change(self):
        self.assertIsNone(percentage_change(10, 0))

    def test_null_nan_and_infinite_are_safe(self):
        self.assertIsNone(percentage_change(None, 5))
        self.assertIsNone(absolute_change(math.nan, 5))
        self.assertIsNone(safe_float(math.inf))

    def test_equal_values(self):
        self.assertEqual(percentage_change(5, 5), 0)
        self.assertEqual(absolute_change(5, 5), 0)

    def test_percentage_points_are_subtraction(self):
        self.assertAlmostEqual(percentage_point_change(8.1, 6.0), 2.1)

    def test_empty_domain_results_emit_no_insight(self):
        filters = FilterState(date(2018, 1, 1), date(2018, 1, 2))
        self.assertEqual(product_insights(filters, pd.DataFrame(), pd.DataFrame()), [])
        self.assertEqual(seller_insights(filters, pd.DataFrame()), [])


if __name__ == "__main__":
    unittest.main()
