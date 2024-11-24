def split_path(input_string):
    """Разделяет строку пути на две части: последнюю часть пути перед $ и начальный путь."""
    parts = input_string.split('$')
    if len(parts) != 2:
        raise ValueError("Неверный формат строки пути")

    root_path_parts = parts[0].strip().split('/')
    last_root_part = root_path_parts[-1]  # берем последний элемент

    initial_path = parts[1].strip()[:-1]  # Убираем точку с запятой в конце
    initial_path = initial_path.replace(' / ', '/')  # Заменяем " / " на "/"

    result1 = f"Загрузки / {last_root_part}"
    result2 = initial_path

    return result1, result2

def replace_path_last_part(input_string, new_path_part):
    """Заменяет последнюю часть пути после последнего '/' на новую строку, оставляя неизменной предпоследнюю часть."""
    parts = input_string.rsplit('/', 2) # Разделяем на три части, начиная с конца
    if len(parts) < 2:
        return ValueError("Недостаточно частей для замены")
    return parts[0] + "/" + parts[1] + "/" + new_path_part
