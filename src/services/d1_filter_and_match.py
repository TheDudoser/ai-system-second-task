def filter_by_d1_and_get_matching_objects(similarity_table, operation_dict):
    # Функция для фильтрации объектов по значению %d1
    filtered_table1 = []
    for item in similarity_table["Table1"]:
        if item["data"].get("%d1", 0) >= 60:
            filtered_table1.append(item)
        if len(filtered_table1) == 6:  # Ограничиваем результат первыми 6 объектами
            break

    # Извлекаем имена (TO_name) из выбранных объектов
    selected_names = [item["TO_name"] for item in filtered_table1]

    # Обрезаем второй словарь, оставляем только те элементы, чьи имена из selected_names
    filtered_table2 = {key: value for key, value in operation_dict.items() if key in selected_names}

    return filtered_table1, filtered_table2
