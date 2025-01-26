def filter_by_method_and_get_matching_objects(similarity_table, operation_dict, is_euklid):
    # Функция для фильтрации объектов по значению %d1
    filtered_table1 = []
    percentage = 60


    for item in similarity_table["Table1" if not is_euklid else "Table2"]:
        if item["data"].get("%d1" if not is_euklid else "%d2", 0) >= percentage:
            filtered_table1.append(item)
        if len(filtered_table1) == 6:  # Ограничиваем результат первыми 6 объектами
            break

    print("В результате фильтрации по " + ("Манхетену" if not is_euklid else "Евклиду") + f" с порогом похожести выше {percentage}% осталось {len(filtered_table1)} операций")
    print()

    # Извлекаем имена (TO_name) из выбранных объектов
    selected_names = [item["TO_name"] for item in filtered_table1]

    filtered_table2 = {}

    for key in selected_names:
        if key in operation_dict:
            filtered_table2[key] = operation_dict[key]


    return filtered_table1, filtered_table2
