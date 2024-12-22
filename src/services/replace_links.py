import copy

from src.api_client import get_without_download_from_repo, get_token_by_current_env_vars
from src.path_utils import split_path



def replace_links_to_dict(*, operation_dict_with_links):
    def resolve_link(link):
        """Получить объект из репозитория по указанному пути link."""
        path, start_target = split_path(link)
        # Возвращаем только данные из 'data'
        response = get_without_download_from_repo(path, get_token_by_current_env_vars(), start_target)

        if isinstance(response, str):
            return [{"field": response}]
        if isinstance(response, list):
            return response

        return response.get('data', {}).get("successors", {})  # Извлекаем только содержимое 'data'


    def recursive_replace(data):
        """Рекурсивно заменить все ссылки на объекты."""
        if isinstance(data, dict):
            # Если ключ 'link' есть, заменяем его содержимым из 'data'
            if 'link' in data:
                resolved_data = resolve_link(data['link'])
                data.pop('link')  # Убираем ключ 'link'
                # Добавляем successors из resolved_data
                data['successors'] = resolved_data
            # Рекурсивно обрабатываем все значения
            for key, value in list(data.items()):
                data[key] = recursive_replace(value)
        elif isinstance(data, list):
            # Рекурсивно обрабатываем каждый элемент списка
            return [recursive_replace(item) for item in data]
        return data

    # Создаём копию словаря, чтобы не изменять оригинал
    operational_dict_copy = copy.deepcopy(operation_dict_with_links)
    # Запускаем рекурсивную обработку
    return recursive_replace(operational_dict_copy)



