import json
import time
from typing import Annotated

from typer.rich_utils import print_with_rich

from src.api_client import get_with_cache_from_repo
from src.extract_element_utils import find_meta_value, find_nested_element
from src.similarity_table.similarity_table import process_similarity_tables
from src.visualization.visualizate_similarity_table import visualize_data
from src.services.replace_links import replace_links_to_dict
from src.services.d1_filter_and_match import filter_by_d1_and_get_matching_objects
from src.sim import Sim
from src.utils import token
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


@app.command(help="Выполнение полного цикла заданий: сравнение ТЗ, KNN, визуализация результата")
def run_comparison(
    path: Annotated[
        str,
        typer.Argument(
            help="path базы ТО. Если указан аргумент --use-api, ссылка вводится в формате 'Загрузки / Архив / ТО', иначе путь до файла"
        ),
    ],
    new_case_path: Annotated[
        str,
        typer.Argument(
            help="path нового случая. Если указан аргумент --use-api, ссылка вводится в формате 'Загрузки / Архив / ТЗ', иначе путь до файла"
        ),
    ],
    use_api: Annotated[
        bool,
        typer.Option(help="Использовать API для загрузки данных?"),
    ] = True,
):
    if use_api:
        print("Получение данных с API...")
        start_time = time.time()

        new_case = get_with_cache_from_repo(new_case_path, token)
        base = get_with_cache_from_repo(path, token)

        end_time = time.time()
        total_time = end_time - start_time
        print(
            "Данные с API получены. Время обращения к API: {total_time}сек.".format(
                total_time=round(total_time)
            )
        )
        print()
    else:
        with open(new_case_path, "r", encoding="utf-8") as f:
            new_case = json.load(f)
        with open(path, "r", encoding="utf-8") as f:
            base = json.load(f)

    new_case_path_to_name = path.split("/")[-1]
    base_operations = extract_operations_with_meta(base, "Технологическая операция")
    tz_meta = "Техническое задание на выполнение технологической операции"
    result_sim = []
    operation_with_links_dict = {}

    print("Старт сравнения ТЗ...")
    start_time = time.time()

    tz_new_case = find_nested_element(
        new_case, "name", new_case_path_to_name, "name", tz_meta
    )

    total_sim = 0
    with typer.progressbar(base_operations) as progress:
        for operation in progress:
            operation_tz = find_meta_value(operation, tz_meta)

            operation_with_links_dict[operation.get("name")] = operation_tz

            data = Sim.compare(tz=operation_tz, tz_new=tz_new_case)
            result_sim.append({"TO_name": operation.get("name"), "data": data})
            total_sim += 1
    print(
        f"Сравнение ТЗ окончено. Было проведено сравнение {total_sim} ТЗ из базы с новым случаем."
    )

    end_time = time.time()
    total_time = end_time - start_time

    print("Время сравнения: {total_time}сек.".format(total_time=round(total_time)))
    print()

    if result_sim:
        result_sim_filename = "result_sim.json"
        with open(result_sim_filename, "w", encoding="utf-8") as f:
            json.dump(result_sim, f, ensure_ascii=False, indent=4)
            print("Результат сравнения сохранён в {filename}".format(filename=result_sim_filename))
            print()

        print("Старт KNN...")
        similarity_table = process_similarity_tables(input_data=result_sim)
        print("Выполнение KNN окончено.")

        similarity_table_filename = "similarity_table.json"
        with open(similarity_table_filename, "w", encoding="utf-8") as f:
            json.dump(similarity_table, f, ensure_ascii=False, indent=4)
            print("Результат KNN сохранён в {filename}".format(filename=similarity_table_filename))
            print()

        # Запись данных в JSON с сохранением структуры
        with open("operation_with_links_dict.json", "w", encoding="utf-8") as f:
            json.dump(operation_with_links_dict, f, ensure_ascii=False, indent=4)

        similarity_table_cropped, operation_dict_cropped = filter_by_d1_and_get_matching_objects(
            similarity_table=similarity_table, operation_dict=operation_with_links_dict
        )

        operation_dict = replace_links_to_dict(operation_dict_with_links=operation_dict_cropped)

        tz_new_without_links = replace_links_to_dict(operation_dict_with_links=tz_new_case)

        print("Старт визуализации...")
        html = visualize_data(
            similarity_table=similarity_table_cropped, operation_dict=operation_dict, new_tz_dict=tz_new_without_links
        )
        print("Окончание визуализации.")

        visualization_filename = "visualization.html"
        with open(visualization_filename, "w", encoding="utf-8") as file:
            file.write(html)
            print(
                "Файл с визуализацией сохранён в {filename}".format(filename=visualization_filename)
            )


if __name__ == "__main__":
    app()
