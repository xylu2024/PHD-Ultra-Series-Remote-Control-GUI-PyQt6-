# -*- coding: utf-8 -*-
"""
Tests for syringe database and validation helpers in functions.py.
"""

import unittest
from functions import Get_syringe_dict, is_number_and_positive, user_input_range_validate


class TestSyringeAndValidation(unittest.TestCase):
    def test_get_syringe_dict_non_empty(self):
        syr_dict = Get_syringe_dict()
        self.assertIsInstance(syr_dict, dict)
        self.assertGreater(len(syr_dict), 0)
        # Verify common manufacturers exist
        self.assertIn("Becton Dickinson, Plasti-pak", syr_dict)
        self.assertIn("Hamilton 700, Glass", syr_dict)

    def test_is_number_and_positive(self):
        self.assertTrue(is_number_and_positive("12.5"))
        self.assertTrue(is_number_and_positive("0.001"))
        self.assertTrue(is_number_and_positive("100"))
        self.assertTrue(is_number_and_positive("0"))  # 0 is considered non-negative
        self.assertFalse(is_number_and_positive("-5"))
        self.assertFalse(is_number_and_positive("abc"))
        self.assertFalse(is_number_and_positive(""))
        self.assertFalse(is_number_and_positive(None))

    def test_user_input_range_validate(self):
        flow_min = "0.5 nl/min"
        flow_max = "10.0 ml/min"
        
        # Valid value within range
        self.assertTrue(user_input_range_validate(flow_min, flow_max, "1.0", "ml/min"))
        self.assertTrue(user_input_range_validate(flow_min, flow_max, "500", "ul/min"))
        
        # Out of bounds
        self.assertFalse(user_input_range_validate(flow_min, flow_max, "20.0", "ml/min"))
        self.assertFalse(user_input_range_validate(flow_min, flow_max, "0.1", "nl/min"))


if __name__ == "__main__":
    unittest.main()
