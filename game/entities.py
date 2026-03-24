"""Игровые сущности: Player, Enemy, Projectile, эффекты."""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import math
import pygame

from game.config import (
    PLAYER_POS_X,
    PLAYER_POS_Y,
    PLAYER_MAX_HP,
    PLAYER_RADIUS,
    ENEMY_GRUNT_HP,
    ENEMY_GRUNT_SPEED,
    ENEMY_GRUNT_RADIUS,
    ENEMY_GRUNT_DAMAGE,
    ENEMY_GRUNT_ATTACK_COOLDOWN,
    ENEMY_RUNNER_HP,
    ENEMY_RUNNER_SPEED,
    ENEMY_RUNNER_RADIUS,
    ENEMY_RUNNER_DAMAGE,
    ENEMY_RUNNER_ATTACK_COOLDOWN,
    SPELL_BOLT_SPEED,
    SPELL_BOLT_RADIUS,
    SPELL_SLOW_FACTOR,
    SPELL_SLOW_DURATION,
    COLOR_RED,
    COLOR_GREEN,
    COLOR_BLUE,
    COLOR_YELLOW,
    COLOR_CYAN,
    COLOR_WHITE,
)


@dataclass
class StatusEffect:
    """Статусный эффект на враге."""
    slow_factor: float = 1.0
    slow_duration: float = 0.0


@dataclass
class Player:
    """Игрок."""

    x: float = PLAYER_POS_X
    y: float = PLAYER_POS_Y
    hp: float = PLAYER_MAX_HP
    max_hp: float = PLAYER_MAX_HP
    radius: float = PLAYER_RADIUS

    def take_damage(self, damage: float) -> None:
        """Получить урон."""
        self.hp = max(0, self.hp - damage)

    def heal(self, amount: float) -> None:
        """Восстановить HP."""
        self.hp = min(self.max_hp, self.hp + amount)

    def is_alive(self) -> bool:
        """Проверить, жив ли игрок."""
        return self.hp > 0

    def draw(self, surface: pygame.Surface) -> None:
        """Нарисовать игрока."""
        pygame.draw.circle(surface, COLOR_CYAN, (int(self.x), int(self.y)), int(self.radius))
        pygame.draw.circle(surface, COLOR_WHITE, (int(self.x), int(self.y)), int(self.radius), 2)

        # HP bar
        bar_width = self.radius * 2
        bar_height = 5
        bar_x = self.x - bar_width / 2
        bar_y = self.y - self.radius - 10

        # Фон
        pygame.draw.rect(
            surface,
            COLOR_RED,
            (int(bar_x), int(bar_y), int(bar_width), int(bar_height)),
        )
        # HP
        hp_width = bar_width * (self.hp / self.max_hp)
        pygame.draw.rect(
            surface,
            COLOR_GREEN,
            (int(bar_x), int(bar_y), int(hp_width), int(bar_height)),
        )


