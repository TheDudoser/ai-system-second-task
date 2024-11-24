import json
import os


def load_fixture(filename):
    fixtures_dir = os.path.join(os.path.dirname(__file__),
                                "fixtures")  # путь к fixtures относительно текущего файла теста
    filepath = os.path.join(fixtures_dir, filename)

    with open(filepath, "r", encoding="utf-8") as f:
        return json.loads(f.read())
