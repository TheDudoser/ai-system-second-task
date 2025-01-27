import sys
from collections import Counter
from typing import Final

from src.api_client import get_with_cache_from_repo
from src.element_types.elemental_composition import ElementalComposition
from src.element_types.interval_type import IntervalType
from src.element_types.material_for_maintenance import MaterialForMaintenance
from src.element_types.metal_powder import MetalPowder
from src.element_types.process_gas import ProcessGas
from src.element_types.requirements_operation_result import RequirementsOperationResult
from src.interval import Interval
from src.path_utils import split_path, replace_path_last_part
from src.element_types.material import Material
from src.element_types.processing_object import ProcessingObject
from src.element_types.substrate_detail import SubstrateDetail
from src.extract_element_utils import (
    find_name_value,
    find_meta_value,
    extract_names_by_meta_iterative,
    find_name_value_endswith,
)
from src.mark import Mark
from src.utils import token


class Sim:
    GEOMETRICAL_CHARACTERISTICS_VALUE: Final = "Геометрические характеристики"

    # про пропуски
    @staticmethod
    def resolve_pass_tz(el, el_new) -> Mark | list:
        if el is not None and el_new is None:
            return Mark.GREEN
        elif el is None and el_new is not None:
            return Mark.RED
        elif el is not None and el_new is not None:
            return [el, el_new]
        else:
            return Mark.GREEN

    @staticmethod
    def compare_analogues(el, el_new) -> Mark:
        name_el = el["name"]
        name_el_new = el_new["name"]

        el_analogues = extract_names_by_meta_iterative(el, Material.ANALOGUES)
        el_new_analogues = extract_names_by_meta_iterative(el_new, Material.ANALOGUES)

        pass_analogues = Sim.resolve_pass_tz(el_analogues, el_new_analogues)
        if isinstance(pass_analogues, Mark):
            return pass_analogues

        if name_el in el_new_analogues or name_el_new in el_analogues:
            return Mark.GREEN
        else:
            return Mark.RED

    @staticmethod
    def __fill_compare_processing_object(tz, tz_new) -> dict[str, Mark]:
        result = dict()

        # Объект обработки
        processing_object = find_meta_value(tz, ProcessingObject.PO)
        processing_object_new = find_meta_value(tz_new, ProcessingObject.PO)

        # Объект обработки -> Подложка / Деталь
        # Может быть либо Подложка, либо Деталь, но есть нюанс в сравнении материалов для Детали
        if find_meta_value(processing_object_new, ProcessingObject.SUBSTRATE):
            is_substrate = True
            processing_object_concrete = find_meta_value(
                processing_object, ProcessingObject.SUBSTRATE
            )
            processing_object_concrete_new = find_meta_value(
                processing_object_new, ProcessingObject.SUBSTRATE
            )
        else:
            is_substrate = False
            processing_object_concrete = find_meta_value(processing_object, ProcessingObject.DETAIL)
            processing_object_concrete_new = find_meta_value(
                processing_object_new, ProcessingObject.DETAIL
            )

        if processing_object_concrete and processing_object_concrete_new:
            pass_mark = Sim.resolve_pass_tz(
                processing_object_concrete, processing_object_concrete_new
            )

            if isinstance(pass_mark, Mark):
                result[
                    ProcessingObject.PO.normalize() + "." + SubstrateDetail.MATERIAL.normalize()
                ] = pass_mark
                result[ProcessingObject.PO.normalize() + "." + SubstrateDetail.MASS.normalize()] = (
                    pass_mark
                )
                result[
                    ProcessingObject.PO.normalize() + "." + SubstrateDetail.GEOM_CHARS.normalize()
                ] = pass_mark
                # В рамках нашей задачи не реализуем - Подложка -> Микроструктура
            elif isinstance(pass_mark, list):
                # Подложка -> Материал
                result_sim_po_materials = Mark.GREEN
                if is_substrate:
                    result_sim_po_materials = Sim.compare_materials(
                        processing_object_concrete, processing_object_concrete_new
                    )
                else:
                    # Деталь -> Материал
                    # Из переписки с Вадимом Андреевичем:
                    #   Если задан материал рабочей поверхности, то сравниваем с ним;
                    #   если не задан, то с материалом основы;
                    #   если вдруг не задан и материал основы, то это пропуск.
                    work_surface = find_meta_value(
                        processing_object_concrete, "Рабочая поверхность"
                    )
                    base = find_meta_value(processing_object_concrete, "Основа")

                    if work_surface:
                        work_surface_new = find_meta_value(
                            processing_object_concrete_new, "Рабочая поверхность"
                        )
                        result_sim_po_materials = Sim.compare_materials(
                            work_surface, work_surface_new
                        )
                    elif base:
                        base_new = find_meta_value(processing_object_concrete_new, "Основа")
                        result_sim_po_materials = Sim.compare_materials(base, base_new)

                result[
                    ProcessingObject.PO.normalize() + "." + SubstrateDetail.MATERIAL.normalize()
                ] = result_sim_po_materials

                # Подложка/Деталь -> Масса
                result_sim_po_mass = Sim.compare_mass(
                    processing_object_concrete, processing_object_concrete_new
                )
                result[ProcessingObject.PO.normalize() + "." + SubstrateDetail.MASS.normalize()] = (
                    result_sim_po_mass
                )

                # Подложка/Деталь -> Геометрические характеристики
                result_sim_po_char = Sim.compare_geometrical_characteristics(
                    processing_object_concrete, processing_object_concrete_new
                )
                result[
                    ProcessingObject.PO.normalize() + "." + SubstrateDetail.GEOM_CHARS.normalize()
                ] = result_sim_po_char

                # В рамках нашей задачи не реализуем - Подложка -> Микроструктура

                return result

        result[ProcessingObject.PO.normalize() + "." + SubstrateDetail.MATERIAL.normalize()] = (
            Mark.GREEN
        )
        result[ProcessingObject.PO.normalize() + "." + SubstrateDetail.MASS.normalize()] = Mark.GREEN
        result[ProcessingObject.PO.normalize() + "." + SubstrateDetail.GEOM_CHARS.normalize()] = (
            Mark.GREEN
        )
        # В рамках нашей задачи не реализуем - Подложка -> Микроструктура

        return result

    @staticmethod
    def __fill_compare_material_for_maintenance(tz, tz_new) -> dict[str, Mark]:
        result = dict()

        material_for_maintenance = find_meta_value(tz, MaterialForMaintenance.MFM)
        material_for_maintenance_new = find_meta_value(tz_new, MaterialForMaintenance.MFM)

        # Уточнял "может ли быть оба" (проволока и порошок), сказали всегда только 1
        if find_meta_value(material_for_maintenance_new, MaterialForMaintenance.METAL_POWDER):
            is_metal_wire = False
            material_for_maintenance_concrete = find_meta_value(
                material_for_maintenance, MaterialForMaintenance.METAL_POWDER
            )
            material_for_maintenance_concrete_new = find_meta_value(
                material_for_maintenance_new, MaterialForMaintenance.METAL_POWDER
            )
        else:
            is_metal_wire = True
            material_for_maintenance_concrete = find_meta_value(
                material_for_maintenance, MaterialForMaintenance.METAL_WIRE
            )
            material_for_maintenance_concrete_new = find_meta_value(
                material_for_maintenance_new, MaterialForMaintenance.METAL_WIRE
            )

        if material_for_maintenance_concrete and material_for_maintenance_concrete_new:
            if is_metal_wire:
                result_mfm = Sim.compare_metal_wire(
                    material_for_maintenance_concrete, material_for_maintenance_concrete_new
                )
            else:
                result_mfm = Sim.compare_metal_powder(
                    material_for_maintenance_concrete, material_for_maintenance_concrete_new
                )

            result[MaterialForMaintenance.MFM.normalize()] = result_mfm
            return result

        result[MaterialForMaintenance.MFM.normalize()] = Mark.GREEN
        return result

    @staticmethod
    def __fill_compare_process_gas(tz, tz_new) -> dict[str, Mark]:
        result = dict()

        # В онтологии этот элемент пустой (даже link нет)...
        pg = find_meta_value(tz, ProcessGas.PG)
        pg_new = find_meta_value(tz_new, ProcessGas.PG)
        pass_mark = Sim.resolve_pass_tz(pg, pg_new)
        if isinstance(pass_mark, list):
            # Технологические газы -> Моногаз
            # В "Онтология архива протоколов технологических операций лазерной обработки" есть "Наполняющий газ",
            #   который по идеи и есть моногаз, поэтому предположил, что оно должно приходить нам примерно в таком виде...
            # Чтобы точно не облажаться, берём окончание названия, причём у первого successors. Это костыль, но данных то нет, делать больше нечего...
            monogas_parent = find_name_value_endswith(pg["successors"][0], ProcessGas.GAS)
            monogas_parent_new = find_name_value_endswith(pg_new["successors"][0], ProcessGas.GAS)

            # Для газовых смесей аналогично, как и с моногазом костыли на костылях из-за отсутствия данных...
            gas_mixture_parent = find_name_value_endswith(
                pg["successors"][0], ProcessGas.GAS_MIXTURE
            )
            gas_mixture_parent_new = find_name_value_endswith(
                pg_new["successors"][0], ProcessGas.GAS_MIXTURE
            )

            # Судя по выводу, у нас может быть либо Моногаз, либо Газовая смесь
            if monogas_parent is not None and monogas_parent_new is not None:
                monogas = find_meta_value(monogas_parent, ProcessGas.GAS.capitalize())
                monogas_new = find_meta_value(monogas_parent_new, ProcessGas.GAS.capitalize())

                result_compare_monogas = Sim.compare_monogas(monogas, monogas_new)
                if result_compare_monogas:
                    result[ProcessGas.PG] = result_compare_monogas
            elif gas_mixture_parent is not None and gas_mixture_parent_new is not None:
                gas_mixture = find_meta_value(monogas_parent, ProcessGas.GAS_MIXTURE.capitalize())
                gas_mixture_new = find_meta_value(
                    monogas_parent_new, ProcessGas.GAS_MIXTURE.capitalize()
                )

                result_compare_gas_mixture = Sim.compare_gas_mixture(gas_mixture, gas_mixture_new)
                if result_compare_gas_mixture:
                    result[ProcessGas.PG.normalize()] = result_compare_gas_mixture

            return result
        else:
            result[ProcessGas.PG.normalize()] = pass_mark

        return result

    @staticmethod
    def __fill_compare_ror(tz, tz_new) -> dict[str, Mark]:
        result = dict()

        ror = find_meta_value(tz, RequirementsOperationResult.ROR)
        ror_new = find_meta_value(tz_new, RequirementsOperationResult.ROR)
        pass_mark = Sim.resolve_pass_tz(ror, ror_new)

        if isinstance(pass_mark, list):
            # Требования к результату операции -> Геометрические характеристики
            result_sim_ror_char = Sim.compare_geometrical_characteristics(ror, ror_new)
            result[
                RequirementsOperationResult.ROR.normalize()
                + "."
                + RequirementsOperationResult.GEOM_CHARS.normalize()
            ] = result_sim_ror_char

            # Требования к результату операции -> Дефекты наплавленного материала
            # Внутри "Дефекты наплавленного материала" лежат обычные дефекты
            defects_deposited_material = find_meta_value(
                ror, RequirementsOperationResult.DEFECTS_DEPOSITED_MATERIAL
            )
            defects_deposited_material_new = find_meta_value(
                ror_new, RequirementsOperationResult.DEFECTS_DEPOSITED_MATERIAL
            )

            result_defects_pass = Sim.resolve_pass_tz(
                defects_deposited_material, defects_deposited_material_new
            )
            if isinstance(result_defects_pass, Mark):
                result[
                    RequirementsOperationResult.ROR.normalize()
                    + "."
                    + RequirementsOperationResult.DEFECTS_DEPOSITED_MATERIAL.normalize()
                ] = result_defects_pass
            elif isinstance(result_defects_pass, list):
                result_sim_ror_defects = Sim.compare_defects(
                    defects_deposited_material, defects_deposited_material_new
                )
                result[
                    RequirementsOperationResult.ROR.normalize()
                    + "."
                    + RequirementsOperationResult.DEFECTS_DEPOSITED_MATERIAL.normalize()
                ] = result_sim_ror_defects

            # Требования к результату операции -> Элементный состав
            # Имеем снова неполные данные, так что действуем по догадке
            elemental_composition = find_meta_value(
                ror, RequirementsOperationResult.ELEMENTAL_COMPOSITION
            )
            elemental_composition_new = find_meta_value(
                ror_new, RequirementsOperationResult.ELEMENTAL_COMPOSITION
            )

            result_elemental_composition_pass = Sim.resolve_pass_tz(
                elemental_composition, elemental_composition_new
            )
            if isinstance(result_elemental_composition_pass, Mark):
                result[
                    RequirementsOperationResult.ROR.normalize()
                    + "."
                    + RequirementsOperationResult.ELEMENTAL_COMPOSITION.normalize()
                ] = result_elemental_composition_pass
            elif isinstance(result_elemental_composition_pass, list):
                # В онтологии снова неполные данные, где ссылка на структуру элементного состава,
                #   поэтому страхуемся на такой случай и учитываем link
                if "link" in elemental_composition:
                    path, start_target = split_path(elemental_composition["link"])
                    response_el = get_with_cache_from_repo(path, token, start_target)
                    elemental_composition = find_name_value(
                        response_el, elemental_composition["name"]
                    )

                if "link" in elemental_composition_new:
                    path_new, new_start_target = split_path(elemental_composition_new["link"])
                    new_response_el = get_with_cache_from_repo(path_new, token, new_start_target)
                    elemental_composition_new = find_name_value(
                        new_response_el, elemental_composition_new["name"]
                    )

                result_elemental_composition = Sim.elemental_composition_compare(
                    elemental_composition, elemental_composition_new
                )
                result[
                    RequirementsOperationResult.ROR.normalize()
                    + "."
                    + RequirementsOperationResult.ELEMENTAL_COMPOSITION.normalize()
                ] = result_elemental_composition

            # В рамках нашей задачи не реализуем (написано в требованиях): Требования к результату операции -> Микроструктура

            return result

        else:
            result[
                RequirementsOperationResult.ROR.normalize()
                + "."
                + RequirementsOperationResult.GEOM_CHARS.normalize()
            ] = Mark.GREEN
            result[
                RequirementsOperationResult.ROR.normalize()
                + "."
                + RequirementsOperationResult.DEFECTS_DEPOSITED_MATERIAL.normalize()
            ] = Mark.GREEN
            result[
                RequirementsOperationResult.ROR.normalize()
                + "."
                + RequirementsOperationResult.ELEMENTAL_COMPOSITION.normalize()
            ] = Mark.GREEN

        return result

    @staticmethod
    def compare(tz, tz_new) -> dict[str, int]:
        result = dict()

        # Сравнение Объектов обработки
        result.update(Sim.__fill_compare_processing_object(tz, tz_new))

        # Материал для выполнения ТО
        result.update(Sim.__fill_compare_material_for_maintenance(tz, tz_new))

        # Технологические газы
        result.update(Sim.__fill_compare_process_gas(tz, tz_new))

        # Требования к результату операции
        result.update(Sim.__fill_compare_ror(tz, tz_new))

        return result

    @staticmethod
    def compare_geometrical_characteristics(tz, tz_new) -> Mark:
        def compare_subtree(subtree1, subtree2):
            if isinstance(subtree1, dict) and isinstance(subtree2, dict):
                if subtree1.keys() != subtree2.keys():
                    return False
                for key in subtree1:
                    if key != "id":
                        if not compare_subtree(subtree1[key], subtree2[key]):
                            return False
                return True
            elif isinstance(subtree1, list) and isinstance(subtree2, list):
                if len(subtree1) != len(subtree2):
                    return False
                for i in range(len(subtree1)):
                    if not compare_subtree(subtree1[i], subtree2[i]):
                        return False
                return True
            else:
                return subtree1 == subtree2

        el = find_name_value(tz, Sim.GEOMETRICAL_CHARACTERISTICS_VALUE)
        el_new = find_name_value(tz_new, Sim.GEOMETRICAL_CHARACTERISTICS_VALUE)

        # default
        pass_result = Sim.resolve_pass_tz(el, el_new)
        if isinstance(pass_result, Mark):
            return pass_result

        if compare_subtree(el["successors"], el_new["successors"]):
            return Mark.GREEN
        else:
            return Mark.RED

    @staticmethod
    def compare_defects(tz, tz_new) -> Mark:
        def extract_defect_value(data):
            for requirement in data.get("successors", []):
                for defect_group in requirement.get("successors", []):
                    for defect in defect_group.get("successors", []):
                        if defect["name"] == "Наличе пор и дефектов":
                            for value in defect.get("successors", []):
                                return value["value"]
            return None

        value1 = extract_defect_value(tz)
        value2 = extract_defect_value(tz_new)

        # default
        pass_result = Sim.resolve_pass_tz(value1, value2)
        if not isinstance(pass_result, list):
            return pass_result

        difference = abs(value1 - value2)

        if difference < 10:
            return Mark.GREEN
        elif 10 <= difference <= 30:
            return Mark.ORANGE
        elif difference > 30:
            return Mark.RED

    @staticmethod
    def compare_materials(tz, tz_new) -> Mark:
        el = find_meta_value(tz, SubstrateDetail.MATERIAL)
        el_new = find_meta_value(tz_new, SubstrateDetail.MATERIAL)

        # default
        pass_result = Sim.resolve_pass_tz(el, el_new)
        if not isinstance(pass_result, list):
            return pass_result

        # Так как в материалах эталонных данных почти ничего и нет, нам нужно вытащить доп информацию из link
        path, start_target = split_path(el["link"])
        response_el = get_with_cache_from_repo(path, token, start_target)
        true_el = find_name_value(response_el, el["name"])

        path_new, new_start_target = split_path(el_new["link"])
        new_response_el = get_with_cache_from_repo(path_new, token, new_start_target)
        true_el_new = find_name_value(new_response_el, el_new["name"])

        pass_result = Sim.resolve_pass_tz(true_el, true_el_new)
        if not isinstance(pass_result, list):
            return pass_result

        # 1. Один из материалов явно указан в перечне аналогичных для другого
        result_compare_analogues = Sim.compare_analogues(true_el, true_el_new)
        if result_compare_analogues != Mark.RED:
            return result_compare_analogues

        # 2. Принадлежность материалов разным классам
        name_el_new = el_new["name"]
        sub_start_target = replace_path_last_part(start_target, name_el_new)
        new_response_el = get_with_cache_from_repo(path, token, sub_start_target)
        if find_name_value(new_response_el, name_el_new) is None:
            return Mark.RED

        # Подобие элементных составов
        return Sim.elemental_composition_compare(true_el, true_el_new)

    # Немного модифицированный метод по сравнению с sim_element_contains.ipynb
    @staticmethod
    def elemental_composition_compare(json1, json2) -> Mark:
        osnov_1 = find_meta_value(json1, ElementalComposition.BASE)
        osnov_2 = find_meta_value(json2, ElementalComposition.BASE)

        pass_result = Sim.resolve_pass_tz(osnov_1, osnov_2)
        if not isinstance(pass_result, list):
            return pass_result

        values_1 = [item["value"] for item in osnov_1["successors"]]
        values_2 = [item["value"] for item in osnov_2["successors"]]

        if values_1 == values_2:
            # default
            pass_result = Sim.resolve_pass_tz(json1, json2)
            if not isinstance(pass_result, list):
                return pass_result
            else:
                pair_counter = 0  # счетчик пар
                green_counter = 0  # счётчик зелёных пар

                elemental_composition1 = find_meta_value(json1, ElementalComposition.EC)
                elemental_composition2 = find_meta_value(json2, ElementalComposition.EC)

                for component in elemental_composition1["successors"]:
                    if component["meta"] != ElementalComposition.COMPONENT:
                        continue

                    chim_element_1 = find_meta_value(component, ElementalComposition.CHIM_ELEMENT)

                    if chim_element_1 is None or chim_element_1.get("name", None) is None:
                        continue

                    for component_2 in elemental_composition2["successors"]:
                        if component["meta"] != ElementalComposition.COMPONENT:
                            continue

                        chim_element_2 = find_name_value(component_2, chim_element_1["name"])

                        if chim_element_2 is not None:
                            pair_counter += 1

                            number_interval_1 = find_meta_value(
                                chim_element_1["successors"], IntervalType.NUM_INTERVAL
                            )
                            number_interval_2 = find_meta_value(
                                chim_element_2["successors"], IntervalType.NUM_INTERVAL
                            )

                            not_bigger_1 = find_meta_value(chim_element_1, IntervalType.NOT_BIGGER)
                            not_bigger_2 = find_meta_value(chim_element_2, IntervalType.NOT_BIGGER)

                            # 3.1
                            if number_interval_1 is not None and number_interval_2 is not None:
                                low_border_1 = find_meta_value(
                                    number_interval_1, IntervalType.LOW_BORDER
                                )
                                top_border_1 = find_meta_value(
                                    number_interval_1, IntervalType.TOP_BORDER
                                )

                                interval_1 = Interval(
                                    float(low_border_1["successors"][0]["value"]),
                                    float(top_border_1["successors"][0]["value"]),
                                )

                                low_border_2 = find_meta_value(
                                    number_interval_2, IntervalType.LOW_BORDER
                                )
                                top_border_2 = find_meta_value(
                                    number_interval_2, IntervalType.TOP_BORDER
                                )

                                interval_2 = Interval(
                                    float(low_border_2["successors"][0]["value"]),
                                    float(top_border_2["successors"][0]["value"]),
                                )

                                if interval_1.contains_interval(interval_2):
                                    green_counter += 1

                            # 3.2
                            elif (not_bigger_1 is not None and number_interval_2 is not None) or (
                                not_bigger_2 is not None and number_interval_1 is not None
                            ):

                                if not_bigger_1 is not None:
                                    interval_value_1 = find_meta_value(
                                        not_bigger_1["successors"], "Числовое значение"
                                    )

                                    interval_1 = Interval(0.0, float(interval_value_1["value"]))

                                    low_border_2 = find_meta_value(
                                        number_interval_2, IntervalType.LOW_BORDER
                                    )
                                    top_border_2 = find_meta_value(
                                        number_interval_2, IntervalType.TOP_BORDER
                                    )

                                    interval_2 = Interval(
                                        float(low_border_2["successors"][0]["value"]),
                                        float(top_border_2["successors"][0]["value"]),
                                    )

                                    if interval_1.contains_interval(interval_2):
                                        green_counter += 1

                            elif not_bigger_1 is not None and not_bigger_2 is not None:  # 3.3
                                interval_value_2 = find_meta_value(
                                    chim_element_2["successors"], "Числовое значение"
                                )
                                interval_value_1 = find_meta_value(
                                    chim_element_1["successors"], "Числовое значение"
                                )

                                if interval_value_1 == interval_value_2:
                                    green_counter += 1

            if green_counter / pair_counter >= 0.9:
                return Mark.GREEN
            elif green_counter / pair_counter >= 0.7:
                return Mark.ORANGE
            else:
                return Mark.RED

        else:
            return Mark.RED

    @staticmethod
    def compare_mass(tz, tz_new) -> Mark:
        def get_mass_interval(local_mass, local_intervals):
            """Находит интервал, содержащий массу."""
            for interval in local_intervals:
                if interval.contains_value(local_mass):
                    return interval
            return None

        el = find_meta_value(tz, SubstrateDetail.MASS)
        el_new = find_meta_value(tz_new, SubstrateDetail.MASS)

        # default
        pass_result = Sim.resolve_pass_tz(el, el_new)
        if not isinstance(pass_result, list):
            return pass_result

        # В онтологии почему-то бывают ситуации, когда нет Значения у массы...
        pass_mass_value = Sim.resolve_pass_tz(
            find_meta_value(el, "Значение"), find_meta_value(el_new, "Значение")
        )
        if not isinstance(pass_mass_value, list):
            return pass_mass_value

        mass = find_meta_value(find_meta_value(el, "Значение"), "Числовое значение")["value"]
        mass_new = find_meta_value(find_meta_value(el_new, "Значение"), "Числовое значение")[
            "value"
        ]

        intervals = [
            Interval(0.01, 0.1),
            Interval(0.1, 1.0),
            Interval(1.0, 10.0),
            Interval(10.0, 100.0),
            Interval(100.0, 400.0),
        ]

        interval1 = get_mass_interval(mass, intervals)
        interval2 = get_mass_interval(mass_new, intervals)

        # 1
        if interval1 == interval2:  # Используем __eq__ из класса Interval
            return Mark.GREEN
        # 2
        elif abs(intervals.index(interval1) - intervals.index(interval2)) > 1:
            return Mark.RED
        else:  # 3. Смежные интервалы
            subinterval_len = interval2.right / 2
            midpoint = subinterval_len

            prev_subinterval_len = (
                intervals[intervals.index(interval2) - 1].right / 2
                if intervals.index(interval2) != 0
                else 0
            )
            mid_midpoint = (
                interval2.left + prev_subinterval_len
                if intervals.index(interval2) != 0
                else interval2.right
            )

            if interval2.left <= mass_new < mid_midpoint:
                return Mark.GREEN
            elif mid_midpoint < mass_new <= midpoint:
                return Mark.ORANGE
            elif midpoint <= mass_new <= interval2.right:
                return Mark.RED

    @staticmethod
    def __compare_material_for_maintenance_first_and_second_step(tz, tz_new) -> Mark | list:
        # default
        el, el_new = tz, tz_new
        pass_result = Sim.resolve_pass_tz(tz, tz_new)
        if isinstance(pass_result, Mark):
            return pass_result

        # Так как в материалах эталонных данных почти ничего и нет, нам нужно вытащить доп информацию из link
        path, start_target = split_path(el["link"])
        response_el = get_with_cache_from_repo(path, token, start_target)
        true_el = find_name_value(response_el, el["name"])

        path_new, new_start_target = split_path(el_new["link"])
        new_response_el = get_with_cache_from_repo(path_new, token, new_start_target)
        true_el_new = find_name_value(new_response_el, el_new["name"])

        pass_result = Sim.resolve_pass_tz(true_el, true_el_new)
        if not isinstance(pass_result, list):
            return pass_result

        # 1. Один из материалов явно указан в перечне аналогичных для другого
        result_compare_analogues = Sim.compare_analogues(true_el, true_el_new)
        if result_compare_analogues != Mark.RED:
            return result_compare_analogues

        # 2. Принадлежность материалов разным классам
        name_el_new = el_new["name"]
        sub_start_target = replace_path_last_part(start_target, name_el_new)
        new_response_el = get_with_cache_from_repo(path, token, sub_start_target)
        if find_name_value(new_response_el, name_el_new) is None:
            return Mark.RED

        return [true_el, true_el_new]

    @staticmethod
    def compare_metal_powder(tz, tz_new) -> Mark:
        first_step_result = Sim.__compare_material_for_maintenance_first_and_second_step(tz, tz_new)
        if not isinstance(first_step_result, list):
            return first_step_result
        else:
            true_el, true_el_new = first_step_result

        def compare_third_part_metal_powder(mp, mp_new) -> Mark:
            # 3.
            # 3.1. Подобие сплавов = подобие материалов
            # Хитрое вытаскивание, так как зачем-то в Материале существует ненужная вложенность
            material = find_meta_value(mp, MetalPowder.MATERIAL)
            material_new = find_meta_value(mp_new, MetalPowder.MATERIAL)

            pass_result_material = Sim.resolve_pass_tz(material, material_new)
            if isinstance(pass_result_material, Mark):
                alloy_similarity = pass_result_material
            else:
                material_sub = find_meta_value(material, MetalPowder.MATERIAL)
                material_sub_new = find_meta_value(material_new, MetalPowder.MATERIAL)
                alloy_similarity = Sim.compare_materials(
                    material_sub["successors"], material_sub_new["successors"]
                )
            # Конец хитрого вытаскивания

            # 3.2. Подобие методов получения
            # На всякий случай предусматриваем ситуацию когда его нет, т.к. сейчас он никогда не приходит
            mt_method_of_obtaining = find_meta_value(mp, MetalPowder.METHOD_OF_OBTAINING)
            mt_method_of_obtaining_new = find_meta_value(mp_new, MetalPowder.METHOD_OF_OBTAINING)
            mt_pass_result = Sim.resolve_pass_tz(mt_method_of_obtaining, mt_method_of_obtaining_new)

            if isinstance(mt_pass_result, Mark):
                method_similarity = mt_pass_result
            else:
                # Сделал по предположению как оно выглядит
                method = find_meta_value(mp, MetalPowder.METHOD_OF_OBTAINING)["name"]
                method_new = find_meta_value(mp_new, MetalPowder.METHOD_OF_OBTAINING)["name"]
                method_similarity = Mark.GREEN if method == method_new else Mark.RED

            # 3.3. Подобие размеров частиц
            # Объявленные интервалы этого пункта
            # Раскраска интервала разными цветами в постановке задачи не играет никакой роли
            intervals = [
                Interval(0.0, 50.0),
                Interval(50.0, 100.0),
                Interval(100.0, 200.0),
                Interval(200.0, 250.0),
                Interval(250.0, sys.float_info.max),
            ]
            # Извлекли интервалы входных данных
            particle_size = find_meta_value(mp, MetalPowder.PARTICLE_SIZE)
            particle_size_new = find_meta_value(mp_new, MetalPowder.PARTICLE_SIZE)

            # Пропуск
            pass_result = Sim.resolve_pass_tz(particle_size, particle_size_new)
            size_similarity = Mark.GREEN
            if isinstance(pass_result, Mark):
                size_similarity = pass_result
            else:
                min_max_particle_size = find_meta_value(
                    particle_size, MetalPowder.MIN_MAX_PARTICLE_SIZE
                )
                min_max_particle_size_new = find_meta_value(
                    particle_size_new, MetalPowder.MIN_MAX_PARTICLE_SIZE
                )

                # Снова ситуация, когда что-то пустое
                pass_result = Sim.resolve_pass_tz(min_max_particle_size, min_max_particle_size_new)
                if isinstance(pass_result, Mark):
                    size_similarity = pass_result
                else:
                    # [a, b]
                    min_particle_size = find_meta_value(
                        find_meta_value(min_max_particle_size, IntervalType.LOW_BORDER),
                        "Числовое значение",
                    )["value"]
                    max_particle_size = find_meta_value(
                        find_meta_value(min_max_particle_size, IntervalType.TOP_BORDER),
                        "Числовое значение",
                    )["value"]
                    interval = Interval(min_particle_size, max_particle_size)

                    # [c, d]
                    min_particle_size = find_meta_value(
                        find_meta_value(min_max_particle_size_new, IntervalType.LOW_BORDER),
                        "Числовое значение",
                    )["value"]
                    max_particle_size = find_meta_value(
                        find_meta_value(min_max_particle_size_new, IntervalType.TOP_BORDER),
                        "Числовое значение",
                    )["value"]
                    interval_new = Interval(min_particle_size, max_particle_size)

                    def find_id_containing_interval(need_interval, input_intervals):
                        """Находит интервал из списка, который полностью содержит входной интервал."""
                        for idx, input_interval in enumerate(input_intervals):
                            if interval.contains_interval(need_interval):
                                return idx
                        return None

                    # both in green interval [100, 200]
                    containing_interval = find_id_containing_interval(interval, intervals)
                    containing_interval_new = find_id_containing_interval(interval, intervals)
                    if intervals[2].contains_interval(interval) and intervals[2].contains_interval(
                        interval_new
                    ):
                        size_similarity = Mark.GREEN
                    # интервалы не включены целиком в смежные
                    elif (containing_interval and containing_interval_new) and (
                        containing_interval - containing_interval_new
                    ) > 1:
                        size_similarity = Mark.RED
                    # интервалы включены целиком в смежные
                    elif (containing_interval and containing_interval_new) and (
                        containing_interval - containing_interval_new
                    ) == 1:
                        size_similarity = Mark.ORANGE
                    # границы интервалов принадлежат разным границам
                    else:
                        # [a, b] ⊂ [c, d] или [c, d] ⊂ [a, b]
                        if interval.contains_interval(
                            interval_new
                        ) or interval_new.contains_interval(interval):
                            size_similarity = Mark.GREEN
                        # [a, b] ∩ [c, d] ≠ ∅
                        elif interval.intersects(interval_new):
                            size_similarity = Mark.ORANGE
                        # [a, b] ∩ [c, d] = ∅
                        elif not interval.intersects(interval_new):
                            size_similarity = Mark.RED

            # Определение цвета по наименьшей похожести (Пункт 3)
            similarities = {alloy_similarity, method_similarity, size_similarity}
            print(similarities)

            # Для 3.1 - 3.3 из трех цветов всегда берется цвет, означающий наименьшую похожесть.
            return Mark(max(similarities))

        return compare_third_part_metal_powder(true_el, true_el_new)

    @staticmethod
    def compare_metal_wire(tz, tz_new) -> Mark:
        first_step_result = Sim.__compare_material_for_maintenance_first_and_second_step(tz, tz_new)
        if isinstance(first_step_result, Mark):
            return first_step_result
        else:
            true_el, true_el_new = first_step_result

        def compare_third_part_metal_wire(mw, mw_new):
            def get_diameter_interval(local_diameter, local_intervals):
                """Находит интервал, содержащий диаметр."""
                for interval in local_intervals:
                    if interval.contains_value(local_diameter):
                        return interval
                return None

            # 3.
            # 3.1. Подобие сплавов
            # Хитрое вытаскивание, так как зачем-то в Материале существует вложенность
            material = find_meta_value(mw, MetalPowder.MATERIAL)
            material_new = find_meta_value(mw_new, MetalPowder.MATERIAL)

            pass_result_material = Sim.resolve_pass_tz(material, material_new)
            if not isinstance(pass_result_material, list):
                alloy_similarity = pass_result_material
            else:
                material_sub = find_meta_value(material, MetalPowder.MATERIAL)
                material_sub_new = find_meta_value(material_new, MetalPowder.MATERIAL)
                alloy_similarity = Sim.compare_materials(material_sub, material_sub_new)
            # Конец хитрого вытаскивания

            if not alloy_similarity:
                return Mark.RED
            # 3.2. Подобие диаметров проволок
            else:
                # Объявленные интервалы этого пункта
                # Раскраска интервала разными цветами в постановке задачи не играет никакой роли
                intervals = [
                    Interval(0.0, 0.5),
                    Interval(0.5, 1.0),
                    Interval(1.0, 1.5),
                    Interval(1.5, 2.0),
                    Interval(2.0, sys.float_info.max),
                ]
                # Извлекаем значения диаметров
                # Структура Диаметра по своему виду напоминает Нижнюю/Верхнюю границу
                diameter = find_meta_value(mw, "Диаметр")
                diameter_new = find_meta_value(mw_new, "Диаметр")

                # Пропуск
                pass_result = Sim.resolve_pass_tz(diameter, diameter_new)
                if not isinstance(pass_result, list):
                    return pass_result
                else:
                    diameter_value_obj = find_meta_value(diameter, "Числовое значение")
                    diameter_new_value_obj = find_meta_value(diameter_new, "Числовое значение")

                    interval1 = get_diameter_interval(diameter_value_obj["value"], intervals)
                    interval2 = get_diameter_interval(diameter_new_value_obj["value"], intervals)
                    # 3.2.1. Пара принадлежит одному и тому же интервалу
                    if interval1 == interval2:
                        return Mark.GREEN
                    # 3.2.2. Смежные интервалы
                    elif abs(intervals.index(interval1) - intervals.index(interval2)) == 1:
                        return Mark.ORANGE
                    # 3.2.3. Не смежные интервалы
                    elif abs(intervals.index(interval1) - intervals.index(interval2)) > 1:
                        return Mark.RED

        return compare_third_part_metal_wire(true_el, true_el_new)

    @staticmethod
    def compare_monogas(json1, json2) -> Mark:
        gas_class1 = find_meta_value(json1, "Класс газов")
        gas_class2 = find_meta_value(json2, "Класс газов")

        if not isinstance(Sim.resolve_pass_tz(json1, json2), list):
            return Sim.resolve_pass_tz(json1, json2)

        # 1. у газов разные классы
        if gas_class1["name"] != gas_class2["name"]:
            return Mark.RED
        else:
            gas_name1 = find_meta_value(gas_class1, "Газ")
            gas_name2 = find_meta_value(gas_class2, "Газ")

            # 2. у газов не одинаковые имена
            if gas_name1["name"] != gas_name2["name"]:
                return Mark.RED
            # 3. Имеют одинаковые названия
            else:
                gas_sort1 = find_meta_value(gas_name1, "Сорт")
                gas_sort2 = find_meta_value(gas_name2, "Сорт")

                gas_mark1 = find_meta_value(gas_name1, "Марка")
                gas_mark2 = find_meta_value(gas_name2, "Марка")

                # 3.1 Есть и сорт и марка
                if (
                    gas_sort1 is not None
                    and gas_sort2 is not None
                    and gas_mark1 is not None
                    and gas_mark2 is not None
                ):
                    # 3.1.1
                    if gas_sort1 == gas_sort2 and gas_mark1 == gas_mark2:
                        return Mark.GREEN
                    # 3.1.2
                    else:
                        return Mark.ORANGE
                # 3.2 Есть неполный набор о сорте и марке газов
                else:
                    # 3.2.1
                    # есть сорт газов
                    if gas_sort1 is not None and gas_sort2 is not None:
                        if gas_sort1 == gas_sort2:
                            return Mark.GREEN
                        else:
                            return Mark.ORANGE

                    # есть марки газа
                    elif gas_mark1 is not None and gas_mark2 is not None:
                        if gas_mark1 == gas_mark2:
                            return Mark.GREEN
                        else:
                            return Mark.ORANGE

                    # 3.2.2.если данные в разных пармаетрах
                    elif (gas_sort1 and gas_mark2) or (gas_mark1 and gas_sort2):
                        return Mark.ORANGE
                    # 3.3
                    elif (
                        (gas_sort1 and gas_mark1)
                        is not None
                        != (gas_sort2 and gas_mark2)
                        is not None
                    ):
                        if gas_sort1 == gas_sort2 or gas_mark1 == gas_mark2:
                            return Mark.GREEN
                        else:
                            return Mark.ORANGE
                    # 3.4 Если для одного из моногазов не указаны его сорт и марка, а для другого указаны, то пара отмечается как оранжевая.
                    elif ((gas_sort1 and gas_mark1) is not None) != (
                        (gas_sort2 and gas_mark2) is not None
                    ):
                        return Mark.ORANGE
                    # 3.5. Если ни для одного из моногазов не указаны их сорт и марка, то пара отмечается как зелёная.
                    else:
                        return Mark.GREEN

    @staticmethod
    def compare_gas_mixture(json1, json2) -> Mark:
        # Сравнение готовых смесей
        if "link" in json1["successors"][0]:
            gasmix_name_1 = json1["successors"][0]["name"]
            gasmix_name_2 = json2["successors"][0]["name"]
            if gasmix_name_1 == gasmix_name_2:
                return Mark.GREEN
            else:
                return Mark.RED

        # Приготовление смесей на месте

        # Посчитать сколько газов в газовой смеси
        gasmix_el_comp_1 = find_meta_value(json1, "Соотношение компонентов газовой смеси")
        elements_names_1 = [
            item["successors"][0]["name"] for item in gasmix_el_comp_1["successors"]
        ]

        # массив для результатов сравнений
        color_results = []

        gasmix_el_comp_2 = find_meta_value(json2, "Соотношение компонентов газовой смеси")
        elements_names_2 = [
            item["successors"][0]["name"] for item in gasmix_el_comp_2["successors"]
        ]

        # 1. Для каждого газа из смеси1 должен найтись такой же в смеси2

        if set(elements_names_1) != set(elements_names_2):
            return Mark.RED

        # 3. Процентное содержание (объемная доля) соответствующих моногазов
        for element in gasmix_el_comp_1["successors"]:
            for element2 in gasmix_el_comp_2["successors"]:
                gas_1 = find_meta_value(element, "Газ")
                gas_name_1 = gas_1["name"]
                gas_2 = find_name_value(element2, gas_name_1)
                if gas_2 is None:
                    continue
                gas_name_2 = gas_2["name"]

                if gas_name_1 == gas_name_2:
                    concentrat_1 = find_meta_value(element, "Концентрация")
                    concentrat_1 = concentrat_1["successors"][0]["value"]

                    concentrat_2 = find_meta_value(element2, "Концентрация")
                    concentrat_2 = concentrat_2["successors"][0]["value"]

                    if abs(concentrat_1 - concentrat_2) < 10:
                        color_results.append(Mark.GREEN)
                    elif abs(concentrat_1 - concentrat_2) < 30:
                        color_results.append(Mark.ORANGE)
                    else:
                        color_results.append(Mark.RED)

        c = Counter(color_results)

        return c.most_common(1)[0][0]
