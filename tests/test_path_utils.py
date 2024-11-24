import unittest
from src.path_utils import split_path, replace_path_last_part


class TestSplitPath(unittest.TestCase):
    # split
    def test_success_split(self):
        example_path = "vadim@dvo.ru / Мой Фонд / Лазерное аддитивное производство / Справочник по материалам$/Сплавы на основе железа/Сталь марки РС категории А;"

        data = split_path(example_path)
        self.assertEqual(
            ('Загрузки /  Справочник по материалам', '/Сплавы на основе железа/Сталь марки РС категории А'),
            data
        )

    def test_raise_split(self):
        example_path = "/Сплавы на основе железа/Сталь марки РС категории А;"

        with self.assertRaises(ValueError):
            split_path(example_path)

    # replace last part
    def test_success_replace_path_last_part(self):
        example_path = "/Сплавы на основе железа/Сталь марки РС категории А"
        self.assertEqual('/Сплавы на основе железа/test', replace_path_last_part(example_path, 'test'))

        example_path = "/Сплавы на основе железа"
        self.assertEqual('/Сплавы на основе железа/test', replace_path_last_part(example_path, 'test'))

    def test_raise_replace_path_last_part(self):
        example_path = "Сплавы на основе железа"

        with self.assertRaises(ValueError):
            split_path(example_path)
