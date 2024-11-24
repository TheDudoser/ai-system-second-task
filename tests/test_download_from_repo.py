import unittest
from src.api_client import get_token_by_current_env_vars, get_without_download_from_repo


class TestDownloadFromRepo(unittest.TestCase):
    def setUp(self):
        self.__token = get_token_by_current_env_vars()

    def test_success_get_without_download_from_repo(self):
        example_path = " Загрузки / Архив протоколов технологических операций лазерной обработки"

        data = get_without_download_from_repo(example_path, self.__token)
        self.assertIsNotNone(data)

    def test_raise_get_without_download_from_repo(self):
        example_path = " Загрузки / "

        get_without_download_from_repo(example_path, self.__token)
        self.assertRaises(Exception)

    def test_get_ontology_materials(self):
        example_path = " Загрузки / Онтология справочника по материалам"

        data = get_without_download_from_repo(example_path, self.__token)
        self.assertIsNotNone(data)

    def test_get_with_start_target(self):
        example_path = 'Загрузки /Справочник по материалам'

        data = get_without_download_from_repo(example_path, self.__token, '/Сплавы на основе железа/Сталь марки РС категории А')
        self.assertIsNotNone(data)

    def test_test(self):
        example_path = 'Загрузки / Онтология архива протоколов технологических операций лазерной обработки'

        print (get_without_download_from_repo(example_path, self.__token))
