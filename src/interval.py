class Interval:
    def __init__(self, left: float, right: float):
        if not isinstance(left, float) or not isinstance(right, float):
            raise TypeError("Левая и правая границы должны быть вещественными числами.")
        if left > right:
            raise ValueError("Левая граница должна быть меньше или равна правой границе.")
        self.left = float(left)
        self.right = float(right)

    # Проверка пересечения двух интервалов
    def intersects(self, other):
        return self.left <= other.right and other.left <= self.right

    # Проверка включения одного интервала в другой
    def contains_interval(self, other):
        return self.left <= other.left and self.right >= other.right

    # Проверка совпадения двух интервалов
    def __eq__(self, other):
        return self.left == other.left and self.right == other.right

    # Проверка принадлежности числа интервалу
    def contains_value(self, value):
        return self.left <= value <= self.right

    # Вычисление длины интервала
    def length(self):
        return self.right - self.left

    # Получение нижней границы интервала
    def get_left(self):
        return self.left

    # Получение верхней границы интервала
    def get_right(self):
        return self.right
