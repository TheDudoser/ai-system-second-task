import numpy as np
import pandas as pd
import json


def process_similarity_tables(*, input_data) -> dict:
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.width', 0)

    # Преобразование данных в DataFrame с обработкой отсутствующих значений
    column_names = list(input_data[0]['data'].keys())
    table = np.array([[row['data'].get(col, None) for col in column_names] for row in input_data])

    m, n = table.shape

    # Расчеты для каждой строки
    d1_values = np.apply_along_axis(lambda _row: 1 - np.sum([x for x in _row if x is not None]) / (n * 10), 1, table)
    d2_values = np.apply_along_axis(lambda _row: 1 - np.sqrt(np.sum([x ** 2 for x in _row if x is not None])) / (n * 10), 1, table)

    # Проценты похожести
    percent_d1 = d1_values * 100
    percent_d2 = d2_values * 100

    # Расширение таблицы
    df = pd.DataFrame(table, columns=column_names)
    df['%d1'] = percent_d1
    df['%d2'] = percent_d2

    # Добавление имени TO
    df.insert(0, 'TO_name', [row['TO_name'] for row in input_data])

    # Формирование Table1 и Table2
    table1 = df.sort_values(by='%d1', ascending=False).reset_index(drop=True)
    table2 = df.sort_values(by='%d2', ascending=False).reset_index(drop=True)

    # Подготовка структур данных для сохранения вложенности
    output_data = {
        "Table1": [],
        # "Table2": [],
    }

    # Сохраняем структуру с полями d1 и d2 внутри data
    for idx, row in table1.iterrows():
        row_data = {
            "TO_name": row["TO_name"],
            "data": {
                **{col: (row[col] if row[col] is not None else None) for col in column_names},
                "%d1": row["%d1"],
                "%d2": row["%d2"]
            }
        }
        output_data["Table1"].append(row_data)

    # for idx, row in table2.iterrows():
    #     row_data = {
    #         "TO_name": row["TO_name"],
    #         "data": {
    #             **{col: (row[col] if row[col] is not None else None) for col in column_names},
    #             "%d1": row["%d1"],
    #             "%d2": row["%d2"]
    #         }
    #     }
    #     output_data["Table2"].append(row_data)


    return output_data
