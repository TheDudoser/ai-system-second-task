def filter_by_method_and_get_matching_objects(similarity_table, operation_dict, is_euklid):
    # Функция для фильтрации объектов по значению %d1
    filtered_table1 = []
    for item in similarity_table["Table1" if not is_euklid else "Table2"]:
        if item["data"].get("%d1" if not is_euklid else "%d2", 0) >= 60:
            filtered_table1.append(item)
        if len(filtered_table1) == 6:  # Ограничиваем результат первыми 6 объектами
            break

    # Извлекаем имена (TO_name) из выбранных объектов
    selected_names = [item["TO_name"] for item in filtered_table1]

    # Обрезаем второй словарь, оставляем только те элементы, чьи имена из selected_names
    filtered_table2 = {key: value for key, value in operation_dict.items() if key in selected_names}

    return filtered_table1, dict(reversed(list(filtered_table2.items())))
