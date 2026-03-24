"""UI и HUD."""

from typing import List, Optional, Tuple
import pygame

from game.config import (
    UI_FONT_SIZE,
    UI_DEBUG_FONT_SIZE,
    UI_MARGIN,
    COLOR_WHITE,
    COLOR_YELLOW,
    COLOR_GREEN,
    COLOR_RED,
    COLOR_GRAY,
    COLOR_CYAN,
    COLOR_BLUE,
    COLOR_MAGENTA,
    COLOR_DARK_GRAY,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    COMBO_WINDOW_TIME,
)


class UI:
    """Класс для отображения UI."""

    def __init__(self):
        """Инициализация."""
        pygame.font.init()
        self.font = pygame.font.Font(None, UI_FONT_SIZE)
        self.debug_font = pygame.font.Font(None, UI_DEBUG_FONT_SIZE)
        self.large_font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 18)

        # Для отображения последней распознанной руны
        self.last_rune: Optional[str] = None
        self.last_rune_time: float = 0.0
        self.last_rune_duration: float = 0.5  # секунды

        # Информация о рунах для подсказок
        self.runes_info = {
            "CROSS": {"name": "CROSS", "effect": "4 снаряда", "color": COLOR_YELLOW},
            "CIRCLE": {"name": "CIRCLE", "effect": "AoE урон", "color": COLOR_RED},
            "V": {"name": "V", "effect": "Конус", "color": COLOR_GREEN},
            "Z": {"name": "Z", "effect": "Цепь", "color": COLOR_CYAN},
            "S": {"name": "S", "effect": "Замедление", "color": COLOR_BLUE},
            "SPIRAL": {"name": "SPIRAL", "effect": "Дренаж", "color": COLOR_MAGENTA},
        }
    
    def draw_rune_hint(self, surface: pygame.Surface, rune_name: str, x: int, y: int, size: int = 40) -> None:
        """Нарисовать подсказку для одной руны."""
        if rune_name not in self.runes_info:
            return
        
        info = self.runes_info[rune_name]
        color = info["color"]
        
        # Фон для подсказки
        padding = 5
        box_width = size + padding * 2
        box_height = size + padding * 2 + 40  # Место для текста
        
        # Полупрозрачный фон
        hint_surface = pygame.Surface((box_width, box_height))
        hint_surface.set_alpha(200)
        hint_surface.fill(COLOR_DARK_GRAY)
        surface.blit(hint_surface, (x - padding, y - padding))
        
        # Рисуем миниатюру руны
        center_x = x + size // 2
        center_y = y + size // 2
        
        if rune_name == "CROSS":
            # Крест
            pygame.draw.line(surface, color, (center_x - size//3, center_y), (center_x + size//3, center_y), 3)
            pygame.draw.line(surface, color, (center_x, center_y - size//3), (center_x, center_y + size//3), 3)
        elif rune_name == "CIRCLE":
            # Круг
            pygame.draw.circle(surface, color, (center_x, center_y), size//3, 2)
        elif rune_name == "V":
            # V
            pygame.draw.line(surface, color, (center_x - size//3, center_y - size//3), (center_x, center_y + size//3), 3)
            pygame.draw.line(surface, color, (center_x, center_y + size//3), (center_x + size//3, center_y - size//3), 3)
        elif rune_name == "Z":
            # Z
            pygame.draw.line(surface, color, (center_x - size//3, center_y - size//3), (center_x + size//3, center_y - size//3), 3)
            pygame.draw.line(surface, color, (center_x + size//3, center_y - size//3), (center_x - size//3, center_y + size//3), 3)
            pygame.draw.line(surface, color, (center_x - size//3, center_y + size//3), (center_x + size//3, center_y + size//3), 3)
        elif rune_name == "S":
            # S
            pygame.draw.arc(surface, color, (center_x - size//3, center_y - size//3, size//3*2, size//3), 0, 3.14, 3)
            pygame.draw.arc(surface, color, (center_x - size//3, center_y, size//3*2, size//3), 3.14, 6.28, 3)
        elif rune_name == "SPIRAL":
            # Спираль (упрощённая)
            for i in range(3):
                radius = size//6 + i * 3
                pygame.draw.arc(surface, color, (center_x - radius, center_y - radius, radius*2, radius*2), i*2, i*2 + 3.14, 2)
        
        # Название руны
        name_text = self.small_font.render(info["name"], True, COLOR_WHITE)
        name_rect = name_text.get_rect(center=(center_x, y + size + 15))
        surface.blit(name_text, name_rect)
        
        # Эффект
        effect_text = self.small_font.render(info["effect"], True, color)
        effect_rect = effect_text.get_rect(center=(center_x, y + size + 30))
        surface.blit(effect_text, effect_rect)
    
    def draw_runes_hints(self, surface: pygame.Surface) -> None:
        """Нарисовать подсказки по всем рунам справа на экране."""
        # Позиция справа
        start_x = WINDOW_WIDTH - 120
        start_y = UI_MARGIN + 100
        spacing = 80
        
        # Заголовок
        title_text = self.font.render("Руны:", True, COLOR_WHITE)
        surface.blit(title_text, (start_x - 10, start_y - 40))
        
        # Рисуем все руны
        y_pos = start_y
        for rune_name in ["CROSS", "CIRCLE", "V", "Z", "S", "SPIRAL"]:
            self.draw_rune_hint(surface, rune_name, start_x, y_pos, 35)
            y_pos += spacing

    def update_last_rune(self, rune: str, current_time: float) -> None:
        """Обновить последнюю распознанную руну."""
        self.last_rune = rune
        self.last_rune_time = current_time

    def draw_hud(
        self,
        surface: pygame.Surface,
        player_hp: float,
        player_max_hp: float,
        wave_number: int,
        enemy_count: int,
        combo_buffer: List[str],
        combo_timer: float,
        current_time: float,
    ) -> None:
        """Нарисовать HUD."""
        y_offset = UI_MARGIN

        # HP
        hp_text = f"HP: {int(player_hp)}/{int(player_max_hp)}"
        hp_surface = self.font.render(hp_text, True, COLOR_WHITE)
        surface.blit(hp_surface, (UI_MARGIN, y_offset))
        y_offset += UI_FONT_SIZE + 5

        # Волна
        wave_text = f"Волна: {wave_number}"
        wave_surface = self.font.render(wave_text, True, COLOR_WHITE)
        surface.blit(wave_surface, (UI_MARGIN, y_offset))
        y_offset += UI_FONT_SIZE + 5

        # Враги
        enemy_text = f"Врагов: {enemy_count}"
        enemy_surface = self.font.render(enemy_text, True, COLOR_WHITE)
        surface.blit(enemy_surface, (UI_MARGIN, y_offset))
        y_offset += UI_FONT_SIZE + 10

        # Комбо
        if combo_buffer:
            combo_text = "Комбо: " + " -> ".join(combo_buffer)
            # Показать таймер комбо
            timer_ratio = combo_timer / COMBO_WINDOW_TIME
            combo_color = COLOR_GREEN if timer_ratio > 0.5 else COLOR_YELLOW
            combo_surface = self.font.render(combo_text, True, combo_color)
            surface.blit(combo_surface, (UI_MARGIN, y_offset))
            y_offset += UI_FONT_SIZE + 5

            # Индикатор таймера комбо
            bar_width = 200
            bar_height = 5
            pygame.draw.rect(
                surface,
                COLOR_GRAY,
                (UI_MARGIN, y_offset, bar_width, bar_height),
            )
            pygame.draw.rect(
                surface,
                combo_color,
                (UI_MARGIN, y_offset, int(bar_width * timer_ratio), bar_height),
            )
            y_offset += bar_height + 10

        # Последняя распознанная руна
        if self.last_rune and (current_time - self.last_rune_time) < self.last_rune_duration:
            alpha = 1.0 - ((current_time - self.last_rune_time) / self.last_rune_duration)
            rune_text = f"Руна: {self.last_rune}"
            rune_surface = self.large_font.render(rune_text, True, COLOR_YELLOW)
            # Центрировать
            text_rect = rune_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            surface.blit(rune_surface, text_rect)
        
        # Подсказки по рунам справа
        self.draw_runes_hints(surface)

    def draw_debug(
        self,
        surface: pygame.Surface,
        recognition_results: List[Tuple[str, float]],
        gesture_point_count: int,
    ) -> None:
        """Нарисовать debug панель."""
        y_offset = WINDOW_HEIGHT - 150
        x_offset = UI_MARGIN

        # Заголовок
        debug_title = self.debug_font.render("DEBUG:", True, COLOR_WHITE)
        surface.blit(debug_title, (x_offset, y_offset))
        y_offset += UI_DEBUG_FONT_SIZE + 5

        # Количество точек жеста
        points_text = f"Точек: {gesture_point_count}"
        points_surface = self.debug_font.render(points_text, True, COLOR_WHITE)
        surface.blit(points_surface, (x_offset, y_offset))
        y_offset += UI_DEBUG_FONT_SIZE + 5

        # Top-3 распознавания
        if recognition_results:
            for i, (rune, score) in enumerate(recognition_results[:3]):
                color = COLOR_GREEN if score >= 0.75 else COLOR_YELLOW if score >= 0.5 else COLOR_RED
                result_text = f"{i+1}. {rune}: {score:.3f}"
                result_surface = self.debug_font.render(result_text, True, color)
                surface.blit(result_surface, (x_offset, y_offset))
                y_offset += UI_DEBUG_FONT_SIZE + 3
        else:
            no_result_text = "Нет результатов"
            no_result_surface = self.debug_font.render(no_result_text, True, COLOR_GRAY)
            surface.blit(no_result_surface, (x_offset, y_offset))

    def draw_game_over(self, surface: pygame.Surface, wave_number: int) -> None:
        """Нарисовать экран Game Over."""
        # Полупрозрачный фон
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))

        # Текст Game Over
        game_over_text = self.large_font.render("GAME OVER", True, COLOR_RED)
        game_over_rect = game_over_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
        surface.blit(game_over_text, game_over_rect)

        # Волна
        wave_text = self.font.render(f"Достигнуто волн: {wave_number}", True, COLOR_WHITE)
        wave_rect = wave_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 20))
        surface.blit(wave_text, wave_rect)

        # Инструкция
        restart_text = self.debug_font.render("Нажмите R для перезапуска", True, COLOR_WHITE)
        restart_rect = restart_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 60))
        surface.blit(restart_text, restart_rect)

    def draw_wave_break(self, surface: pygame.Surface, wave_number: int, time_left: float) -> None:
        """Нарисовать экран перерыва между волнами."""
        # Полупрозрачный фон
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))

        # Текст перерыва
        break_text = self.large_font.render(f"Волна {wave_number} завершена!", True, COLOR_GREEN)
        break_rect = break_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 30))
        surface.blit(break_text, break_rect)

        # Таймер
        timer_text = self.font.render(f"Следующая волна через: {int(time_left)}", True, COLOR_WHITE)
        timer_rect = timer_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 20))
        surface.blit(timer_text, timer_rect)
