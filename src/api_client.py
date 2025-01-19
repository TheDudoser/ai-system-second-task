import os
import requests
import json
from src.dotnev_utils import get_dotenv_by_key


def parse_nested_json(data):
    """
    Recursively parse nested JSON strings into Python dictionaries.
    """
    if isinstance(data, dict):
        return {key: parse_nested_json(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [parse_nested_json(item) for item in data]
    elif isinstance(data, str):
        try:
            return parse_nested_json(json.loads(data))
        except (json.JSONDecodeError, TypeError):
            return data
    else:
        return data


def get_token(username: str, password: str) -> str:
    """
    Get token from iacpass
    :param username: username
    :param password: password
    :return: token
    """
    headers = {"accept": "application/json", "Content-Type": "application/json"}

    payload = {"username": username, "password": password}
    r = requests.post("https://iacpaas.dvo.ru/api/signin", json=payload, headers=headers)
    if r.status_code != 200:
        raise Exception("Failed to get token: {}".format(r.text))
    return r.json()["accessToken"]


def get_token_by_current_env_vars():
    return get_token(get_dotenv_by_key("API_EMAIL"), get_dotenv_by_key("API_PASS"))


def get_data_from_repo(
    path: str,
    token: str,
    start_target: str = "",
    json_type: str = "universal",
    compress: bool = False,
    no_blob_data: bool = True,
):
    """
    Downloads a file from iacpass repository.
    :param start_target: path starting from which data will be returned
    :param name: name of the file to be saved
    :param url: base url to the repository
    :param path: Path to the file
    :param compress: ...
    :param no_blob_data: ...
    :return: None
    """

    params = {
        "path": path,
        "json-type": json_type,
        "compress": compress,
        "no-blob-data": no_blob_data,
        "start-target-concept-path": start_target,
    }

    headers = {"Authorization": f"Bearer {token}"}

    return requests.get(
        "https://iacpaas.dvo.ru/api/data/export/user-item", params=params, headers=headers
    )


def get_without_download_from_repo(
    path: str,
    token: str,
    start_target: str = "",
    json_type: str = "universal",
    compress: bool = False,
    no_blob_data: bool = True,
):
    """
    Get a data from iacpass repository.
    :param start_target: path starting from which data will be returned
    :param name: name of the file to be saved
    :param url: base url to the repository
    :param path: Path to the file
    :param compress: ...
    :param no_blob_data: ...
    :return: None
    """
    r = get_data_from_repo(path, token, start_target, json_type, compress, no_blob_data)
    if r.status_code == 200:
        response_json = r.json()

        return parse_nested_json(response_json)
    else:
        raise Exception("Failed to get data")


def download_from_repo(
    name: str,
    path: str,
    token: str,
    start_target: str = "",
    json_type: str = "universal",
    compress: bool = False,
    no_blob_data: bool = True,
) -> None:
    """
    Downloads a file from iacpass repository.
    :param start_target: path starting from which data will be returned
    :param name: name of the file to be saved
    :param url: base url to the repository
    :param path: Path to the file
    :param compress: ...
    :param no_blob_data: ...
    :return: None
    """
    r = get_data_from_repo(path, token, start_target, json_type, compress, no_blob_data)

    if r.status_code == 200:

        response_json = r.json()

        parsed_data = parse_nested_json(response_json)

        with open(f"{name}.json", "w", encoding="utf-8") as json_file:
            json.dump(parsed_data, json_file, indent=2, ensure_ascii=False)

        print(f"File {name}.json has been saved")
    else:
        raise Exception("Failed to download file")


def get_with_cache_from_repo(
    path: str,
    token: str,
    start_target: str = "",
    json_type: str = "universal",
    compress: bool = False,
    no_blob_data: bool = True,
    cache_dir: str = "cache",
):
    """
    Get data from iacpass repository, downloading only if not already cached.
    :param start_target: path starting from which data will be returned
    :param path: Path to the file
    :param compress: ...
    :param no_blob_data: ...
    :param cache_dir: Directory to store cached files
    :return: Parsed JSON data
    """
    os.makedirs(cache_dir, exist_ok=True)

    full_path = os.path.basename(path) + os.path.basename(start_target)

    cache_file_path = os.path.join(cache_dir, f"{os.path.basename(full_path)}.json")

    if os.path.exists(cache_file_path):
        with open(cache_file_path, "r", encoding="utf-8") as cache_file:
            return parse_nested_json(json.load(cache_file))

    # Fetch data if not cached
    r = get_data_from_repo(path, token, start_target, json_type, compress, no_blob_data)
    if r.status_code == 200:
        response_json = r.json()
        parsed_data = parse_nested_json(response_json)

        # Caching...
        with open(cache_file_path, "w", encoding="utf-8") as cache_file:
            json.dump(parsed_data, cache_file, indent=2, ensure_ascii=False)

        return parsed_data
    else:
        raise Exception("Failed to get data")
