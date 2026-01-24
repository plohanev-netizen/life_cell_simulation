import pygame
import numpy as np
import time
from datetime import datetime

# ----------------------------
# ВИРТУАЛЬНОЕ ПОЛЕ (симуляция)
# ----------------------------
FIELD_PX_W, FIELD_PX_H = 3000, 3000

# ----------------------------
# ОКНО (фактический экран)
# ----------------------------
WINDOW_W, WINDOW_H = 1200, 800
START_FULLSCREEN = False

TARGET_FPS = 60

# Цвета (RGB)
COLOR_BG = (0, 0, 30)
COLOR_WHITE = (220, 220, 255)
COLOR_RED = (220, 50, 50)

# --- ПЛОТНОСТЬ (в %), одинаковая для обеих сторон ---
DENSITY_PERCENT = 45  # 5..99

# --- АКТИВНОСТЬ -> ВЗРЫВ ---
ACTIVITY_TRIGGER_PERCENT = 0.2
ACTIVITY_PATIENCE = 1
MIN_GENS_BETWEEN_BANGS = 30

# Сценарии взрыва
BIG_BANG_PROB_CENTER = 0.5

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
SMALL_BANG_MAX_OVERLAP_FRAC = 0.20
SMALL_BANG_PLACE_TRIES = 250

# Детектор циклов
OSC_MAX_PERIOD = 4

# Лог-файл
LOG_FILE = "life_stats.log"