@dataclass
class Enemy:
    """Враг."""

    x: float
    y: float
    enemy_type: str = "grunt"  # "grunt" или "runner"
    hp: float = field(init=False)
    max_hp: float = field(init=False)
    speed: float = field(init=False)
    radius: float = field(init=False)
    damage: float = field(init=False)
    attack_cooldown: float = field(init=False)
    attack_timer: float = 0.0
    status: StatusEffect = field(default_factory=StatusEffect)

    def __post_init__(self):
        """Инициализировать параметры в зависимости от типа."""
        if self.enemy_type == "runner":
            self.hp = ENEMY_RUNNER_HP
            self.max_hp = ENEMY_RUNNER_HP
            self.speed = ENEMY_RUNNER_SPEED
            self.radius = ENEMY_RUNNER_RADIUS
            self.damage = ENEMY_RUNNER_DAMAGE
            self.attack_cooldown = ENEMY_RUNNER_ATTACK_COOLDOWN
        else:  # grunt
            self.hp = ENEMY_GRUNT_HP
            self.max_hp = ENEMY_GRUNT_HP
            self.speed = ENEMY_GRUNT_SPEED
            self.radius = ENEMY_GRUNT_RADIUS
            self.damage = ENEMY_GRUNT_DAMAGE
            self.attack_cooldown = ENEMY_GRUNT_ATTACK_COOLDOWN

    def update(self, dt: float, target_x: float, target_y: float) -> None:
        """Обновить позицию врага."""
        # Обновить статус
        if self.status.slow_duration > 0:
            self.status.slow_duration -= dt
            if self.status.slow_duration <= 0:
                self.status.slow_factor = 1.0

        # Обновить таймер атаки
        self.attack_timer -= dt

        # Движение к цели
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist > 0:
            speed = self.speed * self.status.slow_factor
            move_dist = min(dist, speed * dt)
            self.x += (dx / dist) * move_dist
            self.y += (dy / dist) * move_dist

    def take_damage(self, damage: float) -> None:
        """Получить урон."""
        self.hp = max(0, self.hp - damage)

    def can_attack(self) -> bool:
        """Проверить, может ли враг атаковать."""
        return self.attack_timer <= 0

    def attack(self) -> float:
        """Выполнить атаку и вернуть урон."""
        self.attack_timer = self.attack_cooldown
        return self.damage

    def is_alive(self) -> bool:
        """Проверить, жив ли враг."""
        return self.hp > 0

    def distance_to(self, x: float, y: float) -> float:
        """Вычислить расстояние до точки."""
        dx = self.x - x
        dy = self.y - y
        return math.sqrt(dx * dx + dy * dy)

    def draw(self, surface: pygame.Surface) -> None:
        """Нарисовать врага."""
        color = COLOR_YELLOW if self.enemy_type == "runner" else COLOR_RED
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(self.radius))

        # Статус замедления
        if self.status.slow_duration > 0:
            pygame.draw.circle(
                surface,
                COLOR_BLUE,
                (int(self.x), int(self.y)),
                int(self.radius + 3),
                2,
            )

        # HP bar
        bar_width = self.radius * 2
        bar_height = 3
        bar_x = self.x - bar_width / 2
        bar_y = self.y - self.radius - 8

        # Фон
        pygame.draw.rect(
            surface,
            COLOR_RED,
            (int(bar_x), int(bar_y), int(bar_width), int(bar_height)),
        )
        # HP
        hp_width = bar_width * (self.hp / self.max_hp)
        pygame.draw.rect(
            surface,
            COLOR_GREEN,
            (int(bar_x), int(bar_y), int(hp_width), int(bar_height)),
        )


@dataclass
class Projectile:
    """Снаряд."""

    x: float
    y: float
    vx: float
    vy: float
    speed: float = SPELL_BOLT_SPEED
    radius: float = SPELL_BOLT_RADIUS
    damage: float = 0.0
    lifetime: float = 2.0  # секунды
    age: float = 0.0

    def update(self, dt: float) -> None:
        """Обновить позицию снаряда."""
        self.age += dt
        dist = self.speed * dt
        self.x += self.vx * dist
        self.y += self.vy * dist

    def is_expired(self) -> bool:
        """Проверить, истёк ли срок жизни."""
        return self.age >= self.lifetime

    def distance_to(self, x: float, y: float) -> float:
        """Вычислить расстояние до точки."""
        dx = self.x - x
        dy = self.y - y
        return math.sqrt(dx * dx + dy * dy)

    def draw(self, surface: pygame.Surface) -> None:
        """Нарисовать снаряд."""
        pygame.draw.circle(surface, COLOR_YELLOW, (int(self.x), int(self.y)), int(self.radius))


@dataclass
class AoEEffect:
    """AoE эффект (Nova и подобные)."""

    x: float
    y: float
    radius: float
    damage: float
    duration: float = 0.1  # секунды
    age: float = 0.0

    def update(self, dt: float) -> None:
        """Обновить эффект."""
        self.age += dt

    def is_expired(self) -> bool:
        """Проверить, истёк ли эффект."""
        return self.age >= self.duration

    def draw(self, surface: pygame.Surface) -> None:
        """Нарисовать AoE эффект."""
        alpha = int(255 * (1.0 - self.age / self.duration))
        color = (255, 255, 0, alpha)
        # Простое отображение без альфа-канала
        pygame.draw.circle(
            surface,
            COLOR_YELLOW,
            (int(self.x), int(self.y)),
            int(self.radius),
            2,
        )
