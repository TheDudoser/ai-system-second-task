import numpy as np
import pandas as pd

def process_similarity_tables(*, input_data) -> dict:
    # Список для хранения итоговых данных
    final_data = []

    # Обработка каждого блока данных отдельно
    for item in input_data:
        column_names = list(item['data'].keys())  # Уникальные ключи для текущего блока
        data_values = list(item['data'].values())  # Соответствующие значения
        n = len(column_names)

        # Преобразование данных в массив для расчета
        table = np.array([data_values])

        # Расчеты для текущей строки
        d1_value = 1 - np.sum([x for x in table[0] if x is not None]) / (n * 10)
        d2_value = 1 - np.sqrt(np.sum([x ** 2 for x in table[0] if x is not None])) / (n * 10)

        # Проценты похожести
        percent_d1 = d1_value * 100
        percent_d2 = d2_value * 100

        # Собираем данные для текущей строки
        row_data = {
            "TO_name": item["TO_name"],
            "data": {
                **{col: val for col, val in zip(column_names, data_values)},  # Только существующие поля
                "%d1": percent_d1,
                "%d2": percent_d2
            }
        }
        final_data.append(row_data)

    # Подготовка структуры для финального результата
    output_data = {
        "Table1": sorted(final_data, key=lambda x: x["data"]["%d1"], reverse=True),
        # Аналогично можно добавить Table2, если нужно
    }

    return output_data
