"""Главный игровой цикл."""

import sys
import pygame
import time
from typing import List, Tuple

from game.config import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    FPS,
    COLOR_BLACK,
    COMBO_WINDOW_TIME,
    WAVE_BREAK_TIME,
    GESTURE_RECOGNITION_THRESHOLD,
    GESTURE_MIN_SCORE_DIFF,
)
from game.entities import Player, Enemy, Projectile, AoEEffect
from game.input_gesture import GestureInput
from game.recognizer_one_dollar import OneDollarRecognizer
from game.spells import cast_spell
from game.waves import WaveManager
from game.ui import UI


class GameState:
    """Состояние игры."""

    def __init__(self):
        """Инициализация состояния игры."""
        self.player = Player()
        self.enemies: List[Enemy] = []
        self.projectiles: List[Projectile] = []
        self.aoe_effects: List[AoEEffect] = []
        self.gesture_input = GestureInput()
        self.recognizer = OneDollarRecognizer()
        self.wave_manager = WaveManager()
        self.ui = UI()

        # Комбо-система
        self.combo_buffer: List[str] = []
        self.combo_timer: float = 0.0

        # Игровое время
        self.game_time: float = 0.0
        self.is_game_over: bool = False

        # Последние результаты распознавания для debug
        self.last_recognition_results: List[Tuple[str, float]] = []

    def reset(self) -> None:
        """Сбросить игру."""
        self.__init__()


def handle_events(game_state: GameState) -> bool:
    """Обработать события. Возвращает False если нужно выйти."""
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and game_state.is_game_over:
                game_state.reset()
            elif event.key == pygame.K_SPACE:
                # Принудительно завершить комбо
                game_state.combo_buffer.clear()
                game_state.combo_timer = 0.0

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # ЛКМ
                game_state.gesture_input.start_gesture(event.pos)
            elif event.button == 3:  # ПКМ
                game_state.gesture_input.cancel_gesture()

        elif event.type == pygame.MOUSEMOTION:
            if game_state.gesture_input.is_drawing:
                game_state.gesture_input.add_point(event.pos)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # ЛКМ
                points = game_state.gesture_input.finish_gesture()
                if len(points) >= 2:
                    # Распознать жест
                    results = game_state.recognizer.recognize(points)
                    game_state.last_recognition_results = results

                    if results:
                        best_rune, best_score = results[0]
                        # Проверка порога и минимальной разницы с вторым результатом
                        if best_score >= GESTURE_RECOGNITION_THRESHOLD:
                            # Если есть второй результат, проверяем разницу
                            should_cast = True
                            if len(results) > 1:
                                second_score = results[1][1]
                                # Если разница слишком мала, возможно ложное срабатывание
                                if best_score - second_score < GESTURE_MIN_SCORE_DIFF:
                                    should_cast = False
                            
                            if should_cast:
                                # Применить заклинание
                                cast_spell(
                                    best_rune,
                                    game_state.player,
                                    game_state.enemies,
                                    game_state.projectiles,
                                    game_state.aoe_effects,
                                    points,
                                )

                                # Обновить комбо
                                game_state.combo_buffer.append(best_rune)
                                game_state.combo_timer = COMBO_WINDOW_TIME

                                # Обновить UI
                                game_state.ui.update_last_rune(best_rune, game_state.game_time)

    return True


def update(game_state: GameState, dt: float) -> None:
    """Обновить игровое состояние."""
    if game_state.is_game_over:
        return

    game_state.game_time += dt

    # Обновить комбо-таймер
    if game_state.combo_timer > 0:
        game_state.combo_timer -= dt
        if game_state.combo_timer <= 0:
            game_state.combo_buffer.clear()

    # Обновить волны
    new_enemies = game_state.wave_manager.update(game_state.game_time, game_state.enemies)
    game_state.enemies.extend(new_enemies)

    # Обновить врагов
    for enemy in game_state.enemies[:]:
        if not enemy.is_alive():
            game_state.enemies.remove(enemy)
            continue

        enemy.update(dt, game_state.player.x, game_state.player.y)

        # Проверка атаки врага
        dist = enemy.distance_to(game_state.player.x, game_state.player.y)
        if dist <= enemy.radius + game_state.player.radius:
            if enemy.can_attack():
                damage = enemy.attack()
                game_state.player.take_damage(damage)

    # Обновить снаряды
    for projectile in game_state.projectiles[:]:
        if projectile.is_expired():
            game_state.projectiles.remove(projectile)
            continue

        projectile.update(dt)

        # Проверка коллизий снарядов с врагами
        for enemy in game_state.enemies:
            if not enemy.is_alive():
                continue
            dist = projectile.distance_to(enemy.x, enemy.y)
            if dist <= projectile.radius + enemy.radius:
                enemy.take_damage(projectile.damage)
                game_state.projectiles.remove(projectile)
                break

    # Обновить AoE эффекты
    for aoe in game_state.aoe_effects[:]:
        if aoe.is_expired():
            game_state.aoe_effects.remove(aoe)
            continue
        aoe.update(dt)

    # Проверка Game Over
    if not game_state.player.is_alive():
        game_state.is_game_over = True


def render(screen: pygame.Surface, game_state: GameState) -> None:
    """Отрисовать игровое состояние."""
    screen.fill(COLOR_BLACK)

    if game_state.is_game_over:
        game_state.ui.draw_game_over(screen, game_state.wave_manager.get_current_wave_number())
        pygame.display.flip()
        return

    # Отрисовка перерыва между волнами
    if game_state.wave_manager.is_in_break() and game_state.wave_manager.get_current_wave_number() > 0:
        time_left = WAVE_BREAK_TIME - (game_state.game_time - game_state.wave_manager.break_start_time)
        if time_left > 0:
            game_state.ui.draw_wave_break(
                screen,
                game_state.wave_manager.get_current_wave_number(),
                time_left,
            )

    # Отрисовать игрока
    game_state.player.draw(screen)

    # Отрисовать врагов
    for enemy in game_state.enemies:
        enemy.draw(screen)

    # Отрисовать снаряды
    for projectile in game_state.projectiles:
        projectile.draw(screen)

    # Отрисовать AoE эффекты
    for aoe in game_state.aoe_effects:
        aoe.draw(screen)

    # Отрисовать жест
    if game_state.gesture_input.is_drawing:
        game_state.gesture_input.draw(screen)

    # Отрисовать HUD
    game_state.ui.draw_hud(
        screen,
        game_state.player.hp,
        game_state.player.max_hp,
        game_state.wave_manager.get_current_wave_number(),
        len(game_state.enemies),
        game_state.combo_buffer,
        game_state.combo_timer,
        game_state.game_time,
    )

    # Отрисовать debug панель
    gesture_points = game_state.gesture_input.get_points()
    game_state.ui.draw_debug(
        screen,
        game_state.last_recognition_results,
        len(gesture_points),
    )

    pygame.display.flip()


def main() -> None:
    """Главная функция."""
    pygame.init()

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Gesture Spellcaster")
    clock = pygame.time.Clock()

    game_state = GameState()

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0  # Конвертировать в секунды

        running = handle_events(game_state)
        update(game_state, dt)
        render(screen, game_state)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
