from typing import Final

from src.api_client import get_without_download_from_repo, get_token_by_current_env_vars
from src.interval import Interval
from src.path_utils import split_path, replace_path_last_part
from src.element_types.material import Material
from src.element_types.processing_object import ProcessingObject
from src.element_types.substrate import Substrate
from src.extract_element_utils import find_name_value, find_meta_value
from src.mark import Mark


class Sim:
    GEOMETRICAL_CHARACTERISTICS_VALUE: Final = 'Геометрические характеристики'

    # про пропуски
    @staticmethod
    def resolve_pass_tz(el, el_new):
        if el is not None and el_new is None:
            return [el, el]
        return [el, el_new]

    @staticmethod
    def compare(tz, tz_new):
        # TODO: ключами должны быть наименования или классы? К примеру, 'Объект обработки' или 'Подложка'?
        result = dict()
        # Сравнение Объектов обработки

        # Объект обработки -> Подложка
        processing_object = find_meta_value(tz, ProcessingObject.PO.value)
        processing_object_new = find_meta_value(tz_new, ProcessingObject.PO.value)

        processing_object_substrate = find_meta_value(processing_object, ProcessingObject.SUBSTRATE.value)
        processing_object_substrate_new = find_meta_value(processing_object_new, ProcessingObject.SUBSTRATE.value)

        if processing_object_substrate and processing_object_substrate_new:
            processing_object_substrate, processing_object_substrate_new = Sim.resolve_pass_tz(
                processing_object_substrate, processing_object_substrate_new
            )

            # TODO: Подложка -> Материал
            result_sim_substrate_material = Sim.compare_materials(
                processing_object_substrate,
                processing_object_substrate_new
            )
            result[
                ProcessingObject.PO.value + '.' + ProcessingObject.SUBSTRATE.value + '.' + Substrate.MATERIAL.value
            ] = result_sim_substrate_material.value

            # TODO: Подложка -> Масса
            result_sim_substrate_mass = Sim.compare_mass(
                processing_object_substrate,
                processing_object_substrate_new
            )
            result[
                ProcessingObject.PO.value + '.' + ProcessingObject.SUBSTRATE.value + '.' + Substrate.MASS.value
            ] = result_sim_substrate_mass.value

            # Подложка -> Геометрические характеристики
            result_sim_substrate_char = Sim.compare_geometrical_characteristics(
                processing_object_substrate,
                processing_object_substrate_new
            )
            result[
                ProcessingObject.PO.value + '.' + ProcessingObject.SUBSTRATE.value + '.' + Substrate.GEOM_CHARS.value
            ] = result_sim_substrate_char.value

            # В рамках нашей задачи не реализуем - Подложка -> Микроструктура

        # Объект обработки Деталь
        # TODO: Уточнить может ли быть одновременно и Подложка и деталь как объекты обработки
        # processing_object_substrate = find_name_value(tz, ProcessingObject.SUBSTRATE)
        # processing_object_substrate_new = find_name_value(tz_new, ProcessingObject.SUBSTRATE)

        # TODO: Материал для выполнения ТО
        # ...
        return result

    # TODO: Возможно, стоит подумать чтобы возвращать ещё и названия
    @staticmethod
    def compare_geometrical_characteristics(tz, tz_new) -> Mark:
        """
         Takes 2 ТЗ and compares their geometric characteristics.

         Args:
         tz: Operation ТЗ (ethalon).
         tz_new: new ТЗ.

         Returns:
         Mark.GREEN, if the sets of characteristics are identical in structure, otherwise Mark.RED.
        """

        el = find_name_value(tz, Sim.GEOMETRICAL_CHARACTERISTICS_VALUE)
        el_new = find_name_value(tz_new, Sim.GEOMETRICAL_CHARACTERISTICS_VALUE)

        # default
        el, el_new = Sim.resolve_pass_tz(el, el_new)

        if el is None:
            return Mark.RED

        names1 = [item['name'] for item in el['successors']]
        names2 = [item['name'] for item in el_new['successors']]

        if set(names1) == set(names2):
            return Mark.GREEN
        else:
            return Mark.RED

    @staticmethod
    def compare_defects(tz, tz_new) -> Mark:
        def extract_defect_value(data):
            for requirement in data.get('successors', []):
                for defect_group in requirement.get('successors', []):
                    for defect in defect_group.get('successors', []):
                        if defect['name'] == 'Наличе пор и дефектов':
                            for value in defect.get('successors', []):
                                return value['value']
            return None

        value1 = extract_defect_value(tz)
        value2 = extract_defect_value(tz_new)

        # default
        value1, value2 = Sim.resolve_pass_tz(value1, value2)

        if value1 is None:
            return Mark.RED

        difference = abs(value1 - value2)

        if difference < 10:
            return Mark.GREEN
        elif 10 <= difference <= 30:
            return Mark.ORANGE
        elif difference > 30:
            return Mark.RED

    @staticmethod
    def compare_materials(tz, tz_new) -> Mark:
        def extract_names_iterative(data) -> list[str]:
            names = []
            stack = [data]

            while stack:
                item = stack.pop()
                if isinstance(item, dict):
                    if item.get('meta') == Material.ANALOGUES.value and 'successors' in item:
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

        el = find_meta_value(tz, Substrate.MATERIAL.value)
        el_new = find_meta_value(tz_new, Substrate.MATERIAL.value)

        # default
        el, el_new = Sim.resolve_pass_tz(el, el_new)

        if el is None:
            return Mark.RED

        # Так как в материалах эталонных данных почти ничего и нет, нам нужно вытащить доп информацию из link
        path, start_target = split_path(el['link'])
        response_el = get_without_download_from_repo(path, get_token_by_current_env_vars(), start_target)
        true_el = find_name_value(response_el, el['name'])

        # Один из материалов явно указан в перечне аналогичных для другого
        name_el = true_el['name']
        name_el_new = el_new['name']

        el_analogues = extract_names_iterative(true_el)
        el_new_analogues = extract_names_iterative(el_new)

        if name_el in el_new_analogues or name_el_new in el_analogues:
            return Mark.GREEN

        # Принадлежность материалов разным классам
        new_start_target = replace_path_last_part(start_target, name_el_new)
        new_response_el = get_without_download_from_repo(path, get_token_by_current_env_vars(), new_start_target)
        if find_name_value(new_response_el, name_el_new) is None:
            return Mark.RED

        # Подобие эл. составов
        # TODO: Делает Матвей, временно возвращаю GREEN
        return Mark.GREEN

    @staticmethod
    def compare_mass(tz, tz_new) -> Mark:
        def get_mass_interval(local_mass, local_intervals):
            """Находит интервал, содержащий массу."""
            for interval in local_intervals:
                if interval.contains_value(local_mass):
                    return interval
            return None

        el = find_meta_value(tz, Substrate.MASS.value)
        el_new = find_meta_value(tz_new, Substrate.MASS.value)

        # default
        el, el_new = Sim.resolve_pass_tz(el, el_new)

        if el is None:
            return Mark.RED

        mass = find_meta_value(
            find_meta_value(el, 'Значение'),
            'Числовое значение'
        )['value']
        mass_new = find_meta_value(
            find_meta_value(el_new, 'Значение'),
            'Числовое значение'
        )['value']

        intervals = [
            Interval(0.01, 0.1),
            Interval(0.1, 1.0),
            Interval(1.0, 10.0),
            Interval(10.0, 100.0),
            Interval(100.0, 400.0)
        ]

        interval1 = get_mass_interval(mass, intervals)
        interval2 = get_mass_interval(mass_new, intervals)

        # 1
        if interval1 == interval2: # Используем __eq__ из класса Interval
            return Mark.GREEN
        # 2
        elif abs(intervals.index(interval1) - intervals.index(interval2)) > 1:
            return Mark.RED
        else: # 3. Смежные интервалы
            subinterval_len = interval2.right / 2
            midpoint = subinterval_len

            prev_subinterval_len = intervals[intervals.index(interval2)-1].right / 2\
                if intervals.index(interval2) != 0\
                else 0
            mid_midpoint = interval2.left + prev_subinterval_len\
                if intervals.index(interval2) != 0\
                else interval2.right

            if interval2.left <= mass_new < mid_midpoint:
                return Mark.GREEN
            elif mid_midpoint < mass_new <= midpoint:
                return Mark.ORANGE
            elif midpoint <= mass_new <= interval2.right:
                return Mark.RED
