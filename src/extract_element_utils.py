def find_nested_element(data, key1, value1, key2, value2):
    def find_first_pair(data, key1, value1):
        if isinstance(data, dict):
            if key1 in data and data[key1] == value1:
                return data
            for key, value in data.items():
                if isinstance(value, dict):
                    result = find_first_pair(value, key1, value1)
                    if result is not None:
                        return result
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            result = find_first_pair(item, key1, value1)
                            if result is not None:
                                return result
        elif isinstance(data, list):
            for item in data:
                result = find_first_pair(item, key1, value1)
                if result is not None:
                    return result
        return None

    first_pair_dict = find_first_pair(data, key1, value1)

    if first_pair_dict:
        return find_first_pair(first_pair_dict, key2, value2)

    return None


def find_name_value(data, name):
    """
     Function to find an object with a given key "name" and its value.

     Args:
     data: Data in dictionary format.
     name: The searched value of the key "name".

     Returns:
     A dictionary with the found object or None if the object is not found.
    """

    if 'name' in data and data['name'] == name:
        return data

    for item in data.values():
        if isinstance(item, dict):
            result = find_name_value(item, name)
            if result:
                return result
        elif isinstance(item, list):
            for sub_item in item:
                result = find_name_value(sub_item, name)
                if result:
                    return result

    return None


def find_meta_value(data, meta):
    """
    Находит первый объект с заданным значением ключа "meta".

    Args:
      data: Данные в формате словаря или списка.
      meta: Искомое значение ключа "meta".

    Returns:
      Словарь с найденным объектом или None, если объект не найден.
    """
    if isinstance(data, dict):
        if 'meta' in data and data['meta'] == meta:
            return data
        for value in data.values():
            result = find_meta_value(value, meta)
            if result:
                return result
    elif isinstance(data, list):
        for item in data:
            result = find_meta_value(item, meta)
            if result:
                return result
    return None


def extract_names_by_meta_iterative(data, meta) -> list[str]:
    names = []
    stack = [data]

    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            if item.get('meta') == meta and 'successors' in item:
                for successor in item['successors']:
                    if isinstance(successor, dict) and 'name' in successor:
                        names.append(successor['name'])
            elif 'successors' in item:
                for successor in item['successors']:
                    stack.append(successor)
        elif isinstance(item, list):
            for element in item:
                stack.append(element)
    return names
