import pygame
import numpy as np
import time
from datetime import datetime

# ----------------------------
# ВИРТУАЛЬНОЕ ПОЛЕ (симуляция)
# ----------------------------
# Это "размер мира", который ты хочешь симулировать.
# Если поставишь 3000x3000 — мир будет таким, но на экране он будет уменьшен так,
# чтобы помещаться целиком.
FIELD_PX_W, FIELD_PX_H = 3000, 3000

# ----------------------------
# ОКНО (фактический экран)
# ----------------------------
# Это "желательный размер окна". Если он больше монитора — автоматически возьмём размер монитора.
WINDOW_W, WINDOW_H = 1200, 800

START_FULLSCREEN = False  # можно True

TARGET_FPS = 60

# Цвета (RGB)
COLOR_BG = (0, 0, 30)           # Темно-синий фон
COLOR_WHITE = (220, 220, 255)   # Белые клетки
COLOR_RED = (220, 50, 50)       # Красные клетки

# --- ПЛОТНОСТЬ (в %), одинаковая для обеих сторон ---
DENSITY_PERCENT = 40  # 5..99

# --- АКТИВНОСТЬ -> ВЗРЫВ ---
ACTIVITY_TRIGGER_PERCENT = 0.4
ACTIVITY_PATIENCE = 1
MIN_GENS_BETWEEN_BANGS = 30

# Сценарии взрыва
BIG_BANG_PROB_CENTER = 0.5  # 50/50

# Большой шар
BIG_BANG_FRACTION_OF_GRID = 0.33
BIG_BANG_FILL_DENSITY = 0.45

# Малые шары
SMALL_BANG_COUNT_MIN = 6
SMALL_BANG_COUNT_MAX = 12
SMALL_BANG_RADIUS_MIN = 40
SMALL_BANG_RADIUS_MAX = 90
SMALL_BANG_RADIUS_MAX_FRAC_OF_MINOR = 0.30
SMALL_BANG_FILL_DENSITY = 0.45

# Ограничение перекрытия малых шаров
SMALL_BANG_MAX_OVERLAP_FRAC = 0.20  # максимум 20% перекрытия (по меньшему радиусу)
SMALL_BANG_PLACE_TRIES = 250        # попыток поставить каждый шар

# Детектор циклов: исключаем клетки, которые зациклены (осцилляторы)
OSC_MAX_PERIOD = 4  # 2..4

# Лог-файл
LOG_FILE = "life_stats.log"


