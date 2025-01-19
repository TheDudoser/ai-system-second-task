import unittest
from src.extract_element_utils import find_meta_value, find_name_value
from tests.utils import load_fixture


class TestFindMetaValue(unittest.TestCase):
    def test_base(self):
        tz = load_fixture("geometrical_characteristics/tz.json")
        self.assertEqual(find_name_value(tz, 'Геометрические характеристики'), find_meta_value(tz, 'Геометрические характеристики'))

