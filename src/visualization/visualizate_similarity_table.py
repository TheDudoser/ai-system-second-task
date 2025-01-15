
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


def visualize_data(*, similarity_table, operation_dict, new_tz_dict):
    def generate_html(*, data, path, top_key, level=0, is_open=False):
        """Рекурсивная функция для генерации HTML с раскрывающимися списками.
           Формируем путь из ключа meta."""
        html = ""
        is_open_str = 'open' if is_open else ''

        if isinstance(data, dict):
            for key, value in data.items():
                if key in ["id", "type", "meta", "name", "valtype", "comment", "original"]:
                    continue  # Пропускаем ненужные ключи

                if key == "successors":  # Обрабатываем successors, если есть
                    for successor in value:
                        current_path = successor.get("meta")
                        full_path = f"{path} | {current_path}"

                        color = _get_color(similarity_table=similarity_table, full_path=full_path, top_key=top_key)
                        is_open = False if color else True
                        is_open_str = 'open' if is_open else ''
                        style = f"background-color: {color};" if color else ""

                        successor_meta = successor.get("meta", "Без мета")
                        meta_title = f"{successor_meta} ({successor.get('name', 'Без названия')})"
                        html += f"<details {is_open_str}>\n<summary style='{style}' data-color='{color}' data-meta='{successor_meta}'>{meta_title}</summary>\n"
                        # Рекурсивно передаем путь
                        html += generate_html(data=successor, path=full_path, top_key=top_key, level=level + 1,
                                              is_open=is_open)
                        html += "</details>\n"
                elif isinstance(value, (dict, list)):
                    html += f"<details {is_open_str}>\n<summary>{key}</summary>\n"
                    html += generate_html(data=value, path=path, top_key=top_key, level=level + 1,
                                          is_open=False)  # Передаем путь
                    html += "</details>\n"
                else:
                    html += f"<p><strong>{key}:</strong> {value}</p>\n"
        elif isinstance(data, list):
            for item in data:
                html += generate_html(data=item, path=path, top_key=top_key, level=level + 1,
                                      is_open=False)  # Передаем путь в случае списка
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
    display: flex;
    flex-direction: row;
    justify-content: space-between;
}
.left-column, .right-column {
    width: 48%;
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
select {
    width: 100%;
    padding: 8px;
    margin-bottom: 20px;
}
</style>
<script>
function updateTree(operationName) {
    var trees = document.getElementsByClassName('operation-tree');
    for (var i = 0; i < trees.length; i++) {
        trees[i].style.display = 'none';  // Скрываем все деревья
    }

    var selectedTree = document.getElementById(operationName);
    if (selectedTree) {
        selectedTree.style.display = 'block';  // Показываем выбранное дерево
    }

    // Находим окрашенные элементы в выбранном дереве
    coloredNodes = selectedTree.querySelectorAll("[data-color]:not([data-color=''])");
    newTzEl = document.getElementById('new-tz');
    
    // Сбрасываем предыдущие цвета в newTzEl
    coloredTzNodes = newTzEl.querySelectorAll("[data-color]:not([data-color=''])");
    coloredTzNodes.forEach((elem) => {
        elem.setAttribute('data-color', '');
        elem.style.backgroundColor = '';
    });
    
    // Функция для поиска родителя с meta
    function findParentWithMeta(element) {
        const parentDetails = element.closest('details');
        if (parentDetails) {
            return parentDetails.querySelector('summary');
        }
        return null;
    }
    
    // Красим элементы в соответствии с выбранной операцией
    coloredNodes.forEach((elem) => {
        const metaValue = elem.getAttribute('data-meta');
        const colorValue = elem.getAttribute('data-color');
    
        // Находим соответствующий элемент в newTzEl
        let matchingElements = newTzEl.querySelectorAll(`[data-meta="${metaValue}"]`);
        matchingElements.forEach((matchingElement) => {
            if (matchingElement) {
                const parentMatchingElementValue = matchingElement.parentElement.parentElement.querySelector("[data-meta]").getAttribute('data-meta');
                const parentElementValue = elem.parentElement.parentElement.querySelector("[data-meta]").getAttribute('data-meta');
                if (parentMatchingElementValue == parentElementValue) {
                    matchingElement.setAttribute('data-color', colorValue);
                    matchingElement.style.backgroundColor = colorValue;
                }
                else if (parentElementValue == 'Подложка' || parentElementValue == 'Деталь') {
                    if (parentMatchingElementValue == 'Подложка' || parentMatchingElementValue == 'Деталь') {
                        matchingElement.setAttribute('data-color', colorValue);
                        matchingElement.style.backgroundColor = colorValue;
                    }
                }
            }
        })
    });
}

// Вызываем updateTree после загрузки страницы
window.onload = function() {
    var selectElement = document.querySelector('select');
    if (selectElement) {
        updateTree(selectElement.value);  // Передаем текущее значение select
    }
};
</script>
</head>
<body> 

<div class="left-column">"""

    operation_name = new_tz_dict['name']

    html += f'<h2>{operation_name}</h2>'
    html += f'<details open id="new-tz"> <summary>{operation_name}</summary>'
    html += generate_html(data=new_tz_dict, path=operation_name, top_key=operation_name, level=0, is_open=True)
    html += '</details>'
    html += '</div>'

    html += """
    <div class="right-column">
    <!-- Выпадающий список -->
    <h2>Выберите операцию</h2>
    <select onchange="updateTree(this.value)">
        """



    # Добавляем операции в выпадающий список
    is_first = True
    for operation_name, operation_data in operation_dict.items():
        percent = get_percent_similarity(operation_name=operation_name, similarity_table=similarity_table)
        html += f'<option value="{operation_name}" {'selected' if is_first else ''}>{operation_name} ({percent}%)</option>'
        is_first = False

    html += """</select>

    <div>"""

    # Генерация дерева для каждой операции в operation_dict
    is_first = True
    for operation_name, operation_data in operation_dict.items():
        percent = get_percent_similarity(operation_name=operation_name, similarity_table=similarity_table)
        html += f'<div id="{operation_name}" class="operation-tree" style="display: none;">'  # Идентификатор для отображения
        html += f"<details open>\n<summary>{operation_name} ({percent}%)</summary>\n"
        html += generate_html(data=operation_data, path=operation_name, top_key=operation_name, level=0,
                              is_open=is_first)
        html += "</details>\n"
        html += "</div>\n"
        is_first = False

    # Конец HTML-документа
    html += "</div>"
    html += "</div>"
    html += "</body>\n</html>"

    return html

