"""Реализация $1 Recognizer для распознавания жестов."""

import math
import json
from typing import List, Tuple, Optional
from pathlib import Path

from game.config import (
    GESTURE_RESAMPLE_POINTS,
    GESTURE_ROTATION_RANGE,
    GESTURE_BOUNDING_BOX_SIZE,
    GESTURE_RECOGNITION_THRESHOLD,
)


Point = Tuple[float, float]
Template = List[Point]


class OneDollarRecognizer:
    """$1 Recognizer для распознавания однострочных жестов."""

    def __init__(self, templates_path: str = "assets/runes.json"):
        """Инициализация распознавателя с загрузкой шаблонов."""
        self.templates: dict[str, List[Template]] = {}
        self.load_templates(templates_path)

    def load_templates(self, path: str) -> None:
        """Загрузить шаблоны рун из JSON файла."""
        templates_file = Path(path)
        if not templates_file.exists():
            raise FileNotFoundError(f"Шаблоны не найдены: {path}")

        with open(templates_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        for rune_name, examples in data.items():
            self.templates[rune_name] = [
                [(float(x), float(y)) for x, y in example] for example in examples
            ]

    def resample(self, points: List[Point], n: int) -> List[Point]:
        """Пересэмплировать точки до n точек с равными интервалами."""
        if len(points) <= 1:
            return points

        # Вычислить общую длину пути
        path_length = 0.0
        for i in range(len(points) - 1):
            dx = points[i + 1][0] - points[i][0]
            dy = points[i + 1][1] - points[i][1]
            path_length += math.sqrt(dx * dx + dy * dy)

        if path_length == 0:
            return points

        # Равномерно распределить n точек
        interval = path_length / (n - 1)
        new_points: List[Point] = [points[0]]
        current_distance = 0.0
        i = 0

        while i < len(points) - 1 and len(new_points) < n:
            dx = points[i + 1][0] - points[i][0]
            dy = points[i + 1][1] - points[i][1]
            segment_length = math.sqrt(dx * dx + dy * dy)

            if current_distance + segment_length >= interval:
                # Интерполировать точку на этом сегменте
                t = (interval - current_distance) / segment_length if segment_length > 0 else 0
                x = points[i][0] + t * dx
                y = points[i][1] + t * dy
                new_points.append((x, y))
                current_distance = 0.0
                # Остаться на этом сегменте для следующей точки
            else:
                current_distance += segment_length
                i += 1

        # Убедиться, что последняя точка добавлена
        if len(new_points) < n:
            new_points.append(points[-1])

        return new_points

    def centroid(self, points: List[Point]) -> Point:
        """Вычислить центроид точек."""
        if not points:
            return (0.0, 0.0)
        sum_x = sum(p[0] for p in points)
        sum_y = sum(p[1] for p in points)
        n = len(points)
        return (sum_x / n, sum_y / n)

    def indicative_angle(self, points: List[Point]) -> float:
        """Вычислить индикативный угол (от центроида к первой точке)."""
        c = self.centroid(points)
        dx = points[0][0] - c[0]
        dy = points[0][1] - c[1]
        return math.atan2(dy, dx)

    def rotate(self, points: List[Point], angle: float) -> List[Point]:
        """Повернуть точки на угол вокруг центроида."""
        c = self.centroid(points)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        rotated = []
        for p in points:
            dx = p[0] - c[0]
            dy = p[1] - c[1]
            x = dx * cos_a - dy * sin_a + c[0]
            y = dx * sin_a + dy * cos_a + c[1]
            rotated.append((x, y))
        return rotated

    def scale(self, points: List[Point], size: float) -> List[Point]:
        """Масштабировать точки к квадрату размера size."""
        # Найти bounding box
        min_x = min(p[0] for p in points)
        max_x = max(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)

        width = max_x - min_x
        height = max_y - min_y

        if width == 0 and height == 0:
            return points

        # Масштабировать, сохраняя пропорции
        scale_factor = size / max(width, height)
        scaled = []
        for p in points:
            x = (p[0] - min_x) * scale_factor
            y = (p[1] - min_y) * scale_factor
            scaled.append((x, y))
        return scaled

    def translate_to_origin(self, points: List[Point]) -> List[Point]:
        """Переместить точки так, чтобы центроид был в начале координат."""
        c = self.centroid(points)
        translated = [(p[0] - c[0], p[1] - c[1]) for p in points]
        return translated

    def path_distance(self, points1: List[Point], points2: List[Point]) -> float:
        """Вычислить расстояние между двумя путями (среднее расстояние по соответствующим точкам)."""
        if len(points1) != len(points2):
            return float("inf")

        total_distance = 0.0
        for i in range(len(points1)):
            dx = points1[i][0] - points2[i][0]
            dy = points1[i][1] - points2[i][1]
            total_distance += math.sqrt(dx * dx + dy * dy)

        # Также учитываем направление движения для более точного распознавания
        direction_penalty = 0.0
        if len(points1) > 1:
            for i in range(len(points1) - 1):
                # Вычислить направление движения в первом пути
                dx1 = points1[i + 1][0] - points1[i][0]
                dy1 = points1[i + 1][1] - points1[i][1]
                # Вычислить направление движения во втором пути
                dx2 = points2[i + 1][0] - points2[i][0]
                dy2 = points2[i + 1][1] - points2[i][1]
                
                # Вычислить угол между направлениями
                if (dx1 != 0 or dy1 != 0) and (dx2 != 0 or dy2 != 0):
                    angle1 = math.atan2(dy1, dx1)
                    angle2 = math.atan2(dy2, dx2)
                    angle_diff = abs(angle1 - angle2)
                    if angle_diff > math.pi:
                        angle_diff = 2 * math.pi - angle_diff
                    # Штраф за разницу в направлении (нормализованный)
                    direction_penalty += angle_diff / math.pi

        # Комбинируем расстояние и штраф за направление
        avg_distance = total_distance / len(points1)
        if len(points1) > 1:
            avg_direction_penalty = direction_penalty / (len(points1) - 1)
            # Взвешенная комбинация (направление менее важно, чем позиция)
            return avg_distance + avg_direction_penalty * 10.0
        return avg_distance

    def distance_at_angle(
        self, points: List[Point], template: List[Point], angle: float
    ) -> float:
        """Вычислить расстояние между точками и шаблоном при повороте на угол."""
        rotated = self.rotate(points, angle)
        return self.path_distance(rotated, template)

    def golden_section_search(
        self, points: List[Point], template: List[Point], a: float, b: float, threshold: float
    ) -> Tuple[float, float]:
        """Golden Section Search для поиска оптимального угла поворота."""
        phi = (1 + math.sqrt(5)) / 2  # Золотое сечение
        resphi = 2 - phi

        x1 = resphi * a + (1 - resphi) * b
        f1 = self.distance_at_angle(points, template, x1)
        x2 = (1 - resphi) * a + resphi * b
        f2 = self.distance_at_angle(points, template, x2)

        while abs(b - a) > threshold:
            if f1 < f2:
                b = x2
                x2 = x1
                f2 = f1
                x1 = resphi * a + (1 - resphi) * b
                f1 = self.distance_at_angle(points, template, x1)
            else:
                a = x1
                x1 = x2
                f1 = f2
                x2 = (1 - resphi) * a + resphi * b
                f2 = self.distance_at_angle(points, template, x2)

        return (min(f1, f2), (a + b) / 2)

    def normalize(self, points: List[Point]) -> List[Point]:
        """Нормализовать точки: resample, rotate-to-zero, scale, translate."""
        if len(points) < 2:
            return points

        # Resample
        resampled = self.resample(points, GESTURE_RESAMPLE_POINTS)

        # Rotate to zero
        angle = -self.indicative_angle(resampled)
        rotated = self.rotate(resampled, angle)

        # Scale
        scaled = self.scale(rotated, GESTURE_BOUNDING_BOX_SIZE)

        # Translate to origin
        normalized = self.translate_to_origin(scaled)

        return normalized

    def recognize(
        self, points: List[Point]
    ) -> List[Tuple[str, float]]:
        """Распознать жест и вернуть топ-3 результата с score."""
        if len(points) < 2:
            return []

        # Нормализовать входные точки
        normalized = self.normalize(points)

        results: List[Tuple[str, float]] = []
        half_diagonal = math.sqrt(
            GESTURE_BOUNDING_BOX_SIZE * GESTURE_BOUNDING_BOX_SIZE * 2
        ) / 2

        # Проверить каждый шаблон
        for rune_name, templates in self.templates.items():
            best_score = 0.0

            for template_points in templates:
                # Нормализовать шаблон
                normalized_template = self.normalize(template_points)

                # Rotation-invariant поиск лучшего угла
                angle_min = math.radians(GESTURE_ROTATION_RANGE[0])
                angle_max = math.radians(GESTURE_ROTATION_RANGE[1])
                best_distance, best_angle = self.golden_section_search(
                    normalized, normalized_template, angle_min, angle_max, 0.01
                )

                # Вычислить score
                score = 1.0 - (best_distance / half_diagonal)
                if score > best_score:
                    best_score = score

            results.append((rune_name, best_score))

        # Сортировать по score (убывание)
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:3]  # Вернуть топ-3

    def recognize_best(self, points: List[Point]) -> Optional[Tuple[str, float]]:
        """Распознать жест и вернуть лучший результат, если он выше порога."""
        results = self.recognize(points)
        if results and results[0][1] >= GESTURE_RECOGNITION_THRESHOLD:
            return results[0]
        return None
