import json
from src.api_client import get_without_download_from_repo, get_token_by_current_env_vars, download_from_repo
from src.extract_element_utils import find_nested_element
from src.sim import Sim
import typer

app = typer.Typer()

@app.command()
def run_comparison(path: str, new_case_path: str, name: str, save_result: bool = False):
    base = get_without_download_from_repo(path, get_token_by_current_env_vars())
    new_case = get_without_download_from_repo(new_case_path, get_token_by_current_env_vars())
    key1 = "name"
    value1 = name
    key2 = "name"
    value2 = "Техническое задание на выполнение технологической операции"

    to_1 = find_nested_element(base, key1, value1, key2, value2)
    to_2 = find_nested_element(new_case, key1, value1, key2, value2)

    result = Sim.compare(to_1, to_2)

    if save_result:
        with open("result.json", "w") as f:
            json.dump(result, f)
            print("result saved")
            print(result)
    else:
        print(result)




if __name__ == "__main__":
    app()