class TwoCampGameOfLife:
    def __init__(self, field_w_px, field_h_px, window_w, window_h, scale=4, density_percent=40, start_fullscreen=False):
        pygame.init()

        self.scale = int(max(1, scale))

        # Виртуальное поле (мир)
        self.field_w_px = int(field_w_px)
        self.field_h_px = int(field_h_px)
        self.cols = max(1, self.field_w_px // self.scale)
        self.rows = max(1, self.field_h_px // self.scale)

        # Окно
        self.window_w = int(window_w)
        self.window_h = int(window_h)
        self.fullscreen = bool(start_fullscreen)

        # Создаём окно корректно (с учётом монитора/ретины)
        self.screen = None
        self._create_display()

        pygame.display.set_caption("Game of Life: Two Camps (Scaled View)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 16, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 14)

        # Сетка: 0 - мертво, 1 - белые, 2 - красные
        self.grid = np.zeros((self.rows, self.cols), dtype=np.uint8)

        self.running = True
        self.paused = True
        self.speed = 15
        self.last_update_time = time.time()

        # Счётчики
        self.generation = 0
        self.gen_since_bang = 0
        self.explosions = 0

        # --- Активность ---
        self.activity_trigger = float(ACTIVITY_TRIGGER_PERCENT)
        self.activity_patience = int(ACTIVITY_PATIENCE)
        self.low_activity_streak = 0
        self.min_gens_between_bangs = int(MIN_GENS_BETWEEN_BANGS)

        # Для исключения осцилляторов
        self.history = []
        self.history_limit = max(OSC_MAX_PERIOD + 1, 5)

        # HUD-поля активности
        self.activity_total = 0.0
        self.activity_white = 0.0
        self.activity_red = 0.0
        self.oscillating_percent = 0.0

        # Плотность
        self.density_percent = int(np.clip(density_percent, 5, 99))

        # Палитра для быстрой отрисовки
        self.palette = np.array([COLOR_BG, COLOR_WHITE, COLOR_RED], dtype=np.uint8)

        # --- Разделитель существует только в начале ---
        self.center_x = self.cols // 2
        base_sep = max(15, int(self.cols * 0.20))
        narrowed = max(15, int(round(base_sep * (2.0 / 3.0))))  # сужаем на треть
        self.separator_width = narrowed
        self.sep_left = self.center_x - self.separator_width // 2
        self.sep_right = self.center_x + self.separator_width // 2

        # Трансформация "мир -> экран"
        self.view_scale = 1.0
        self.view_rect = pygame.Rect(0, 0, 1, 1)
        self._update_view_transform()

        # Инициализация по плотности
        self.validate_and_initialize_by_density()

        self.log_event(
            "START",
            extra=f"density={self.density_percent}% grid={self.rows}x{self.cols} scale={self.scale} sep={self.separator_width} fullscreen={self.fullscreen}"
        )

    # ----------------------------
    # Display / Scaling
    # ----------------------------
    def _create_display(self):
        # В pygame 2 на macOS ретина лучше живёт с SCALED
        flags_window = pygame.SCALED | pygame.RESIZABLE
        flags_full = pygame.FULLSCREEN | pygame.SCALED

        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), flags_full)
        else:
            # Подрежем окно под монитор, если просим слишком большое
            info = pygame.display.Info()
            w = min(self.window_w, info.current_w)
            h = min(self.window_h, info.current_h)
            self.screen = pygame.display.set_mode((w, h), flags_window)
            self.window_w, self.window_h = w, h

    def _toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self._create_display()
        self._update_view_transform()

    def _update_view_transform(self):
        sw, sh = self.screen.get_size()

        # Масштабируем так, чтобы ВСЁ поле помещалось целиком
        sx = sw / float(self.cols)
        sy = sh / float(self.rows)
        self.view_scale = min(sx, sy)

        rw = max(1, int(self.cols * self.view_scale))
        rh = max(1, int(self.rows * self.view_scale))
        ox = (sw - rw) // 2
        oy = (sh - rh) // 2

        self.view_rect = pygame.Rect(ox, oy, rw, rh)

    def _screen_to_grid(self, x, y):
        # Преобразуем координаты экрана в координаты сетки (с учётом масштабирования/полос)
        if not self.view_rect.collidepoint(x, y):
            return None

        gx = int((x - self.view_rect.x) / self.view_scale)
        gy = int((y - self.view_rect.y) / self.view_scale)

        if 0 <= gx < self.cols and 0 <= gy < self.rows:
            return gx, gy
        return None

    # ----------------------------
    # Logging
    # ----------------------------
    def log_event(self, event, extra=""):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        w = int(np.sum(self.grid == 1))
        r = int(np.sum(self.grid == 2))
        line = (
            f"[{ts}] {event} | gen={self.generation} gen_since_bang={self.gen_since_bang} "
            f"explosions={self.explosions} white={w} red={r} "
            f"act_total={self.activity_total:.4f}% act_w={self.activity_white:.4f}% act_r={self.activity_red:.4f}% "
            f"osc={self.oscillating_percent:.4f}%"
        )
        if extra:
            line += f" | {extra}"
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass

    # ----------------------------
    # Init by density
    # ----------------------------
    def validate_and_initialize_by_density(self):
        left_capacity = self.rows * max(0, self.sep_left)
        right_capacity = self.rows * max(0, (self.cols - self.sep_right))

        init_red = int(left_capacity * (self.density_percent / 100.0))
        init_white = int(right_capacity * (self.density_percent / 100.0))

        if (init_red + init_white) < 3:
            init_red = 2
            init_white = 1

        self.init_red = min(init_red, left_capacity)
        self.init_white = min(init_white, right_capacity)

        self.randomize_grid()

    def randomize_grid(self):
        self.grid.fill(0)
        self.generation = 0
        self.gen_since_bang = 0
        self.low_activity_streak = 0
        self.history.clear()

        # левый лагерь (красные)
        if self.sep_left > 0 and self.init_red > 0:
            left_mask = np.zeros((self.rows, self.cols), dtype=bool)
            left_mask[:, :self.sep_left] = True
            left_positions = np.flatnonzero(left_mask.ravel())
            k = min(len(left_positions), self.init_red)
            if k > 0:
                chosen = np.random.choice(left_positions, size=k, replace=False)
                self.grid.ravel()[chosen] = 2

        # правый лагерь (белые)
        if self.sep_right < self.cols and self.init_white > 0:
            right_mask = np.zeros((self.rows, self.cols), dtype=bool)
            right_mask[:, self.sep_right:] = True
            right_positions = np.flatnonzero(right_mask.ravel())
            k = min(len(right_positions), self.init_white)
            if k > 0:
                chosen = np.random.choice(right_positions, size=k, replace=False)
                self.grid.ravel()[chosen] = 1

        self.activity_total = 0.0
        self.activity_white = 0.0
        self.activity_red = 0.0
        self.oscillating_percent = 0.0

    # ----------------------------
    # Neighbors
    # ----------------------------
    def count_neighbors_vectorized(self, grid_mask):
        grid = grid_mask.astype(np.uint8)
        neighbors = np.zeros_like(grid, dtype=np.uint8)

        neighbors[1:, :] += grid[:-1, :]     # N
        neighbors[:-1, :] += grid[1:, :]     # S
        neighbors[:, 1:] += grid[:, :-1]     # W
        neighbors[:, :-1] += grid[:, 1:]     # E

        neighbors[1:, 1:] += grid[:-1, :-1]  # NW
        neighbors[1:, :-1] += grid[:-1, 1:]  # NE
        neighbors[:-1, 1:] += grid[1:, :-1]  # SW
        neighbors[:-1, :-1] += grid[1:, 1:]  # SE

        return neighbors

    # ----------------------------
    # Activity & Oscillators
    # ----------------------------
    def compute_oscillating_mask(self, old_grid, new_grid):
        if len(self.history) < 2:
            return np.zeros_like(old_grid, dtype=bool)

        changed = (new_grid != old_grid)
        osc_mask = np.zeros_like(old_grid, dtype=bool)

        max_k = min(OSC_MAX_PERIOD, len(self.history))
        for k in range(2, max_k + 1):
            prev_k = self.history[-k]
            osc_mask |= changed & (new_grid == prev_k)

        return osc_mask

    def compute_activity(self, old_grid, new_grid):
        total_cells = old_grid.size
        changed = (new_grid != old_grid)

        osc_mask = self.compute_oscillating_mask(old_grid, new_grid)
        active = changed & (~osc_mask)

        active_white = active & ((old_grid == 1) | (new_grid == 1))
        active_red = active & ((old_grid == 2) | (new_grid == 2))

        act_total_percent = float(active.mean() * 100.0)
        act_white_percent = float(active_white.sum() / total_cells * 100.0)
        act_red_percent = float(active_red.sum() / total_cells * 100.0)
        osc_percent = float(osc_mask.mean() * 100.0)

        return act_total_percent, act_white_percent, act_red_percent, osc_percent

    # ----------------------------
    # Bang helpers
    # ----------------------------
    def _apply_ball(self, cy, cx, r, fill_density):
        if r <= 1:
            return 0, 0

        yy, xx = np.ogrid[-r:r+1, -r:r+1]
        disk = (xx * xx + yy * yy) <= (r * r)

        dy, dx = np.where(disk)
        dy = dy - r
        dx = dx - r

        ys = (cy + dy).astype(np.int32)
        xs = (cx + dx).astype(np.int32)

        inside = (ys >= 0) & (ys < self.rows) & (xs >= 0) & (xs < self.cols)
        ys = ys[inside]
        xs = xs[inside]

        cap = ys.size
        if cap <= 0:
            return 0, 0

        self.grid[ys, xs] = 0

        k = int(cap * float(fill_density))
        k = max(k, 200)
        k = min(k, cap)

        chosen_idx = np.random.choice(cap, size=k, replace=False)

        assign = np.empty(k, dtype=np.uint8)
        half = k // 2
        assign[:half] = 1
        assign[half:] = 2
        np.random.shuffle(assign)

        self.grid[ys[chosen_idx], xs[chosen_idx]] = assign
        return cap, k

    def _big_center_bang(self):
        total_cells = self.rows * self.cols
        target_area = int(total_cells * float(BIG_BANG_FRACTION_OF_GRID))
        r_from_area = int(np.sqrt(target_area / np.pi))
        r_min = int(min(self.rows, self.cols) / 3)
        r = max(r_from_area, r_min)
        r = min(r, (min(self.rows, self.cols) // 2) - 2)

        cy, cx = self.rows // 2, self.cols // 2
        cap, k = self._apply_ball(cy, cx, r, BIG_BANG_FILL_DENSITY)
        return {"scenario": "center", "balls": 1, "r": r, "cap": cap, "k": k}

    def _multi_small_bang(self):
        balls_target = int(np.random.randint(SMALL_BANG_COUNT_MIN, SMALL_BANG_COUNT_MAX + 1))

        minor = min(self.rows, self.cols)
        r_cap = int(minor * SMALL_BANG_RADIUS_MAX_FRAC_OF_MINOR)
        r_hi = min(SMALL_BANG_RADIUS_MAX, r_cap)
        r_lo = min(SMALL_BANG_RADIUS_MIN, r_hi)
        if r_hi < 5:
            return {"scenario": "multi", "balls": 0, "r_min": 0, "r_max": 0, "sum_k": 0}

        placed = []  # (cy, cx, r)
        sum_k = 0
        r_min_used = 10**9
        r_max_used = 0

        def ok_place(cy, cx, r):
            for (py, px, pr) in placed:
                dy = cy - py
                dx = cx - px
                d = (dy * dy + dx * dx) ** 0.5
                allowed_overlap = SMALL_BANG_MAX_OVERLAP_FRAC * min(r, pr)
                # запрещаем сильное пересечение
                if d < (r + pr - allowed_overlap):
                    return False
            return True

        for _ in range(balls_target):
            success = False
            for _try in range(SMALL_BANG_PLACE_TRIES):
                r = int(np.random.randint(r_lo, r_hi + 1))

                cy = int(np.random.randint(r, self.rows - r)) if (self.rows - 2 * r) > 0 else self.rows // 2
                cx = int(np.random.randint(r, self.cols - r)) if (self.cols - 2 * r) > 0 else self.cols // 2

                if ok_place(cy, cx, r):
                    placed.append((cy, cx, r))
                    r_min_used = min(r_min_used, r)
                    r_max_used = max(r_max_used, r)
                    _, k = self._apply_ball(cy, cx, r, SMALL_BANG_FILL_DENSITY)
                    sum_k += k
                    success = True
                    break

            if not success:
                continue

        if r_min_used == 10**9:
            r_min_used = 0

        return {"scenario": "multi", "balls": len(placed), "r_min": r_min_used, "r_max": r_max_used, "sum_k": sum_k}

    def big_bang(self):
        if np.random.random() < BIG_BANG_PROB_CENTER:
            info = self._big_center_bang()
        else:
            info = self._multi_small_bang()

        self.explosions += 1
        self.log_event("BIG_BANG", extra=str(info))
        self.gen_since_bang = 0
        self.low_activity_streak = 0
        self.history.clear()

    # ----------------------------
    # Logic update
    # ----------------------------
    def update_logic(self):
        old_grid = self.grid

        is_white = (old_grid == 1)
        is_red = (old_grid == 2)
        is_alive = is_white | is_red

        white_neighbors = self.count_neighbors_vectorized(is_white)
        red_neighbors = self.count_neighbors_vectorized(is_red)
        total_neighbors = white_neighbors + red_neighbors

        survivors_mask = is_alive & ((total_neighbors == 2) | (total_neighbors == 3))
        newborn_mask = (~is_alive) & (total_neighbors == 3)

        new_grid = np.zeros_like(old_grid)

        new_grid[survivors_mask] = old_grid[survivors_mask]

        majority_white = (white_neighbors > red_neighbors)
        majority_red = (red_neighbors > white_neighbors)
        tie = (white_neighbors == red_neighbors)

        new_grid[newborn_mask & majority_white] = 1
        new_grid[newborn_mask & majority_red] = 2

        # Ничья -> случайно (зафиксировано)
        tie_newborn = newborn_mask & tie
        if np.any(tie_newborn):
            random_choices = np.random.choice([1, 2], size=old_grid.shape).astype(np.uint8)
            new_grid[tie_newborn] = random_choices[tie_newborn]

        # Активность (исключая осцилляторы)
        act_total, act_white, act_red, osc_percent = self.compute_activity(old_grid, new_grid)
        self.activity_total = act_total
        self.activity_white = act_white
        self.activity_red = act_red
        self.oscillating_percent = osc_percent

        # history
        self.history.append(old_grid.copy())
        if len(self.history) > self.history_limit:
            self.history.pop(0)

        # применяем
        self.grid = new_grid
        self.generation += 1
        self.gen_since_bang += 1

        # Взрыв, если активность ниже порога
        if self.activity_total < self.activity_trigger:
            self.low_activity_streak += 1
        else:
            self.low_activity_streak = 0

        if self.low_activity_streak >= self.activity_patience:
            if self.gen_since_bang >= self.min_gens_between_bangs:
                self.big_bang()
            else:
                self.low_activity_streak = 0

    # ----------------------------
    # Input
    # ----------------------------
    def handle_input(self):
        keys = pygame.key.get_pressed()
        shift_held = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.VIDEORESIZE:
                # Работает при RESIZABLE
                self._update_view_transform()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_r:
                    self.validate_and_initialize_by_density()
                    self.log_event("RESET", extra=f"density={self.density_percent}%")
                elif event.key == pygame.K_c:
                    self.grid.fill(0)
                    self.generation = 0
                    self.gen_since_bang = 0
                    self.low_activity_streak = 0
                    self.history.clear()
                    self.log_event("CLEAR")
                elif event.key == pygame.K_UP:
                    self.speed = min(60, self.speed + 2)
                elif event.key == pygame.K_DOWN:
                    self.speed = max(1, self.speed - 2)

                # Fullscreen toggle (на маке удобно)
                elif event.key == pygame.K_f:
                    self._toggle_fullscreen()

                # тест: менять плотность
                elif event.key == pygame.K_1:
                    self.density_percent = int(np.clip(self.density_percent - 5, 5, 99))
                    self.validate_and_initialize_by_density()
                    self.log_event("DENSITY", extra=f"set={self.density_percent}%")
                elif event.key == pygame.K_2:
                    self.density_percent = int(np.clip(self.density_percent + 5, 5, 99))
                    self.validate_and_initialize_by_density()
                    self.log_event("DENSITY", extra=f"set={self.density_percent}%")

                # ручной взрыв
                elif event.key == pygame.K_b:
                    if self.gen_since_bang >= self.min_gens_between_bangs:
                        self.big_bang()

        # Рисование мышью (с учётом масштабирования)
        mouse_pressed = pygame.mouse.get_pressed()
        x, y = pygame.mouse.get_pos()
        gpos = self._screen_to_grid(x, y)
        if gpos is None:
            return

        grid_x, grid_y = gpos

        if shift_held and mouse_pressed[0]:
            self.grid[grid_y, grid_x] = 0
        elif mouse_pressed[0]:
            self.grid[grid_y, grid_x] = 1
        elif mouse_pressed[2]:
            self.grid[grid_y, grid_x] = 2

    # ----------------------------
    # HUD + Draw
    # ----------------------------
    def draw_hud(self):
        count_white = int(np.sum(self.grid == 1))
        count_red = int(np.sum(self.grid == 2))

        panel_h = 42
        s = pygame.Surface((self.screen.get_width(), panel_h))
        s.set_alpha(200)
        s.fill((0, 0, 0))
        self.screen.blit(s, (0, 0))

        stats = (
            f"Field:{self.cols}x{self.rows} | Gen:{self.generation} | SinceBang:{self.gen_since_bang} | Expl:{self.explosions} | "
            f"W:{count_white} R:{count_red} | Spd:{self.speed}/s | Den:{self.density_percent}% | "
            f"ActTot:{self.activity_total:.4f}% ActW:{self.activity_white:.4f}% ActR:{self.activity_red:.4f}% | "
            f"Osc:{self.oscillating_percent:.4f}% | Bang< {self.activity_trigger:.2f}% | F:Fullscreen"
        )
        t = self.small_font.render(stats, True, (230, 230, 230))
        self.screen.blit(t, (20, 14))

        if self.paused:
            help_s = pygame.Surface((520, 130))
            help_s.set_alpha(180)
            help_s.fill((0, 0, 0))
            self.screen.blit(help_s, (10, self.screen.get_height() - 140))

            controls = [
                "PAUSED",
                "L-Click: White | R-Click: Red",
                "Shift+Click: Erase",
                "Space: Run | R: Reset | C: Clear",
                "Arrows: Adjust Speed",
                "1/2: Density -/+ 5% (restarts)",
                "B: Big Bang (manual test)",
                "F: Toggle Fullscreen"
            ]
            for i, line in enumerate(controls):
                c = COLOR_WHITE if i > 0 else (255, 255, 0)
                t2 = self.small_font.render(line, True, c)
                self.screen.blit(t2, (20, self.screen.get_height() - 130 + i * 18))

    def draw(self):
        # 1) Рендерим "мир" в поверхность cols x rows
        rgb_array = self.palette[self.grid]
        surface = pygame.surfarray.make_surface(rgb_array.swapaxes(0, 1))

        # 2) Масштабируем под окно так, чтобы всё поле было видно
        if surface.get_width() != self.view_rect.w or surface.get_height() != self.view_rect.h:
            surface = pygame.transform.scale(surface, (self.view_rect.w, self.view_rect.h))

        # 3) Заливаем фон и рисуем поле (с возможными "полосами")
        self.screen.fill(COLOR_BG)
        self.screen.blit(surface, (self.view_rect.x, self.view_rect.y))

        # HUD поверх
        self.draw_hud()
        pygame.display.flip()

    # ----------------------------
    # Main loop
    # ----------------------------
    def run(self):
        while self.running:
            self.handle_input()

            current_time = time.time()
            if not self.paused and (current_time - self.last_update_time) > (1.0 / self.speed):
                self.update_logic()
                self.last_update_time = current_time

            self.draw()
            self.clock.tick(TARGET_FPS)

        self.log_event("END")
        pygame.quit()


if __name__ == "__main__":
    game = TwoCampGameOfLife(
        field_w_px=FIELD_PX_W,
        field_h_px=FIELD_PX_H,
        window_w=WINDOW_W,
        window_h=WINDOW_H,
        scale=4,
        density_percent=DENSITY_PERCENT,
        start_fullscreen=START_FULLSCREEN
    )
    game.run()
