import json
from typing import Annotated

from src.api_client import get_without_download_from_repo, get_token_by_current_env_vars
from src.extract_element_utils import find_nested_element, find_name_value, find_meta_value
from src.similarity_table.similarity_table import process_similarity_tables
from src.visualization.visualizate_similarity_table import visualize_data
from src.services.replace_links import replace_links_to_dict
from src.services.d1_filter_and_match import filter_by_d1_and_get_matching_objects
from src.sim import Sim
import typer

app = typer.Typer()


def extract_operations_with_meta(data, target_meta):
    operations = []

    def traverse(node):
        if isinstance(node, dict):
            if node.get("meta") == target_meta:
                operations.append(node)
            for key, value in node.items():
                traverse(value)
        elif isinstance(node, list):
            for item in node:
                traverse(item)

    traverse(data)
    return operations


@app.command()
def run_comparison(
        path: Annotated[
            str,
            typer.Argument(help="path базы ТО"),
        ],
        new_case_path: Annotated[
            str,
            typer.Argument(help="path нового случая"),
        ],
        save_result: Annotated[
            bool,
            typer.Option(help="Название технологического задания"),
        ] = False,
):
    base = get_without_download_from_repo(
        path,
        get_token_by_current_env_vars()
    )
    base_operations = extract_operations_with_meta(base, 'Технологическая операция')

    new_case = get_without_download_from_repo(new_case_path, get_token_by_current_env_vars())

    result = []
    operation_with_links_dict = {}

    tz_meta = "Техническое задание на выполнение технологической операции"
    for operation in base_operations:
        operation_tz = find_meta_value(operation, tz_meta)

        operation_with_links_dict[operation.get("name")] = operation_tz

        tz_new_case = find_meta_value(new_case, tz_meta)

        data = Sim.compare(operation_tz, tz_new_case)
        result.append({
            "TO_name": operation.get("name"),
            "data": data
        })



    if result:
        similarity_table = process_similarity_tables(input_data=result)

        similarity_table_cropped, operation_dict_cropped = filter_by_d1_and_get_matching_objects(similarity_table=similarity_table, operation_dict=operation_with_links_dict)

        operation_dict = replace_links_to_dict(operation_dict_with_links=operation_dict_cropped)

        visualize_data(similarity_table=similarity_table_cropped, operation_dict=operation_dict)



    if save_result:
        with open("result.json", "w") as f:
            json.dump(result, f)
            print("result saved")
            print(result)
    else:
        print(result)




if __name__ == "__main__":
    app()