class StatsRecorder:
    """
    Хранит историю метрик по поколениям.
    X = generation (0..N-1)
    Y = counts:
      POPULATION:
        1) alive_total
        2) alive_red
        3) alive_white
      ACTIVITY:
        4) active_total
        5) active_red
        6) active_white
    """
    def __init__(self):
        self.reset()

    def reset(self):
        self.gen = []
        self.alive_total = []
        self.alive_red = []
        self.alive_white = []
        self.active_total = []
        self.active_red = []
        self.active_white = []

    def append(self, gen, alive_total, alive_red, alive_white, active_total, active_red, active_white):
        self.gen.append(int(gen))
        self.alive_total.append(int(alive_total))
        self.alive_red.append(int(alive_red))
        self.alive_white.append(int(alive_white))
        self.active_total.append(int(active_total))
        self.active_red.append(int(active_red))
        self.active_white.append(int(active_white))

    def has_data(self):
        return len(self.gen) > 1

    def _downsample(self, x, y, max_points):
        n = len(x)
        if n <= max_points:
            return x, y
        idx = np.linspace(0, n - 1, max_points).astype(np.int32)
        return [x[i] for i in idx], [y[i] for i in idx]

    def _render_chart(self, w, h, title, x, series, font, small_font):
        """
        Рисует один график (серии линий) на поверхности размером w*h.
        series: list of (name, y_list, color)
        """
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 220))

        pad = 55
        left = pad
        top = pad
        right = w - pad
        bottom = h - pad

        pygame.draw.rect(surf, (200, 200, 200, 255), (left, top, right - left, bottom - top), 2)

        if len(x) < 2:
            txt = font.render("No data", True, (255, 255, 255))
            surf.blit(txt, (left + 20, top + 20))
            return surf

        max_points = max(200, min(1400, right - left))

        x_min = x[0]
        x_max = x[-1] if x[-1] != x_min else (x_min + 1)

        down = []
        y_max = 1
        for name, y, col in series:
            xd, yd = self._downsample(x, y, max_points)
            down.append((name, xd, yd, col))
            y_max = max(y_max, max(yd) if len(yd) else 1)

        # axes
        pygame.draw.line(surf, (200, 200, 200), (left, bottom), (right, bottom), 2)
        pygame.draw.line(surf, (200, 200, 200), (left, top), (left, bottom), 2)

        # labels
        surf.blit(small_font.render("Generations (X)", True, (230, 230, 230)), (left + 10, bottom + 10))
        surf.blit(small_font.render("Count (Y)", True, (230, 230, 230)), (10, top - 28))

        # y ticks
        ticks = 5
        for i in range(ticks + 1):
            ty = top + int((bottom - top) * (i / ticks))
            val = int(y_max * (1 - i / ticks))
            pygame.draw.line(surf, (120, 120, 120), (left - 6, ty), (left, ty), 2)
            lab = small_font.render(str(val), True, (200, 200, 200))
            surf.blit(lab, (left - 12 - lab.get_width(), ty - lab.get_height() // 2))

        def to_px(gx, gy):
            px = left + int((gx - x_min) / (x_max - x_min) * (right - left))
            py = top + int((1 - (gy / y_max)) * (bottom - top))
            return px, py

        # draw lines
        for name, xd, yd, col in down:
            pts = [to_px(gx, gy) for gx, gy in zip(xd, yd)]
            if len(pts) >= 2:
                pygame.draw.lines(surf, col, False, pts, 2)

        # legend
        lx = right - 240
        ly = top + 10
        for name, _, __, col in down:
            pygame.draw.rect(surf, col, (lx, ly + 5, 18, 10))
            surf.blit(small_font.render(name, True, (240, 240, 240)), (lx + 28, ly))
            ly += 18

        # title
        t = font.render(title, True, (255, 255, 255))
        surf.blit(t, (left, 14))

        return surf

    def render_population_and_activity(self, w, h, font, small_font):
        """
        Два графика: сверху POPULATION (3 линии), снизу ACTIVITY (3 линии).
        """
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 220))

        if not self.has_data():
            txt = font.render("No stats yet", True, (255, 255, 255))
            surf.blit(txt, (30, 30))
            return surf

        # внешний заголовок + рамка
        pygame.draw.rect(surf, (220, 220, 220, 255), (0, 0, w, h), 2)
        head = font.render("Statistics (T close, G external plot)", True, (255, 255, 255))
        surf.blit(head, (18, 14))

        # размеры двух графиков
        gap = 14
        top_pad = 46
        chart_h = (h - top_pad - gap - 18) // 2
        chart_w = w - 18 * 2

        x = self.gen

        pop_series = [
            ("Alive Total", self.alive_total, (230, 230, 230)),
            ("Alive Red", self.alive_red, (255, 80, 80)),
            ("Alive White", self.alive_white, (200, 200, 255)),
        ]
        act_series = [
            ("Active Total", self.active_total, (255, 220, 120)),
            ("Active Red", self.active_red, (255, 140, 120)),
            ("Active White", self.active_white, (180, 255, 255)),
        ]

        pop_s = self._render_chart(
            chart_w, chart_h,
            "Population",
            x, pop_series,
            font, small_font
        )
        act_s = self._render_chart(
            chart_w, chart_h,
            "Activity",
            x, act_series,
            font, small_font
        )

        surf.blit(pop_s, (18, top_pad))
        surf.blit(act_s, (18, top_pad + chart_h + gap))

        return surf

    def open_matplotlib(self):
        try:
            import matplotlib.pyplot as plt
        except Exception:
            return False
        if not self.has_data():
            return False

        x = np.array(self.gen)

        fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
        fig.canvas.manager.set_window_title("Game of Life Stats")

        # Population
        axes[0].plot(x, self.alive_total, label="Alive Total")
        axes[0].plot(x, self.alive_red, label="Alive Red")
        axes[0].plot(x, self.alive_white, label="Alive White")
        axes[0].set_ylabel("Count")
        axes[0].set_title("Population")
        axes[0].legend()

        # Activity
        axes[1].plot(x, self.active_total, label="Active Total")
        axes[1].plot(x, self.active_red, label="Active Red")
        axes[1].plot(x, self.active_white, label="Active White")
        axes[1].set_xlabel("Generation")
        axes[1].set_ylabel("Count")
        axes[1].set_title("Activity")
        axes[1].legend()

        plt.tight_layout()
        plt.show()
        return True


