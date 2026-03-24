"""Система заклинаний: связь рун с эффектами."""

import math
from typing import List, Optional, Tuple

from game.entities import Player, Enemy, Projectile, AoEEffect, StatusEffect
from game.config import (
    SPELL_BOLT_DAMAGE,
    SPELL_NOVA_DAMAGE,
    SPELL_NOVA_RADIUS,
    SPELL_CONE_DAMAGE,
    SPELL_CONE_ANGLE,
    SPELL_CONE_RANGE,
    SPELL_CHAIN_DAMAGE,
    SPELL_CHAIN_JUMPS,
    SPELL_CHAIN_RANGE,
    SPELL_SLOW_RADIUS,
    SPELL_SLOW_DURATION,
    SPELL_SLOW_FACTOR,
    SPELL_DRAIN_DAMAGE,
    SPELL_DRAIN_RADIUS,
    SPELL_DRAIN_HEAL,
    PLAYER_POS_X,
    PLAYER_POS_Y,
)


def find_nearest_enemy(
    enemies: List[Enemy], x: float, y: float, exclude: Optional[Enemy] = None
) -> Optional[Enemy]:
    """Найти ближайшего врага к точке."""
    nearest = None
    min_dist = float("inf")

    for enemy in enemies:
        if not enemy.is_alive() or enemy == exclude:
            continue
        dist = enemy.distance_to(x, y)
        if dist < min_dist:
            min_dist = dist
            nearest = enemy

    return nearest


def get_gesture_direction(points: List[Tuple[float, float]]) -> float:
    """Вычислить направление жеста (угол в радианах)."""
    if len(points) < 2:
        return 0.0

    # Взять направление от первой к последней точке
    dx = points[-1][0] - points[0][0]
    dy = points[-1][1] - points[0][1]

    if dx == 0 and dy == 0:
        return 0.0

    return math.atan2(dy, dx)


def cast_cross(
    player: Player,
    enemies: List[Enemy],
    projectiles: List[Projectile],
) -> None:
    """Применить заклинание Cross (CROSS) - стреляет снарядами в 4 направления."""
    # Стреляем в 4 стороны: вверх, вправо, вниз, влево
    directions = [
        (0.0, -1.0),   # Вверх
        (1.0, 0.0),    # Вправо
        (0.0, 1.0),    # Вниз
        (-1.0, 0.0),   # Влево
    ]
    
    for vx, vy in directions:
        projectile = Projectile(
            x=player.x,
            y=player.y,
            vx=vx,
            vy=vy,
            damage=SPELL_BOLT_DAMAGE,
        )
        projectiles.append(projectile)


def cast_nova(
    player: Player,
    enemies: List[Enemy],
    aoe_effects: List[AoEEffect],
) -> None:
    """Применить заклинание Nova (CIRCLE)."""
    # Создать AoE эффект
    aoe = AoEEffect(
        x=player.x,
        y=player.y,
        radius=SPELL_NOVA_RADIUS,
        damage=SPELL_NOVA_DAMAGE,
    )
    aoe_effects.append(aoe)

    # Нанести урон всем врагам в радиусе
    for enemy in enemies:
        if not enemy.is_alive():
            continue
        dist = enemy.distance_to(player.x, player.y)
        if dist <= SPELL_NOVA_RADIUS:
            enemy.take_damage(SPELL_NOVA_DAMAGE)


def cast_cone(
    player: Player,
    enemies: List[Enemy],
    points: List[Tuple[float, float]],
) -> None:
    """Применить заклинание Cone (V)."""
    # Определить направление по жесту
    angle = get_gesture_direction(points)
    if len(points) < 2:
        angle = 0.0  # По умолчанию вправо

    half_angle = math.radians(SPELL_CONE_ANGLE / 2)

    # Найти врагов в конусе
    for enemy in enemies:
        if not enemy.is_alive():
            continue

        dx = enemy.x - player.x
        dy = enemy.y - player.y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist > SPELL_CONE_RANGE:
            continue

        # Вычислить угол к врагу
        enemy_angle = math.atan2(dy, dx)

        # Проверить, находится ли враг в конусе
        angle_diff = abs(enemy_angle - angle)
        if angle_diff > math.pi:
            angle_diff = 2 * math.pi - angle_diff

        if angle_diff <= half_angle:
            enemy.take_damage(SPELL_CONE_DAMAGE)


def cast_chain(
    player: Player,
    enemies: List[Enemy],
) -> None:
    """Применить заклинание Chain (Z)."""
    current_target = find_nearest_enemy(enemies, player.x, player.y)
    if not current_target:
        return

    hit_enemies = []
    remaining_jumps = SPELL_CHAIN_JUMPS

    while current_target and remaining_jumps > 0:
        current_target.take_damage(SPELL_CHAIN_DAMAGE)
        hit_enemies.append(current_target)
        remaining_jumps -= 1

        # Найти следующую цель
        next_target = None
        min_dist = float("inf")

        for enemy in enemies:
            if not enemy.is_alive() or enemy in hit_enemies:
                continue
            dist = current_target.distance_to(enemy.x, enemy.y)
            if dist <= SPELL_CHAIN_RANGE and dist < min_dist:
                min_dist = dist
                next_target = enemy

        current_target = next_target


def cast_slow(
    player: Player,
    enemies: List[Enemy],
) -> None:
    """Применить заклинание Slow (S)."""
    for enemy in enemies:
        if not enemy.is_alive():
            continue
        dist = enemy.distance_to(player.x, player.y)
        if dist <= SPELL_SLOW_RADIUS:
            enemy.status.slow_factor = SPELL_SLOW_FACTOR
            enemy.status.slow_duration = SPELL_SLOW_DURATION


def cast_drain(
    player: Player,
    enemies: List[Enemy],
) -> None:
    """Применить заклинание Drain (SPIRAL)."""
    hit_count = 0

    for enemy in enemies:
        if not enemy.is_alive():
            continue
        dist = enemy.distance_to(player.x, player.y)
        if dist <= SPELL_DRAIN_RADIUS:
            enemy.take_damage(SPELL_DRAIN_DAMAGE)
            hit_count += 1

    # Лечение пропорционально количеству поражённых врагов
    if hit_count > 0:
        player.heal(SPELL_DRAIN_HEAL * hit_count)


def cast_spell(
    rune: str,
    player: Player,
    enemies: List[Enemy],
    projectiles: List[Projectile],
    aoe_effects: List[AoEEffect],
    gesture_points: List[Tuple[float, float]],
) -> None:
    """Применить заклинание по имени руны."""
    if rune == "CROSS":
        cast_cross(player, enemies, projectiles)
    elif rune == "CIRCLE":
        cast_nova(player, enemies, aoe_effects)
    elif rune == "V":
        cast_cone(player, enemies, gesture_points)
    elif rune == "Z":
        cast_chain(player, enemies)
    elif rune == "S":
        cast_slow(player, enemies)
    elif rune == "SPIRAL":
        cast_drain(player, enemies)
    # Если руна не распознана или неизвестна - ничего не делать (fizzle)
