import unittest
from src.sim import Sim
from src.mark import Mark
from tests.utils import load_fixture


class TestSim(unittest.TestCase):
    # geometrical_characteristics
    def test_green_compare_geometrical_characteristics(self):
        tz = load_fixture("geometrical_characteristics/tz.json")
        tz_green = load_fixture("geometrical_characteristics/tz_green.json")
        self.assertEqual(Mark.GREEN, Sim.compare_geometrical_characteristics(tz, tz_green))

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

    # defects
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

    # materials
    def test_material_in_analogues(self):
        """У ДВО РАН нет примеров с аналогами на текущий момент..."""
        pass

    def test_materials_in_not_class(self):
        tz = load_fixture("materials/tz.json")
        tz_not_in_class = load_fixture("materials/tz_not_in_class.json")
        self.assertEqual(Mark.RED, Sim.compare_materials(tz, tz_not_in_class))

    def test_materials_in_class(self):
        # TODO: Ждём подобие эл. составов от Матвея
        pass

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
