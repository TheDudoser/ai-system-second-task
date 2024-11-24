from dotenv import load_dotenv, dotenv_values
from pathlib import Path


def get_project_root() -> str:
    return Path(__file__).parent.parent.__str__() + '/'

def get_dotenv_config() -> dict[str, str | None]:
    return dotenv_values(get_project_root() + '.env.local')\
        if load_dotenv(get_project_root() + '.env.local')\
        else dotenv_values(get_project_root() + '.env')


def get_dotenv_by_key(key: str) -> str:
    return get_dotenv_config().get(key)
