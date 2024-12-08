from src.api_client import get_without_download_from_repo, get_token_by_current_env_vars, download_from_repo
from src.extract_element_utils import find_nested_element
from src.sim import Sim

if __name__ == '__main__':
    # TODO: cli with 2 params: "ontology" path and "new case" path
    path = "Загрузки / Онтология архива протоколов технологических операций лазерной обработки"

    test_data = get_without_download_from_repo(path, get_token_by_current_env_vars())

    # TEST
    key1 = "name"
    value1 = "Для целей тестирования"
    key2 = "name"
    value2 = "Техническое задание на выполнение технологической операции"

    # Search for the element containing both key-value pairs
    result = find_nested_element(test_data, key1, value1, key2, value2)

    print(Sim.compare(result, result))
