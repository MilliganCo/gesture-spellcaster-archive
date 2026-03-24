"""Система волн врагов."""

from dataclasses import dataclass
from typing import List, Tuple, Optional
import random
import math

from game.entities import Enemy
from game.config import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    WAVE_START_ENEMIES,
    WAVE_ENEMY_INCREMENT,
    WAVE_SPAWN_INTERVAL,
    WAVE_BREAK_TIME,
    PLAYER_POS_X,
    PLAYER_POS_Y,
)


@dataclass
class WaveSpawn:
    """Один спавн врага в волне."""

    enemy_type: str
    spawn_time: float  # Время относительно начала волны


@dataclass
class Wave:
    """Волна врагов."""

    wave_number: int
    spawns: List[WaveSpawn]
    start_time: float = 0.0
    is_active: bool = False


class WaveManager:
    """Менеджер волн."""

    def __init__(self):
        """Инициализация."""
        self.current_wave_number = 0
        self.current_wave: Optional[Wave] = None
        self.wave_start_time = 0.0
        self.last_spawn_time = 0.0
        self.spawn_index = 0
        self.is_break = True  # Начинаем с перерыва, чтобы первая волна запустилась через should_start_wave
        self.break_start_time = -WAVE_BREAK_TIME  # Чтобы первая волна началась сразу

    def start_next_wave(self, current_time: float) -> None:
        """Начать следующую волну."""
        self.current_wave_number += 1
        self.is_break = False

        # Вычислить количество врагов
        enemy_count = WAVE_START_ENEMIES + (self.current_wave_number - 1) * WAVE_ENEMY_INCREMENT

        # Создать спавны
        spawns: List[WaveSpawn] = []
        for i in range(enemy_count):
            # Чередовать типы врагов
            enemy_type = "runner" if i % 3 == 0 else "grunt"
            spawn_time = i * WAVE_SPAWN_INTERVAL
            spawns.append(WaveSpawn(enemy_type=enemy_type, spawn_time=spawn_time))

        self.current_wave = Wave(
            wave_number=self.current_wave_number,
            spawns=spawns,
            start_time=current_time,
            is_active=True,
        )
        self.wave_start_time = current_time
        self.last_spawn_time = current_time
        self.spawn_index = 0

    def start_break(self, current_time: float) -> None:
        """Начать перерыв между волнами."""
        self.is_break = True
        self.break_start_time = current_time
        if self.current_wave:
            self.current_wave.is_active = False

    def should_start_wave(self, current_time: float) -> bool:
        """Проверить, нужно ли начать новую волну."""
        if not self.is_break:
            return False

        # Для первой волны (wave_number == 0) начинаем сразу
        if self.current_wave_number == 0:
            return True

        elapsed = current_time - self.break_start_time
        return elapsed >= WAVE_BREAK_TIME

    def update(
        self, current_time: float, enemies: List[Enemy]
    ) -> List[Enemy]:
        """Обновить менеджер волн и вернуть список новых врагов для спавна."""
        new_enemies: List[Enemy] = []

        # Проверить, нужно ли начать новую волну
        if self.should_start_wave(current_time):
            self.start_next_wave(current_time)

        # Если перерыв - не спавнить
        if self.is_break or not self.current_wave:
            return new_enemies

        # Проверить, закончилась ли волна
        if self.spawn_index >= len(self.current_wave.spawns):
            # Проверить, все ли враги убиты
            if len(enemies) == 0:
                self.start_break(current_time)
            return new_enemies

        # Спавнить врагов по расписанию
        elapsed = current_time - self.wave_start_time
        next_spawn = self.current_wave.spawns[self.spawn_index]

        if elapsed >= next_spawn.spawn_time:
            # Спавнить врага
            enemy = self.spawn_enemy(next_spawn.enemy_type)
            new_enemies.append(enemy)
            self.spawn_index += 1

        return new_enemies

    def spawn_enemy(self, enemy_type: str) -> Enemy:
        """Создать врага на краю экрана."""
        # Случайная позиция на краю экрана
        side = random.randint(0, 3)  # 0=верх, 1=право, 2=низ, 3=лево

        if side == 0:  # Верх
            x = random.uniform(0, WINDOW_WIDTH)
            y = -50
        elif side == 1:  # Право
            x = WINDOW_WIDTH + 50
            y = random.uniform(0, WINDOW_HEIGHT)
        elif side == 2:  # Низ
            x = random.uniform(0, WINDOW_WIDTH)
            y = WINDOW_HEIGHT + 50
        else:  # Лево
            x = -50
            y = random.uniform(0, WINDOW_HEIGHT)

        return Enemy(x=x, y=y, enemy_type=enemy_type)

    def get_current_wave_number(self) -> int:
        """Получить номер текущей волны."""
        return self.current_wave_number

    def is_in_break(self) -> bool:
        """Проверить, идёт ли перерыв."""
        return self.is_break
