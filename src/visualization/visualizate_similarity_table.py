
def get_percent_similarity(*, operation_name, similarity_table) -> str:
    finded_data = next((entry for entry in similarity_table if entry.get("TO_name") == operation_name), None)
    return finded_data.get("data").get("%d1")


def _get_color(*, similarity_table, full_path, top_key) -> str:
    # Найти запись с соответствующим TO_name
    finded_data = next((entry for entry in similarity_table if entry.get("TO_name") == top_key), None)

    if not finded_data:
        return ""  # Если данные не найдены, возвращаем пустую строку

    # Извлекаем data из найденной записи
    data = finded_data.get("data", {})

    # Разбиваем full_path на элементы
    full_parts = full_path.split(" | ")

    for sim_path, sim_value in data.items():
        if sim_value is None:
            continue  # Пропускаем отсутствующие значения

        # Разбиваем sim_path на элементы
        sim_parts = sim_path.replace("_", " ").split(".")

        if sim_parts[-1] == full_parts[-1]:
            print("#########")
            print(full_parts)
            print(sim_parts)

        # Проверяем, совпадает ли последний элемент и включен ли путь
        if (
                sim_parts[-1] == full_parts[-1]  # Последний элемент должен совпадать
                and all(part in full_parts for part in sim_parts[:-1])  # Все остальные части должны быть в пути
                and sim_parts[-1] not in full_parts[:-1]  # Последний элемент не должен встречаться раньше
        ):
            if sim_value == 0:
                return "green"
            elif sim_value == 5:
                return "orange"
            elif sim_value == 10:
                return "red"

    return ""  # Если совпадений не найдено, возвращаем пустую строку


def visualize_data(*, similarity_table, operation_dict):
    def generate_html(*, data, path, top_key, level=0):
        """Рекурсивная функция для генерации HTML с раскрывающимися списками.
           Формируем путь из ключа meta."""
        html = ""

        if isinstance(data, dict):
            for key, value in data.items():
                if key in ["id", "type", "meta", "name", "valtype", "comment", "original"]:
                    continue  # Пропускаем ненужные ключи


                if key == "successors":  # Обрабатываем successors, если есть
                    for successor in value:

                        current_path = successor.get("meta")
                        full_path = f"{path} | {current_path}"

                        color = _get_color(similarity_table=similarity_table, full_path=full_path, top_key=top_key)
                        style = f"background-color: {color};" if color else ""

                        successor_meta = successor.get("meta", "Без мета")
                        meta_title = f"{successor_meta} ({successor.get('name', 'Без названия')})"
                        html += f"<details>\n<summary style='{style}'>{meta_title}</summary>\n"
                        # Рекурсивно передаем путь
                        html += generate_html(data=successor, path=full_path, top_key=top_key, level=level + 1)
                        html += "</details>\n"
                elif isinstance(value, (dict, list)):
                    html += f"<details>\n<summary>{key}</summary>\n"
                    html += generate_html(data=value, path=path, top_key=top_key, level=level + 1)  # Передаем путь
                    html += "</details>\n"
                else:
                    html += f"<p><strong>{key}:</strong> {value}</p>\n"
        elif isinstance(data, list):
            for item in data:
                html += generate_html(data=item, path=path, top_key=top_key, level=level + 1)  # Передаем путь в случае списка
        else:
            html += f"<p>{data}</p>\n"

        return html

    # Начало HTML-документа
    html = """<!DOCTYPE html>
<html lang='en'>
<head>
<meta charset='UTF-8'>
<title>TO Visualization</title>
<style>
body {
    font-family: Arial, sans-serif;
}
details {
    margin-left: 20px;
}
summary {
    cursor: pointer;
    font-weight: bold;
    margin: 5px 0;
}
p {
    margin: 0 0 5px 20px;
}
</style>
</head>
<body>
<h1>Технические операции</h1>
"""

    # Генерация контента для каждого ключа в operation_dict
    for operation_name, operation_data in operation_dict.items():
        html += f"<details>\n<summary>{operation_name} ({get_percent_similarity(operation_name=operation_name, similarity_table=similarity_table)}%)</summary>\n"
        # Путь для первого уровня — это значение из meta
        html += generate_html(data=operation_data, path=operation_name, top_key=operation_name, level=0)  # Начальный путь = ключ (meta)
        html += "</details>\n"

    # Конец HTML-документа
    html += "</body>\n</html>"

    # Сохранение HTML в файл
    with open("visualization.html", "w", encoding="utf-8") as file:
        file.write(html)

    print("HTML файл создан: visualization.html")