class ManualBlast:
    def __init__(self, hold_seconds=0.5, radius_cells=40):
        self.hold_seconds = float(hold_seconds)
        self.radius_cells = int(radius_cells)
        self.holding = False
        self.triggered = False
        self.start_time = 0.0

    def start_hold(self):
        self.holding = True
        self.triggered = False
        self.start_time = time.time()

    def stop_hold(self):
        self.holding = False
        self.triggered = False
        self.start_time = 0.0

    def should_trigger(self):
        if not self.holding or self.triggered:
            return False
        return (time.time() - self.start_time) >= self.hold_seconds

    def mark_triggered(self):
        self.triggered = True


class TwoCampGameOfLife:
    def __init__(self, field_w_px, field_h_px, window_w, window_h, scale=4, density_percent=40, start_fullscreen=False):
        pygame.init()

        self.scale = int(max(1, scale))

        self.field_w_px = int(field_w_px)
        self.field_h_px = int(field_h_px)
        self.cols = max(1, self.field_w_px // self.scale)
        self.rows = max(1, self.field_h_px // self.scale)

        self.window_w = int(window_w)
        self.window_h = int(window_h)
        self.fullscreen = bool(start_fullscreen)

        self.screen = None
        self._create_display()

        pygame.display.set_caption("Game of Life: Two Camps (Scaled View)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 16, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 14)

        self.grid = np.zeros((self.rows, self.cols), dtype=np.uint8)

        self.running = True
        self.paused = True
        self.speed = 15
        self.last_update_time = time.time()

        self.generation = 0
        self.gen_since_bang = 0
        self.explosions = 0
        self.manual_explosions = 0

        self.activity_trigger = float(ACTIVITY_TRIGGER_PERCENT)
        self.activity_patience = int(ACTIVITY_PATIENCE)
        self.low_activity_streak = 0
        self.min_gens_between_bangs = int(MIN_GENS_BETWEEN_BANGS)

        self.history = []
        self.history_limit = max(OSC_MAX_PERIOD + 1, 5)

        self.activity_total = 0.0
        self.activity_white = 0.0
        self.activity_red = 0.0
        self.oscillating_percent = 0.0

        self.active_total_count = 0
        self.active_white_count = 0
        self.active_red_count = 0

        self.density_percent = int(np.clip(density_percent, 5, 99))
        self.palette = np.array([COLOR_BG, COLOR_WHITE, COLOR_RED], dtype=np.uint8)

        # Разделитель (для старта)
        self.center_x = self.cols // 2
        base_sep = max(15, int(self.cols * 0.20))
        narrowed = max(15, int(round(base_sep * (2.0 / 3.0))))
        self.separator_width = narrowed
        self.sep_left = self.center_x - self.separator_width // 2
        self.sep_right = self.center_x + self.separator_width // 2

        # View transform
        self.view_scale = 1.0
        self.view_rect = pygame.Rect(0, 0, 1, 1)
        self._update_view_transform()

        # Manual blast
        self.manual_blast = ManualBlast(hold_seconds=0.5, radius_cells=40)

        # Stats
        self.stats = StatsRecorder()
        self.show_stats = False
        self.stats_surface_cache = None
        self.stats_cache_gen = -1

        # Controls overlay
        self.controls_toggle = False
        self.controls_start_until = time.time() + 3.0

        self.validate_and_initialize_by_density()

        self.log_event(
            "START",
            extra=f"density={self.density_percent}% grid={self.rows}x{self.cols} scale={self.scale} sep={self.separator_width} fullscreen={self.fullscreen}"
        )

    # ----------------------------
    # Display / Scaling
    # ----------------------------
    def _create_display(self):
        flags_window = pygame.SCALED | pygame.RESIZABLE
        flags_full = pygame.FULLSCREEN | pygame.SCALED
        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), flags_full)
        else:
            info = pygame.display.Info()
            w = min(self.window_w, info.current_w)
            h = min(self.window_h, info.current_h)
            self.screen = pygame.display.set_mode((w, h), flags_window)
            self.window_w, self.window_h = w, h

    def _toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self._create_display()
        self._update_view_transform()
        self._invalidate_stats_cache()

    def _update_view_transform(self):
        sw, sh = self.screen.get_size()
        sx = sw / float(self.cols)
        sy = sh / float(self.rows)
        self.view_scale = min(sx, sy)

        rw = max(1, int(self.cols * self.view_scale))
        rh = max(1, int(self.rows * self.view_scale))
        ox = (sw - rw) // 2
        oy = (sh - rh) // 2
        self.view_rect = pygame.Rect(ox, oy, rw, rh)

    def _screen_to_grid(self, x, y):
        if not self.view_rect.collidepoint(x, y):
            return None
        gx = int((x - self.view_rect.x) / self.view_scale)
        gy = int((y - self.view_rect.y) / self.view_scale)
        if 0 <= gx < self.cols and 0 <= gy < self.rows:
            return gx, gy
        return None

    # ----------------------------
    # Cache helpers
    # ----------------------------
    def _invalidate_stats_cache(self):
        self.stats_surface_cache = None
        self.stats_cache_gen = -1

    # ----------------------------
    # Logging
    # ----------------------------
    def log_event(self, event, extra=""):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        w = int(np.sum(self.grid == 1))
        r = int(np.sum(self.grid == 2))
        line = (
            f"[{ts}] {event} | gen={self.generation} gen_since_bang={self.gen_since_bang} "
            f"explosions={self.explosions} manual_explosions={self.manual_explosions} white={w} red={r} "
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

        self.stats.reset()
        self._invalidate_stats_cache()

        if self.sep_left > 0 and self.init_red > 0:
            left_mask = np.zeros((self.rows, self.cols), dtype=bool)
            left_mask[:, :self.sep_left] = True
            left_positions = np.flatnonzero(left_mask.ravel())
            k = min(len(left_positions), self.init_red)
            if k > 0:
                chosen = np.random.choice(left_positions, size=k, replace=False)
                self.grid.ravel()[chosen] = 2

        if self.sep_right < self.cols and self.init_white > 0:
            right_mask = np.zeros((self.rows, self.cols), dtype=bool)
            right_mask[:, self.sep_right:] = True
            right_positions = np.flatnonzero(right_mask.ravel())
            k = min(len(right_positions), self.init_white)
            if k > 0:
                chosen = np.random.choice(right_positions, size=k, replace=False)
                self.grid.ravel()[chosen] = 1

        self._append_stats_point(active_total=0, active_red=0, active_white=0)
        self.controls_start_until = time.time() + 3.0

    def _append_stats_point(self, active_total, active_red, active_white):
        alive_white = int(np.sum(self.grid == 1))
        alive_red = int(np.sum(self.grid == 2))
        alive_total = alive_white + alive_red

        self.stats.append(
            gen=self.generation,
            alive_total=alive_total,
            alive_red=alive_red,
            alive_white=alive_white,
            active_total=active_total,
            active_red=active_red,
            active_white=active_white
        )

    # ----------------------------
    # Neighbors
    # ----------------------------
    def count_neighbors_vectorized(self, grid_mask):
        grid = grid_mask.astype(np.uint8)
        neighbors = np.zeros_like(grid, dtype=np.uint8)

        neighbors[1:, :] += grid[:-1, :]
        neighbors[:-1, :] += grid[1:, :]
        neighbors[:, 1:] += grid[:, :-1]
        neighbors[:, :-1] += grid[:, 1:]

        neighbors[1:, 1:] += grid[:-1, :-1]
        neighbors[1:, :-1] += grid[:-1, 1:]
        neighbors[:-1, 1:] += grid[1:, :-1]
        neighbors[:-1, :-1] += grid[1:, 1:]

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

        active_total_count = int(active.sum())
        active_white_count = int(active_white.sum())
        active_red_count = int(active_red.sum())

        act_total_percent = float(active.mean() * 100.0)
        act_white_percent = float(active_white_count / total_cells * 100.0)
        act_red_percent = float(active_red_count / total_cells * 100.0)
        osc_percent = float(osc_mask.mean() * 100.0)

        return (act_total_percent, act_white_percent, act_red_percent, osc_percent,
                active_total_count, active_white_count, active_red_count)

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
    # Manual blast action
    # ----------------------------
    def manual_boom_at(self, gx, gy):
        r = self.manual_blast.radius_cells
        cap, k = self._apply_ball(gy, gx, r, fill_density=0.45)

        self.manual_explosions += 1
        self.log_event("MANUAL_BANG", extra=f"center=({gx},{gy}) r={r} cap={cap} k={k}")

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

        tie_newborn = newborn_mask & tie
        if np.any(tie_newborn):
            random_choices = np.random.choice([1, 2], size=old_grid.shape).astype(np.uint8)
            new_grid[tie_newborn] = random_choices[tie_newborn]

        (act_total, act_white, act_red, osc_percent,
         active_total_count, active_white_count, active_red_count) = self.compute_activity(old_grid, new_grid)

        self.activity_total = act_total
        self.activity_white = act_white
        self.activity_red = act_red
        self.oscillating_percent = osc_percent

        self.active_total_count = active_total_count
        self.active_white_count = active_white_count
        self.active_red_count = active_red_count

        self.history.append(old_grid.copy())
        if len(self.history) > self.history_limit:
            self.history.pop(0)

        self.grid = new_grid
        self.generation += 1
        self.gen_since_bang += 1

        self._append_stats_point(
            active_total=self.active_total_count,
            active_red=self.active_red_count,
            active_white=self.active_white_count
        )
        self._invalidate_stats_cache()

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
                self._update_view_transform()
                self._invalidate_stats_cache()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused

                elif event.key == pygame.K_h:
                    self.controls_toggle = not self.controls_toggle

                elif event.key == pygame.K_t:
                    if self.paused:
                        self.show_stats = not self.show_stats
                        self._invalidate_stats_cache()

                elif event.key == pygame.K_g:
                    if self.paused:
                        self.stats.open_matplotlib()

                elif event.key == pygame.K_r:
                    self.validate_and_initialize_by_density()
                    self.log_event("RESET", extra=f"density={self.density_percent}%")

                elif event.key == pygame.K_c:
                    self.grid.fill(0)
                    self.generation = 0
                    self.gen_since_bang = 0
                    self.low_activity_streak = 0
                    self.history.clear()
                    self.stats.reset()
                    self._invalidate_stats_cache()
                    self._append_stats_point(active_total=0, active_red=0, active_white=0)
                    self.controls_start_until = time.time() + 3.0
                    self.log_event("CLEAR")

                elif event.key == pygame.K_UP:
                    self.speed = min(60, self.speed + 2)
                elif event.key == pygame.K_DOWN:
                    self.speed = max(1, self.speed - 2)

                elif event.key == pygame.K_f:
                    self._toggle_fullscreen()

                elif event.key == pygame.K_1:
                    self.density_percent = int(np.clip(self.density_percent - 5, 5, 99))
                    self.validate_and_initialize_by_density()
                    self.log_event("DENSITY", extra=f"set={self.density_percent}%")
                elif event.key == pygame.K_2:
                    self.density_percent = int(np.clip(self.density_percent + 5, 5, 99))
                    self.validate_and_initialize_by_density()
                    self.log_event("DENSITY", extra=f"set={self.density_percent}%")

                elif event.key == pygame.K_b:
                    if self.gen_since_bang >= self.min_gens_between_bangs:
                        self.big_bang()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and not shift_held:
                    self.manual_blast.start_hold()

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.manual_blast.stop_hold()

        mx, my = pygame.mouse.get_pos()
        gpos = self._screen_to_grid(mx, my)

        if gpos is not None and self.manual_blast.should_trigger():
            gx, gy = gpos
            self.manual_boom_at(gx, gy)
            self.manual_blast.mark_triggered()

        mouse_pressed = pygame.mouse.get_pressed()
        if gpos is None:
            return

        grid_x, grid_y = gpos

        if self.manual_blast.holding and self.manual_blast.triggered:
            return

        if shift_held and mouse_pressed[0]:
            self.grid[grid_y, grid_x] = 0
        elif mouse_pressed[0]:
            self.grid[grid_y, grid_x] = 1
        elif mouse_pressed[2]:
            self.grid[grid_y, grid_x] = 2

    # ----------------------------
    # Overlays
    # ----------------------------
    def draw_controls_overlay(self):
        now = time.time()
        show = self.controls_toggle or (now < self.controls_start_until)
        if not show:
            return

        w = int(self.screen.get_width() * 0.62)
        h = int(self.screen.get_height() * 0.45)
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 210))
        pygame.draw.rect(surf, (220, 220, 220, 255), (0, 0, w, h), 2)

        title = self.font.render("CONTROLS", True, (255, 255, 0))
        surf.blit(title, (18, 14))

        lines = [
            "Space: Pause / Run",
            "H: Show / Hide this overlay",
            "F: Toggle Fullscreen",
            "T: Stats overlay (pause)",
            "G: Open matplotlib plot (pause)",
            "R: Restart (same density)",
            "C: Clear field",
            "Up/Down: Speed +/-",
            "1/2: Density -/+ 5% (restart)",
            "B: Force algorithmic big bang (debug)",
            "",
            "Mouse:",
            "L-Click: Paint WHITE",
            "R-Click: Paint RED",
            "Shift + L-Click: Erase",
            "Hold L-Click ~0.5s: MANUAL mini-bang (radius 40 cells)",
            "",
            "press h to show controls",
        ]

        y = 52
        for line in lines:
            color = (240, 240, 240)
            if line == "press h to show controls":
                color = (180, 220, 255)
            t = self.small_font.render(line, True, color)
            surf.blit(t, (18, y))
            y += 18

        ox = (self.screen.get_width() - w) // 2
        oy = (self.screen.get_height() - h) // 2
        self.screen.blit(surf, (ox, oy))

    # ----------------------------
    # HUD + Draw
    # ----------------------------
    def draw_hud(self):
        count_white = int(np.sum(self.grid == 1))
        count_red = int(np.sum(self.grid == 2))

        panel_h = 50
        s = pygame.Surface((self.screen.get_width(), panel_h))
        s.set_alpha(200)
        s.fill((0, 0, 0))
        self.screen.blit(s, (0, 0))

        stats = (
            f"Field:{self.cols}x{self.rows} | Gen:{self.generation} | SinceBang:{self.gen_since_bang} | "
            f"Expl:{self.explosions} | ManExpl:{self.manual_explosions} | "
            f"W:{count_white} R:{count_red} | Spd:{self.speed}/s | Den:{self.density_percent}% | "
            f"ActTot:{self.activity_total:.4f}% | Bang< {self.activity_trigger:.2f}% | "
            f"H:Controls | F:Fullscreen | T:Stats"
        )
        t = self.small_font.render(stats, True, (230, 230, 230))
        self.screen.blit(t, (20, 18))

    def draw(self):
        rgb_array = self.palette[self.grid]
        surface = pygame.surfarray.make_surface(rgb_array.swapaxes(0, 1))
        if surface.get_width() != self.view_rect.w or surface.get_height() != self.view_rect.h:
            surface = pygame.transform.scale(surface, (self.view_rect.w, self.view_rect.h))

        self.screen.fill(COLOR_BG)
        self.screen.blit(surface, (self.view_rect.x, self.view_rect.y))

        self.draw_hud()

        if self.paused and self.show_stats:
            if (self.stats_surface_cache is None) or (self.stats_cache_gen != self.generation):
                w = int(self.screen.get_width() * 0.92)
                h = int(self.screen.get_height() * 0.86)
                self.stats_surface_cache = self.stats.render_population_and_activity(w, h, self.font, self.small_font)
                self.stats_cache_gen = self.generation

            ox = (self.screen.get_width() - self.stats_surface_cache.get_width()) // 2
            oy = (self.screen.get_height() - self.stats_surface_cache.get_height()) // 2
            self.screen.blit(self.stats_surface_cache, (ox, oy))

        self.draw_controls_overlay()

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
