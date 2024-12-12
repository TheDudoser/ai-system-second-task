import unittest
from src.sim import Sim
from src.mark import Mark
from tests.utils import load_fixture


class TestSim(unittest.TestCase):
    ###> geometrical_characteristics ###
    def test_green_compare_geometrical_characteristics(self):
        tz = load_fixture("geometrical_characteristics/tz.json")
        tz_other_name_in_subtree = load_fixture("geometrical_characteristics/tz_other_name_in_subtree.json")
        self.assertEqual(Mark.RED, Sim.compare_geometrical_characteristics(tz, tz_other_name_in_subtree))

    def test_eq_compare_geometrical_characteristics(self):
        tz = load_fixture("geometrical_characteristics/tz.json")
        self.assertEqual(Mark.GREEN, Sim.compare_geometrical_characteristics(tz, tz))

    def test_red_compare_geometrical_characteristics(self):
        tz = load_fixture("geometrical_characteristics/tz.json")
        tz_red = load_fixture("geometrical_characteristics/tz_red.json")
        self.assertEqual(Mark.RED, Sim.compare_geometrical_characteristics(tz, tz_red))

    def test_pass_archive_compare_geometrical_characteristics(self):
        tz = load_fixture("geometrical_characteristics/tz.json")
        tz_pass = load_fixture("geometrical_characteristics/tz_pass.json")
        self.assertEqual(Mark.RED, Sim.compare_geometrical_characteristics(tz_pass, tz))

    def test_pass_new_compare_geometrical_characteristics(self):
        tz = load_fixture("geometrical_characteristics/tz.json")
        tz_pass = load_fixture("geometrical_characteristics/tz_pass.json")
        self.assertEqual(Mark.GREEN, Sim.compare_geometrical_characteristics(tz, tz_pass))
    ###< geometrical_characteristics ###

    ###> defects ###
    def test_green_compare_defects(self):
        tz = load_fixture("defects/tz.json")
        tz_green = load_fixture("defects/tz_green.json")
        self.assertEqual(Mark.GREEN, Sim.compare_defects(tz, tz_green))

    def test_zero_diff_compare_defects(self):
        tz = load_fixture("defects/tz.json")
        self.assertEqual(Mark.GREEN, Sim.compare_defects(tz, tz))

    def test_pass_new_compare_defects(self):
        tz = load_fixture("defects/tz.json")
        tz_pass = load_fixture("defects/tz_pass.json")
        self.assertEqual(Mark.GREEN, Sim.compare_defects(tz, tz_pass))

    def test_pass_archive_compare_defects(self):
        tz = load_fixture("defects/tz.json")
        tz_pass = load_fixture("defects/tz_pass.json")
        self.assertEqual(Mark.RED, Sim.compare_defects(tz_pass, tz))

    def test_orange_compare_defects(self):
        tz = load_fixture("defects/tz.json")
        tz_orange = load_fixture("defects/tz_orange.json")
        self.assertEqual(Mark.ORANGE, Sim.compare_defects(tz, tz_orange))
    ###< defects ###

    ###> materials ###
    # У ДВО РАН нет примеров с аналогами на текущий момент...
    def test_material_in_analogues(self):
        pass

    def test_materials_in_not_class(self):
        tz = load_fixture("materials/tz.json")
        tz_not_in_class = load_fixture("materials/tz_not_in_class.json")
        self.assertEqual(Mark.RED, Sim.compare_materials(tz, tz_not_in_class))

    def test_materials_in_class(self):
        tz = load_fixture("materials/tz.json")
        print(Sim.compare_materials(tz, tz))

    def test_materials_detail(self):
        # TODO: Наплавка на основе Олова, сказали что добавили рабочую поверхность
        # TODO: Уточнения требований от Вадима
        pass
    ###< materials ###

    ###> mass ###
    def test_mass_one_interval(self):
        # 1 пункт
        tz_first_interval = load_fixture("mass/tz_first_interval.json")
        tz_new_first_interval = load_fixture("mass/tz_new_first_interval.json")
        self.assertEqual(Mark.GREEN, Sim.compare_materials(tz_first_interval, tz_new_first_interval))

        tz_fifth_interval = load_fixture("mass/tz_fifth_interval.json")
        tz_new_fifth_interval = load_fixture("mass/tz_new_fifth_interval.json")
        self.assertEqual(Mark.GREEN, Sim.compare_mass(tz_fifth_interval, tz_new_fifth_interval))

    def test_mass_not_adjacent(self):
        # 2 пункт
        tz_first_interval = load_fixture("mass/tz_first_interval.json")
        tz_fifth_interval = load_fixture("mass/tz_fifth_interval.json")

        self.assertEqual(Mark.RED, Sim.compare_mass(tz_first_interval, tz_fifth_interval))

    def test_mass_adjacent(self):
        # 3 пункт
        # 3.1
        tz_value_015 = load_fixture("mass/tz_value_015.json")
        tz_value_006 = load_fixture("mass/tz_value_006.json")
        tz_value_2 = load_fixture("mass/tz_value_1_and_2.json")

        self.assertEqual(Mark.GREEN, Sim.compare_mass(tz_value_015, tz_value_2))
        self.assertEqual(Mark.GREEN, Sim.compare_mass(tz_value_015, tz_value_006))

        # 3.2
        tz_value_2 = load_fixture("mass/tz_value_2.json")
        tz_value_20 = load_fixture("mass/tz_value_20.json")

        self.assertEqual(Mark.ORANGE, Sim.compare_mass(tz_value_2, tz_value_20))

        # 3.3
        tz_value_20 = load_fixture("mass/tz_value_20.json")
        tz_value_300 = load_fixture("mass/tz_value_300.json")

        self.assertEqual(Mark.RED, Sim.compare_mass(tz_value_20, tz_value_300))
    ###< mass ###

    ###> Подобие элементных составов ###
    def test_elemental_composition_identical_compare(self):
        tz = load_fixture("elemental_composition/St3sp.json")
        self.assertEqual(Mark.GREEN, Sim.elemental_composition_compare(tz, tz))

    # Одинаковая основа, разные элементы
    def test_elemental_composition_not_identical_compare(self):
        tz = load_fixture("elemental_composition/St3sp.json")
        tz_new = load_fixture("elemental_composition/12X18H10T.json")
        self.assertEqual(Mark.RED, Sim.elemental_composition_compare(tz, tz_new))
    ###< Подобие элементных составов ###

    ###> Металлический порошок ###
    # Тут пока один тест, потому что в онтологии кучу всего нет...
    def test_compare_metal_powder(self):
        tz = load_fixture("metal_powders/default.json")
        self.assertEqual(Mark.RED, Sim.compare_metal_powder(tz, tz))
    ###< Металлический порошок ###

    ###> Металлическая проволока ###
    # TODO: Нет тестов, потому что у ДВО РАН сейчас есть только онтология (структура),
    #   а мы тянем link и подставить своё я не могу из-за этого...
    def test_compare_metal_wire(self):
        pass
    ###< Металлическая проволока ###

    ###> Моногаз ###
    def test_compare_identical_monogas(self):
        tz = load_fixture("monogas/default.json")
        self.assertEqual(Mark.GREEN, Sim.compare_monogas(tz, tz))

    # Разные названия газов
    def test_compare_other_monogas(self):
        tz = load_fixture("monogas/default.json")
        tz_new = load_fixture("monogas/other_gas_without_sort_marka.json")
        self.assertEqual(Mark.RED, Sim.compare_monogas(tz, tz_new))

    # Марки одинаковые
    def test_compare_without_sort_monogas(self):
        tz = load_fixture("monogas/default.json")
        tz_new = load_fixture("monogas/without_sort.json")
        self.assertEqual(Mark.GREEN, Sim.compare_monogas(tz, tz_new))

    # Сорты одинаковые
    def test_compare_without_marka_monogas(self):
        tz = load_fixture("monogas/default.json")
        tz_new = load_fixture("monogas/without_marka.json")
        self.assertEqual(Mark.GREEN, Sim.compare_monogas(tz, tz_new))

    # Разные марки
    def test_compare_with_other_marka_monogas(self):
        tz = load_fixture("monogas/default.json")
        tz_new = load_fixture("monogas/default_with_other_marka.json")
        self.assertEqual(Mark.ORANGE, Sim.compare_monogas(tz, tz_new))

    # Разные сорты
    def test_compare_with_other_sort_monogas(self):
        tz = load_fixture("monogas/default.json")
        tz_new = load_fixture("monogas/default_with_other_sort.json")
        self.assertEqual(Mark.ORANGE, Sim.compare_monogas(tz, tz_new))

    ###< Моногаз ###

    ###> Газовая смесь ###
    def test_compare_gas_mixture(self):
        pass
        # todo
    ###< Газовая смесь ###
