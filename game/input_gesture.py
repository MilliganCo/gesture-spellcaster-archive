"""Обработка ввода жестов мышью."""

from typing import List, Optional, Tuple
import pygame

from game.config import WINDOW_WIDTH, WINDOW_HEIGHT

Point = Tuple[float, float]


class GestureInput:
    """Класс для обработки ввода жестов."""

    def __init__(self):
        """Инициализация."""
        self.is_drawing = False
        self.points: List[Point] = []
        self.last_point: Optional[Point] = None
        self.min_distance_squared = 5.0 * 5.0  # Минимальная дистанция между точками

    def start_gesture(self, pos: Tuple[int, int]) -> None:
        """Начать новый жест."""
        self.is_drawing = True
        self.points = [pos]
        self.last_point = pos

    def add_point(self, pos: Tuple[int, int]) -> None:
        """Добавить точку к текущему жесту (с throttling по дистанции)."""
        if not self.is_drawing:
            return

        # Throttling: добавлять только если точка достаточно далеко от предыдущей
        if self.last_point:
            dx = pos[0] - self.last_point[0]
            dy = pos[1] - self.last_point[1]
            dist_sq = dx * dx + dy * dy
            if dist_sq < self.min_distance_squared:
                return

        self.points.append(pos)
        self.last_point = pos

    def finish_gesture(self) -> List[Point]:
        """Завершить жест и вернуть список точек."""
        if not self.is_drawing:
            return []

        result = self.points.copy()
        self.reset()
        return result

    def cancel_gesture(self) -> None:
        """Отменить текущий жест."""
        self.reset()

    def reset(self) -> None:
        """Сбросить состояние."""
        self.is_drawing = False
        self.points = []
        self.last_point = None

    def get_points(self) -> List[Point]:
        """Получить текущие точки жеста."""
        return self.points.copy()

    def draw(self, surface: pygame.Surface, color: Tuple[int, int, int] = (255, 255, 255)) -> None:
        """Нарисовать текущий жест на поверхности."""
        if len(self.points) < 2:
            return

        # Рисовать линии между точками
        for i in range(len(self.points) - 1):
            pygame.draw.line(
                surface,
                color,
                self.points[i],
                self.points[i + 1],
                3,
            )

        # Рисовать точки
        for point in self.points:
            pygame.draw.circle(surface, color, (int(point[0]), int(point[1])), 3)
