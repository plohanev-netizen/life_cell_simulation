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
COLOR_GREEN = (60, 220, 60)

# --- ПЛОТНОСТЬ (в %), одинаковая для обеих сторон ---
DENSITY_PERCENT = 40  # 5..99

# --- АКТИВНОСТЬ -> ВЗРЫВ ---
ACTIVITY_TRIGGER_PERCENT = 0.05
ACTIVITY_PATIENCE = 1
MIN_GENS_BETWEEN_BANGS = 30

# Сценарии взрыва затухания
BIG_BANG_PROB_CENTER = 0.5
BIG_BANG_FRACTION_OF_GRID = 0.33
BIG_BANG_FILL_DENSITY = 0.45
SMALL_BANG_COUNT_MIN = 6
SMALL_BANG_COUNT_MAX = 12
SMALL_BANG_RADIUS_MIN = 40
SMALL_BANG_RADIUS_MAX = 90
SMALL_BANG_RADIUS_MAX_FRAC_OF_MINOR = 0.30
SMALL_BANG_FILL_DENSITY = 0.45
SMALL_BANG_MAX_OVERLAP_FRAC = 0.20
SMALL_BANG_PLACE_TRIES = 250

# Детектор циклов
OSC_MAX_PERIOD = 4

# Лог-файл
LOG_FILE = "life_stats.log"

# Реал-тайм matplotlib
MPL_UPDATE_INTERVAL = 0.10

# ----------------------------
# "рейдерский удар" (оптимизировано)
# ----------------------------
ENABLE_RAIDER_STRIKE_DEFAULT = True

RAIDER_MAX_GROUP_SIZE = 8

RAIDER_ISOLATION_RADIUS = 30      # "нет клеток своего цвета" вокруг группы
RAIDER_ENEMY_RADIUS = 40          # "в радиусе 40" врагов > 20
RAIDER_ENEMY_MIN_COUNT = 20
RAIDER_EXPLOSION_RADIUS = 20

RAIDER_PROBABILITY = 0.25

# ОПТИМИЗАЦИИ:
RAIDER_CHECK_EVERY_N = 2          # проверять рейдеров раз в N поколений
RAIDER_MAX_GROUPS_PER_GEN = 120   # максимум групп за поколение (защита FPS)

# УСИЛЕНИЕ/ДЕБАГ рейдеров
RAIDER_ISO_EXTRA_ALLOW = 2       # допускаем до N "своих" лишних клеток в зоне изоляции (делает срабатывание в куче чаще)
RAIDER_PROB_SCALE_PER_ENEMY = 0.015  # добавка к вероятности за каждого врага сверх минимума
RAIDER_MAX_PROBABILITY = 0.95

RAIDER_STRIKE_FILL_DENSITY = 0.78  # плотность заполнения при взрыве рейдера (чтобы не 'пустело' на следующем поколении)

RAIDER_DEBUG_DEFAULT = False
RAIDER_DEBUG_POINT_LIFETIME = 0.35   # секунд
RAIDER_DEBUG_MAX_POINTS = 300


# =========================
# VIRUS & SANITARIANS (BIOHAZARD) PARAMETERS
# =========================
# Важно: санитары будут включаться/выключаться вместе с вирусами (пока санитары не реализованы)
BIOHAZARD_ENABLED_DEFAULT = True

VIRUS_STATE = 3

# Окно первой волны спавна "групп вирусов" (по поколениям симуляции)
VIRUS_GROUP_SPAWN_WINDOW_START = 300
VIRUS_GROUP_SPAWN_WINDOW_END = 500

# Группы: 2–3 группы, в каждой 10–30 клеток (рандом)
VIRUS_GROUPS_MIN = 4
VIRUS_GROUPS_MAX = 10
VIRUS_GROUP_SIZE_MIN = 20
VIRUS_GROUP_SIZE_MAX = 50

# Срок жизни вирусов: глобально для всех зелёных (от первого появления)
VIRUS_GLOBAL_LIFETIME_GENS = 1500

# Если вирусная клетка не менялась более N ходов — исчезает
VIRUS_STAGNATION_GENS = 200

# Вирусы могут появляться при взрыве (большой взрыв или удар райдера),
# но только если на поле нет вирусов и если разрешено по кулдауну.
VIRUS_SPAWN_ON_BANG_PROB = 0.35
VIRUS_SPAWN_ON_BANG_CELLS_MIN = 8
VIRUS_SPAWN_ON_BANG_CELLS_MAX = 40

# Повторное появление: не ранее чем через N поколений после полного исчезновения вирусов
VIRUS_RESPAWN_COOLDOWN_GENS = 400



# Важно: санитары будут включаться/выключаться вместе с вирусами (пока санитары не реализованы)
BIOHAZARD_ENABLED_DEFAULT = True

VIRUS_STATE = 3

# Окно первой волны спавна "групп вирусов" (по поколениям симуляции)
VIRUS_GROUP_SPAWN_WINDOW_START = 500
VIRUS_GROUP_SPAWN_WINDOW_END = 700

# Группы: 2–3 группы, в каждой 10–30 клеток (рандом)
VIRUS_GROUPS_MIN = 10
VIRUS_GROUPS_MAX = 40
VIRUS_GROUP_SIZE_MIN = 1000
VIRUS_GROUP_SIZE_MAX = 5000

# Срок жизни вирусов: глобально для всех зелёных (от первого появления)
VIRUS_GLOBAL_LIFETIME_GENS = 800

# Если вирусная клетка не менялась более N ходов — исчезает
VIRUS_STAGNATION_GENS = 100

# Вирусы могут появляться при взрыве (большой взрыв или удар райдера),
# но только если на поле нет вирусов и если разрешено по кулдауну.
VIRUS_SPAWN_ON_BANG_PROB = 0.35
VIRUS_SPAWN_ON_BANG_CELLS_MIN = 8
VIRUS_SPAWN_ON_BANG_CELLS_MAX = 40

# Повторное появление: не ранее чем через N поколений после полного исчезновения вирусов
VIRUS_RESPAWN_COOLDOWN_GENS = 400


# ----------------------------
# Клик ставит группу из 4 клеток
# ----------------------------
PAINT_GROUP_SIZE = 4
PAINT_GROUP_MAX_TRIES = 40


def make_disk_offsets(radius: int):
    r = int(radius)
    yy, xx = np.ogrid[-r:r + 1, -r:r + 1]
    disk = (xx * xx + yy * yy) <= (r * r)
    dy, dx = np.where(disk)
    dy = dy - r
    dx = dx - r
    return dy.astype(np.int32), dx.astype(np.int32)


# end make_disk_offsets
def prefix_sum(mask_u8: np.ndarray) -> np.ndarray:
    ps = np.zeros((mask_u8.shape[0] + 1, mask_u8.shape[1] + 1), dtype=np.int32)
    ps[1:, 1:] = np.cumsum(np.cumsum(mask_u8, axis=0), axis=1)
    return ps


# end prefix_sum
def rect_sum(ps: np.ndarray, y0: int, x0: int, y1: int, x1: int) -> int:
    return int(ps[y1, x1] - ps[y0, x1] - ps[y1, x0] + ps[y0, x0])


# end rect_sum
def window_sum_map(ps: np.ndarray, r: int) -> np.ndarray:
    """
    Карта сумм в квадратном окне радиуса r (2r+1)x(2r+1) для каждой клетки.
    (Квадратная аппроксимация радиуса ради скорости.)
    """
    H = ps.shape[0] - 1
    W = ps.shape[1] - 1

    ys = np.arange(H, dtype=np.int32)
    xs = np.arange(W, dtype=np.int32)

    y0 = np.clip(ys - r, 0, H)
    y1 = np.clip(ys + r + 1, 0, H)
    x0 = np.clip(xs - r, 0, W)
    x1 = np.clip(xs + r + 1, 0, W)

    A = ps[y1[:, None], x1[None, :]]
    B = ps[y0[:, None], x1[None, :]]
    C = ps[y1[:, None], x0[None, :]]
    D = ps[y0[:, None], x0[None, :]]
    return (A - B - C + D)


# end window_sum_map
class StatsRecorder:
    def __init__(self):
        self.reset()

    # end __init__
    def reset(self):
        self.gen = []
        self.alive_total = []
        self.alive_red = []
        self.alive_white = []
        self.alive_virus = []
        self.active_total = []
        self.active_red = []
        self.active_white = []
        self.active_virus = []

    # end reset
    def append(self, gen, alive_total, alive_red, alive_white, alive_virus, active_total, active_red, active_white, active_virus):
        self.gen.append(int(gen))
        self.alive_total.append(int(alive_total))
        self.alive_red.append(int(alive_red))
        self.alive_white.append(int(alive_white))
        self.alive_virus.append(int(alive_virus))
        self.active_total.append(int(active_total))
        self.active_red.append(int(active_red))
        self.active_white.append(int(active_white))
        self.active_virus.append(int(active_virus))

    # end append
    def has_data(self):
        return len(self.gen) > 1

    # end has_data
    def _downsample(self, x, y, max_points):
        n = len(x)
        if n <= max_points:
            return x, y
        idx = np.linspace(0, n - 1, max_points).astype(np.int32)
        return [x[i] for i in idx], [y[i] for i in idx]

    # end _downsample
    def _render_chart(self, w, h, title, x, series, font, small_font):
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 220))

        pad = 55
        left = pad
        top = pad
        right = w - pad
        bottom = h - pad

        pygame.draw.rect(surf, (200, 200, 200, 255), (left, top, right - left, bottom - top), 2)

        if len(x) < 2:
            txt = font.render("No data yet", True, (255, 255, 255))
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
            if yd:
                y_max = max(y_max, max(yd))

        pygame.draw.line(surf, (200, 200, 200), (left, bottom), (right, bottom), 2)
        pygame.draw.line(surf, (200, 200, 200), (left, top), (left, bottom), 2)

        surf.blit(small_font.render("Generations (X)", True, (230, 230, 230)), (left + 10, bottom + 10))
        surf.blit(small_font.render("Count (Y)", True, (230, 230, 230)), (10, top - 28))

        ticks = 5
        for i in range(ticks + 1):
            ty = top + int((bottom - top) * (i / ticks))
            val = int(y_max * (1 - i / ticks))
            pygame.draw.line(surf, (120, 120, 120), (left - 6, ty), (left, ty), 2)
            lab = small_font.render(str(val), True, (200, 200, 200))
            surf.blit(lab, (left - 12 - lab.get_width(), ty - lab.get_height() // 2))

        def to_px(gx, gy):
            px = left + int((gx - x_min) / (x_max - x_min) * (right - left))
            py = top + int((1 - (gy / y_max if y_max else 0)) * (bottom - top))
            return px, py

        for name, xd, yd, col in down:
            pts = [to_px(gx, gy) for gx, gy in zip(xd, yd)]
            if len(pts) >= 2:
                pygame.draw.lines(surf, col, False, pts, 2)

        lx = right - 240
        ly = top + 10
        for name, _, __, col in down:
            pygame.draw.rect(surf, col, (lx, ly + 5, 18, 10))
            surf.blit(small_font.render(name, True, (240, 240, 240)), (lx + 28, ly))
            ly += 18

        surf.blit(font.render(title, True, (255, 255, 255)), (left, 14))
        return surf

    # end _render_chart
    def render_population_and_activity(self, w, h, font, small_font):
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 220))
        pygame.draw.rect(surf, (220, 220, 220, 255), (0, 0, w, h), 2)

        header = font.render("Statistics (real-time). T: overlay | G: matplotlib window", True, (255, 255, 255))
        surf.blit(header, (18, 14))

        if not self.has_data():
            txt = font.render("No stats yet", True, (255, 255, 255))
            surf.blit(txt, (18, 60))
            return surf

        gap = 14
        top_pad = 46
        chart_h = (h - top_pad - gap - 18) // 2
        chart_w = w - 18 * 2
        x = self.gen

        pop_series = [
            ("Alive Total", self.alive_total, (230, 230, 230)),
            ("Alive Red", self.alive_red, (255, 80, 80)),
            ("Alive White", self.alive_white, (200, 200, 255)),
            ("Alive Virus", self.alive_virus, (120, 255, 120)),
        ]
        act_series = [
            ("Active Total", self.active_total, (255, 220, 120)),
            ("Active Red", self.active_red, (255, 140, 120)),
            ("Active White", self.active_white, (180, 255, 255)),
            ("Active Virus", self.active_virus, (140, 255, 140)),
        ]

        pop_s = self._render_chart(chart_w, chart_h, "Population", x, pop_series, font, small_font)
        act_s = self._render_chart(chart_w, chart_h, "Activity", x, act_series, font, small_font)

        surf.blit(pop_s, (18, top_pad))
        surf.blit(act_s, (18, top_pad + chart_h + gap))
        return surf


    # end render_population_and_activity
class LiveMatplotlibStats:
    def __init__(self, update_interval=MPL_UPDATE_INTERVAL):
        self.update_interval = float(update_interval)
        self.available = None
        self.plt = None
        self.fig = None
        self.axes = None
        self.lines = {}
        self.opened = False
        self.last_update = 0.0

    # end __init__
    def _ensure_import(self):
        if self.available is False:
            return False
        if self.available is True:
            return True
        try:
            import matplotlib.pyplot as plt
            self.plt = plt
            self.available = True
            return True
        except Exception:
            self.available = False
            return False

    # end _ensure_import
    def toggle(self):
        if not self._ensure_import():
            return False
        if self.opened:
            self.close()
            return True
        self.open()
        return True

    # end toggle
    def open(self):
        if not self._ensure_import():
            return False
        if self.opened:
            return True

        plt = self.plt
        plt.ion()
        self.fig, ax = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
        self.axes = ax
        try:
            self.fig.canvas.manager.set_window_title("Game of Life Stats (Live)")
        except Exception:
            pass

        ax[0].set_title("Population")
        ax[0].set_ylabel("Count")
        l1, = ax[0].plot([], [], label="Alive Total")
        l2, = ax[0].plot([], [], label="Alive Red")
        l3, = ax[0].plot([], [], label="Alive White")
        l7, = ax[0].plot([], [], label="Alive Virus")
        ax[0].legend(loc="upper right")

        ax[1].set_title("Activity")
        ax[1].set_xlabel("Generation")
        ax[1].set_ylabel("Count")
        l4, = ax[1].plot([], [], label="Active Total")
        l5, = ax[1].plot([], [], label="Active Red")
        l6, = ax[1].plot([], [], label="Active White")
        l8, = ax[1].plot([], [], label="Active Virus")
        ax[1].legend(loc="upper right")

        self.lines = {
            "alive_total": l1,
            "alive_red": l2,
            "alive_white": l3,
            "alive_virus": l7,
            "active_total": l4,
            "active_red": l5,
            "active_white": l6,
            "active_virus": l8,
        }

        def _on_close(_evt):
            self.opened = False
            self.fig = None
            self.axes = None
            self.lines = {}

        self.fig.canvas.mpl_connect("close_event", _on_close)
        plt.tight_layout()
        plt.show(block=False)

        self.opened = True
        self.last_update = 0.0
        return True

    # end open
    def close(self):
        if not self.opened:
            return
        try:
            self.plt.close(self.fig)
        except Exception:
            pass
        self.opened = False
        self.fig = None
        self.axes = None
        self.lines = {}

    # end close
    def update(self, stats: StatsRecorder):
        if not self.opened or not stats.has_data():
            return
        now = time.time()
        if (now - self.last_update) < self.update_interval:
            return
        self.last_update = now

        x = np.array(stats.gen)
        self.lines["alive_total"].set_data(x, np.array(stats.alive_total))
        self.lines["alive_red"].set_data(x, np.array(stats.alive_red))
        self.lines["alive_white"].set_data(x, np.array(stats.alive_white))
        self.lines["alive_virus"].set_data(x, np.array(stats.alive_virus))
        self.lines["active_total"].set_data(x, np.array(stats.active_total))
        self.lines["active_red"].set_data(x, np.array(stats.active_red))
        self.lines["active_white"].set_data(x, np.array(stats.active_white))
        self.lines["active_virus"].set_data(x, np.array(stats.active_virus))

        for a in self.axes:
            a.relim()
            a.autoscale_view()
        try:
            self.fig.canvas.draw_idle()
            self.fig.canvas.flush_events()
        except Exception:
            pass


    # end update
class ManualBlast:
    def __init__(self, hold_seconds=0.5, radius_cells=40):
        self.hold_seconds = float(hold_seconds)
        self.radius_cells = int(radius_cells)
        self.holding = False
        self.triggered = False
        self.start_time = 0.0

    # end __init__
    def start_hold(self):
        self.holding = True
        self.triggered = False
        self.start_time = time.time()

    # end start_hold
    def stop_hold(self):
        self.holding = False
        self.triggered = False
        self.start_time = 0.0

    # end stop_hold
    def hold_duration(self):
        if not self.holding:
            return 0.0
        return time.time() - self.start_time

    # end hold_duration
    def should_trigger(self):
        if not self.holding or self.triggered:
            return False
        return self.hold_duration() >= self.hold_seconds

    # end should_trigger
    def mark_triggered(self):
        self.triggered = True


    # end mark_triggered
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

        # 0=dead, 1=white, 2=red, 3=virus
        self.grid = np.zeros((self.rows, self.cols), dtype=np.uint8)

        self.running = True
        self.paused = True
        self.speed = 15
        self.last_update_time = time.time()

        self.generation = 0
        self.gen_since_bang = 0
        self.explosions = 0
        self.manual_explosions = 0
        self.raider_explosions = 0
        self.last_explosion_gen = 0  # any explosion (big/raider/manual)


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
        self.palette = np.array([COLOR_BG, COLOR_WHITE, COLOR_RED, COLOR_GREEN], dtype=np.uint8)

        # стартовый разделитель (только для инициализации)
        self.center_x = self.cols // 2
        base_sep = max(15, int(self.cols * 0.20))
        narrowed = max(15, int(round(base_sep * (2.0 / 3.0))))
        self.separator_width = narrowed
        self.sep_left = self.center_x - self.separator_width // 2
        self.sep_right = self.center_x + self.separator_width // 2

        # view transform (показать поле целиком)
        self.view_scale = 1.0
        self.view_rect = pygame.Rect(0, 0, 1, 1)
        self._update_view_transform()

        # manual blast (long-press)
        self.manual_blast = ManualBlast(hold_seconds=0.5, radius_cells=40)

        # stats + live mpl
        self.stats = StatsRecorder()
        self.show_stats = False
        self.stats_surface_cache = None
        self.stats_cache_gen = -1
        self.mpl_live = LiveMatplotlibStats(update_interval=MPL_UPDATE_INTERVAL)

        # controls overlay
        self.controls_toggle = False
        self.controls_start_until = time.time() + 3.0
        self.controls_rect = None

        # Biohazard (viruses + future sanitarians) toggle
        self.biohazard_enabled = bool(BIOHAZARD_ENABLED_DEFAULT)

        # Virus state bookkeeping
        self.virus_epoch_start_gen = None  # generation when first virus appeared in current epoch
        self.last_virus_end_gen = -1_000_000_000    # generation when viruses fully disappeared last time
        self.virus_groups_spawn_gen = None  # planned generation for group spawn
        self.virus_groups_spawned_or_canceled = False
        self.virus_last_change_gen = np.full((self.rows, self.cols), -10**9, dtype=np.int32)

        # Spontaneous respawn after cooldown: require 100 gens without any explosion after VirusIn hits 0
        self.virus_quiet_start_gen = None
        self.virus_quiet_deadline_gen = None
        self.virus_quiet_blocked = False
        # Virus counters
        self.virus_spawns = 0
        self.virus_infections = 0
        self.virus_expire_global = 0
        self.virus_expire_stagnation = 0

        # Raider strike toggle
        self.enable_raider_strike = bool(ENABLE_RAIDER_STRIKE_DEFAULT)

        # Raider debug overlay toggle (Y)
        self.raider_debug = bool(RAIDER_DEBUG_DEFAULT)
        self._raider_dbg_points = []  # list of (t_expire, kind, gy, gx)
        self._raider_dbg_counts = None

        # cache offsets for explosion radius (disk)
        self._disk20 = make_disk_offsets(RAIDER_EXPLOSION_RADIUS)

        # планируем спавн групп вирусов (первая волна)
        self._plan_virus_groups_spawn()

        # init
        self.validate_and_initialize_by_density()
        self.log_event("START", extra=f"density={self.density_percent}% grid={self.rows}x{self.cols} scale={self.scale} sep={self.separator_width} fullscreen={self.fullscreen} raider={self.enable_raider_strike}")

    # ----------------------------
    # Display / Scaling
    # ----------------------------
    # end __init__
    def _create_display(self):
        flags_window = pygame.SCALED | pygame.RESIZABLE
        flags_full = pygame.FULLSCREEN | pygame.SCALED
        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), flags_full)
        else:
            di = pygame.display.Info()
            w = min(self.window_w, di.current_w)
            h = min(self.window_h, di.current_h)
            self.screen = pygame.display.set_mode((w, h), flags_window)
            self.window_w, self.window_h = w, h

    # end _create_display
    def _toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self._create_display()
        self._update_view_transform()
        self._invalidate_stats_cache()

    # end _toggle_fullscreen
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

    # end _update_view_transform
    def _screen_to_grid(self, x, y):
        if not self.view_rect.collidepoint(x, y):
            return None
        gx = int((x - self.view_rect.x) / self.view_scale)
        gy = int((y - self.view_rect.y) / self.view_scale)
        if 0 <= gx < self.cols and 0 <= gy < self.rows:
            return gx, gy
        return None

    # end _screen_to_grid
    def _invalidate_stats_cache(self):
        self.stats_surface_cache = None
        self.stats_cache_gen = -1

    # ----------------------------
    # Logging
    # ----------------------------
    # end _invalidate_stats_cache
    def log_event(self, event, extra=""):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        w = int(np.sum(self.grid == 1))
        r = int(np.sum(self.grid == 2))
        line = (
            f"[{ts}] {event} | gen={self.generation} gen_since_bang={self.gen_since_bang} "
            f"explosions={self.explosions} manual_explosions={self.manual_explosions} raider_explosions={self.raider_explosions} "
            f"white={w} red={r} "
            f"act_total={self.activity_total:.4f}% act_w={self.activity_white:.4f}% act_r={self.activity_red:.4f}% "
            f"osc={self.oscillating_percent:.4f}% raider_enabled={self.enable_raider_strike}"
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
    # end log_event
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

    # end validate_and_initialize_by_density
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

        self._append_stats_point(active_total=0, active_red=0, active_white=0, active_virus=0)
        self.controls_start_until = time.time() + 3.0
        self.mpl_live.update(self.stats)

    # end randomize_grid
    def _append_stats_point(self, active_total, active_red, active_white, active_virus):
        alive_white = int(np.sum(self.grid == 1))
        alive_red = int(np.sum(self.grid == 2))
        alive_virus = int(np.sum(self.grid == 3))
        alive_total = alive_white + alive_red + alive_virus
        self.stats.append(
            gen=self.generation,
            alive_total=alive_total,
            alive_red=alive_red,
            alive_white=alive_white,
            alive_virus=alive_virus,
            active_total=active_total,
            active_red=active_red,
            active_white=active_white,
            active_virus=active_virus,
        )

    # ----------------------------
    # Neighbors
    # ----------------------------
    # end _append_stats_point
    def count_neighbors_vectorized(self, grid_mask_bool):
        grid = grid_mask_bool.astype(np.uint8)
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
    # end count_neighbors_vectorized
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

    # end compute_oscillating_mask
    
    def compute_activity(self, old_grid, new_grid):
        total_cells = old_grid.size
        changed = (new_grid != old_grid)

        osc_mask = self.compute_oscillating_mask(old_grid, new_grid)
        changed_no_osc = changed & (~osc_mask)

        active_total_count = int(np.sum(changed_no_osc))

        active_white_count = int(np.sum(changed_no_osc & ((old_grid == 1) | (new_grid == 1))))
        active_red_count = int(np.sum(changed_no_osc & ((old_grid == 2) | (new_grid == 2))))
        active_virus_count = int(np.sum(changed_no_osc & ((old_grid == 3) | (new_grid == 3))))

        act_total = 100.0 * active_total_count / float(total_cells)
        act_white = 100.0 * active_white_count / float(total_cells)
        act_red = 100.0 * active_red_count / float(total_cells)
        act_virus = 100.0 * active_virus_count / float(total_cells)

        osc_percent = 100.0 * int(np.sum(osc_mask)) / float(total_cells)

        return (act_total, act_white, act_red, act_virus, osc_percent,
                active_total_count, active_white_count, active_red_count, active_virus_count)

    # end compute_activity

    def _apply_circle_fill_color(self, grid, cy, cx, radius, color_state, fill_density: float = 1.0):
        """Заполнить круг радиуса `radius` вокруг (cy,cx) клетками `color_state`.

        Если fill_density < 1.0, то внутри круга клетки ставятся случайно с данной плотностью,
        а остальные очищаются (0). Это важно для "взрыва рейдера": сплошной диск в Life часто
        вымирает на следующем поколении и визуально выглядит как "зачистка без своих".
        """
        dy, dx = self._disk20 if radius == RAIDER_EXPLOSION_RADIUS else make_disk_offsets(radius)
        ys = cy + dy
        xs = cx + dx
        inside = (ys >= 0) & (ys < self.rows) & (xs >= 0) & (xs < self.cols)
        ys = ys[inside]
        xs = xs[inside]

        if fill_density >= 0.999:
            grid[ys, xs] = color_state
            return

        # Сначала очищаем область, затем ставим своих с нужной плотностью
        grid[ys, xs] = 0
        cap = ys.size
        if cap <= 0:
            return

        k = int(cap * float(fill_density))
        if k <= 0:
            return

        chosen = np.random.choice(cap, size=k, replace=False)
        grid[ys[chosen], xs[chosen]] = color_state
    
    def _apply_ball_single_color(self, grid, cy, cx, r, fill_density: float, color_state: int):
        """Заполнить круг как в больших взрывах (случайная выборка с плотностью + минимум),
        но цвет всегда один (color_state).

        Алгоритм:
        - очищаем область круга (ставим 0)
        - выбираем k = max(int(cap*fill_density), 200), но не больше cap
        - ставим выбранные клетки в color_state
        """
        if r <= 1:
            return 0, 0

        # Быстрый путь для стандартного радиуса рейдера
        if r == RAIDER_EXPLOSION_RADIUS:
            dy, dx = self._disk20
            ys = cy + dy
            xs = cx + dx
        else:
            dy, dx = make_disk_offsets(r)
            ys = cy + dy
            xs = cx + dx

        inside = (ys >= 0) & (ys < self.rows) & (xs >= 0) & (xs < self.cols)
        ys = ys[inside].astype(np.int32)
        xs = xs[inside].astype(np.int32)

        cap = int(ys.size)
        if cap <= 0:
            return 0, 0

        # очистить область
        grid[ys, xs] = 0

        k = int(cap * float(fill_density))
        k = max(k, 200)
        k = min(k, cap)
        if k <= 0:
            return cap, 0

        chosen_idx = np.random.choice(cap, size=k, replace=False)
        grid[ys[chosen_idx], xs[chosen_idx]] = color_state
        return cap, k

    # end _apply_ball_single_color
# ----------------------------
    # Big bang helpers
    # ----------------------------
    # end _apply_circle_fill_color
    def _apply_ball(self, cy, cx, r, fill_density):
        if r <= 1:
            return 0, 0
        yy, xx = np.ogrid[-r:r + 1, -r:r + 1]
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

        # очистить область
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

    # end _apply_ball
    def _big_center_bang(self):
        total_cells = self.rows * self.cols
        target_area = int(total_cells * float(BIG_BANG_FRACTION_OF_GRID))
        r_from_area = int(np.sqrt(target_area / np.pi))
        r_min = int(min(self.rows, self.cols) / 3)
        r = max(r_from_area, r_min)
        r = min(r, (min(self.rows, self.cols) // 2) - 2)
        cy, cx = self.rows // 2, self.cols // 2
        cap, k = self._apply_ball(cy, cx, r, BIG_BANG_FILL_DENSITY)
        self._maybe_spawn_viruses_from_bang(cx, cy, r)
        return {"scenario": "center", "balls": 1, "r": r, "cap": cap, "k": k, "centers": [(cy, cx, r)]}

    # end _big_center_bang
    def _multi_small_bang(self):
        balls_target = int(np.random.randint(SMALL_BANG_COUNT_MIN, SMALL_BANG_COUNT_MAX + 1))

        minor = min(self.rows, self.cols)
        r_cap = int(minor * SMALL_BANG_RADIUS_MAX_FRAC_OF_MINOR)
        r_hi = min(SMALL_BANG_RADIUS_MAX, r_cap)
        r_lo = min(SMALL_BANG_RADIUS_MIN, r_hi)
        if r_hi < 5:
            return {"scenario": "multi", "balls": 0, "r_min": 0, "r_max": 0, "sum_k": 0}

        placed = []
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
                    self._maybe_spawn_viruses_from_bang(cx, cy, r)
                    sum_k += k
                    success = True
                    break
            if not success:
                continue

        if r_min_used == 10**9:
            r_min_used = 0

        return {"scenario": "multi", "balls": len(placed), "r_min": r_min_used, "r_max": r_max_used, "sum_k": sum_k, "centers": [(py, px, pr) for (py, px, pr) in placed]}

    # end _multi_small_bang
    def big_bang(self):
        info = self._big_center_bang() if (np.random.random() < BIG_BANG_PROB_CENTER) else self._multi_small_bang()
        self.explosions += 1
        self.log_event("BIG_BANG", extra=str(info))
        self.gen_since_bang = 0
        self.last_explosion_gen = int(self.generation)
        self.low_activity_streak = 0
        self.history.clear()

    # ----------------------------
    # Manual blast
    # ----------------------------
    # end big_bang
    def manual_boom_at(self, gx, gy):
        r = self.manual_blast.radius_cells
        cap, k = self._apply_ball(gy, gx, r, fill_density=0.45)
        self.manual_explosions += 1
        self.log_event("MANUAL_BANG", extra=f"center=({gx},{gy}) r={r} cap={cap} k={k}")
        self.last_explosion_gen = int(self.generation)
        self.history.clear()

    # ----------------------------
    # NEW Raiders (без требования "переноса", чтобы работало в куче)
    # ----------------------------
    # end manual_boom_at
    def _apply_raider_strikes(self, old_grid, new_grid):
        if not self.enable_raider_strike:
            return
        if RAIDER_CHECK_EVERY_N > 1 and (self.generation % RAIDER_CHECK_EVERY_N) != 0:
            return

        # маски на new_grid (после обычных правил)
        new_white = (new_grid == 1).astype(np.uint8)
        new_red = (new_grid == 2).astype(np.uint8)

        ps_new_white = prefix_sum(new_white)
        ps_new_red = prefix_sum(new_red)

        # изоляция (радиус 30, квадрат)
        iso_r = RAIDER_ISOLATION_RADIUS
        win_white_iso = window_sum_map(ps_new_white, iso_r)
        win_red_iso = window_sum_map(ps_new_red, iso_r)

        # враги в радиусе 40 (квадрат)
        rE = RAIDER_ENEMY_RADIUS
        win_red_enemy40 = window_sum_map(ps_new_red, rE)      # враги для белых
        win_white_enemy40 = window_sum_map(ps_new_white, rE)  # враги для красных

        processed_groups = 0

        # debug counters (минимальный оверхед)
        dbg = {
            'candidates': 0,
            'bfs_ok': 0,
            'iso_ok': 0,
            'contact_ok': 0,
            'enemy_ok': 0,
            'prob_ok': 0,
            'exploded': 0,
        }
        now_t = time.time()
        if self.raider_debug:
            # чистим протухшие точки
            self._raider_dbg_points = [p for p in self._raider_dbg_points if p[0] > now_t]

        for color_state, enemy_state, self_mask_u8, win_iso, win_enemy40 in (
            (1, 2, new_white, win_white_iso, win_red_enemy40),
            (2, 1, new_red,   win_red_iso,   win_white_enemy40),
        ):
            if processed_groups >= RAIDER_MAX_GROUPS_PER_GEN:
                break

            self_mask = (self_mask_u8 == 1)
            enemy_mask = (new_grid == enemy_state)

            # есть ли рядом враг (8-соседи)
            enemy_neighbors = (self.count_neighbors_vectorized(enemy_mask) > 0)

            # кандидаты
            candidates = (
                self_mask
                & (win_iso <= (RAIDER_MAX_GROUP_SIZE + RAIDER_ISO_EXTRA_ALLOW))
                & enemy_neighbors
                & (win_enemy40 > RAIDER_ENEMY_MIN_COUNT)
            )

            cy, cx = np.where(candidates)
            if cy.size == 0:
                continue

            dbg['candidates'] += int(cy.size)
            if self.raider_debug:
                # показываем небольшую выборку кандидатов
                sample_n = int(min(40, cy.size))
                if sample_n > 0:
                    si = np.random.choice(cy.size, size=sample_n, replace=False)
                    exp = now_t + RAIDER_DEBUG_POINT_LIFETIME
                    for yy, xx in zip(cy[si], cx[si]):
                        self._raider_dbg_points.append((exp, 'cand', int(yy), int(xx)))

            # рандомизируем
            idx = np.random.permutation(cy.size)
            cy = cy[idx]
            cx = cx[idx]

            visited = np.zeros((self.rows, self.cols), dtype=bool)

            for sy, sx in zip(cy, cx):
                if processed_groups >= RAIDER_MAX_GROUPS_PER_GEN:
                    break
                if visited[sy, sx]:
                    continue
                if new_grid[sy, sx] != color_state:
                    continue

                # BFS 8-связность, лимит 8
                stack = [(int(sy), int(sx))]
                visited[sy, sx] = True
                comp = []

                while stack:
                    y, x = stack.pop()
                    comp.append((y, x))
                    if len(comp) > RAIDER_MAX_GROUP_SIZE:
                        comp = None
                        break
                    for dy in (-1, 0, 1):
                        ny = y + dy
                        if ny < 0 or ny >= self.rows:
                            continue
                        for dx in (-1, 0, 1):
                            if dy == 0 and dx == 0:
                                continue
                            nx = x + dx
                            if nx < 0 or nx >= self.cols:
                                continue
                            if (not visited[ny, nx]) and (new_grid[ny, nx] == color_state):
                                visited[ny, nx] = True
                                stack.append((ny, nx))

                if comp is None:
                    continue

                dbg['bfs_ok'] += 1

                # Условие 2: в радиусе 30 от границ группы нет других клеток этого цвета
                ys = [p[0] for p in comp]
                xs = [p[1] for p in comp]
                y0 = max(0, min(ys) - iso_r)
                y1 = min(self.rows, max(ys) + iso_r + 1)
                x0 = max(0, min(xs) - iso_r)
                x1 = min(self.cols, max(xs) + iso_r + 1)

                ps_self = ps_new_white if color_state == 1 else ps_new_red
                total_same = rect_sum(ps_self, y0, x0, y1, x1)
                # допускаем немного "своих" рядом, чтобы срабатывало глубже в куче врагов
                iso_allow = RAIDER_ISO_EXTRA_ALLOW
                if total_same > (len(comp) + iso_allow):
                    continue

                dbg['iso_ok'] += 1

                # Условие 3а: контакт с врагом (в 8-соседстве от компоненты)
                has_contact = False
                for (y, x) in comp:
                    yb0 = max(0, y - 1); yb1 = min(self.rows, y + 2)
                    xb0 = max(0, x - 1); xb1 = min(self.cols, x + 2)
                    if np.any(new_grid[yb0:yb1, xb0:xb1] == enemy_state):
                        has_contact = True
                        break
                if not has_contact:
                    continue

                dbg['contact_ok'] += 1

                # Условие 3б: врагов много в радиусе 40
                cy0 = int(round(np.mean(ys)))
                cx0 = int(round(np.mean(xs)))
                enemy_cnt = int(win_enemy40[cy0, cx0])
                if enemy_cnt <= RAIDER_ENEMY_MIN_COUNT:
                    continue

                dbg['enemy_ok'] += 1

                # Условие 4: вероятность (масштабируем по плотности врага)
                p = RAIDER_PROBABILITY * (1.0 + RAIDER_PROB_SCALE_PER_ENEMY * max(0, enemy_cnt - RAIDER_ENEMY_MIN_COUNT))
                if p > RAIDER_MAX_PROBABILITY:
                    p = RAIDER_MAX_PROBABILITY
                if np.random.random() >= p:
                    continue

                dbg['prob_ok'] += 1

                # Взрыв радиус 20 — заполняем своим цветом (уничтожая другой)
                self._apply_ball_single_color(new_grid, cy0, cx0, RAIDER_EXPLOSION_RADIUS, fill_density=RAIDER_STRIKE_FILL_DENSITY, color_state=color_state)
                self._maybe_spawn_viruses_from_bang(cx0, cy0, RAIDER_EXPLOSION_RADIUS, grid_target=new_grid)

                # Virus spawn on raider strike (if eligible)
                self._maybe_spawn_viruses_from_bang(cx0, cy0, RAIDER_EXPLOSION_RADIUS, grid_target=new_grid)

                dbg['exploded'] += 1
                if self.raider_debug:
                    exp = now_t + RAIDER_DEBUG_POINT_LIFETIME
                    self._raider_dbg_points.append((exp, 'boom', int(cy0), int(cx0)))

                processed_groups += 1
                self.raider_explosions += 1
                self.last_explosion_gen = int(self.generation)
                self.log_event(
                    "RAIDER_STRIKE",
                    extra=f"color={color_state} center=({cx0},{cy0}) enemyWin40={enemy_cnt} comp={len(comp)}"
                )

        if self.raider_debug:
            self._raider_dbg_counts = dbg


    # ----------------------------
    # Connected group of 4 (8-связность)
    # ----------------------------
    # end _apply_raider_strikes

    # ----------------------------
    # Viruses (BIOHAZARD)
    # ----------------------------
    def _can_spawn_viruses_now(self, grid_view=None):
        """Check global conditions: biohazard enabled, no current viruses, cooldown passed, and generation >= start."""
        if not self.biohazard_enabled:
            return False
        gv = self.grid if grid_view is None else grid_view
        if np.any(gv == VIRUS_STATE):
            return False
        if int(self.generation) < int(VIRUS_GROUP_SPAWN_WINDOW_START):
            return False
        if (int(self.generation) - int(self.last_virus_end_gen)) < int(VIRUS_RESPAWN_COOLDOWN_GENS):
            return False
        return True
    # end _can_spawn_viruses_now

    def _plan_virus_groups_spawn(self):
        """Plan the first-wave group spawn generation within configured window."""
        self.virus_groups_spawn_gen = int(np.random.randint(VIRUS_GROUP_SPAWN_WINDOW_START, VIRUS_GROUP_SPAWN_WINDOW_END + 1))
        self.virus_groups_spawned_or_canceled = False
    # end _plan_virus_groups_spawn

    def _spawn_virus_groups(self, grid_target=None):
        """Spawn 2–3 virus groups (10–30 cells each) at random positions."""
        grid = self.grid if grid_target is None else grid_target
        groups = int(np.random.randint(VIRUS_GROUPS_MIN, VIRUS_GROUPS_MAX + 1))
        for _ in range(groups):
            size = int(np.random.randint(VIRUS_GROUP_SIZE_MIN, VIRUS_GROUP_SIZE_MAX + 1))
            cx = int(np.random.randint(0, self.cols))
            cy = int(np.random.randint(0, self.rows))
            # random-walk blob around (cx, cy)
            x, y = cx, cy
            for _k in range(size):
                if 0 <= x < self.cols and 0 <= y < self.rows:
                    grid[y, x] = VIRUS_STATE
                    self.virus_last_change_gen[y, x] = int(self.generation)
                dx = int(np.random.randint(-1, 2))
                dy = int(np.random.randint(-1, 2))
                x = int(np.clip(x + dx, 0, self.cols - 1))
                y = int(np.clip(y + dy, 0, self.rows - 1))

        self.virus_spawns += 1
        if self.virus_epoch_start_gen is None:
            self.virus_epoch_start_gen = int(self.generation)
        self.log_event("VIRUS_SPAWN", extra=f"type=groups gen={int(self.generation)}")
        # end _spawn_virus_groups

    def _maybe_spawn_viruses_from_bang(self, cx, cy, radius, grid_target=None):
        """Potentially spawn viruses inside a bang circle."""
        gt = self.grid if grid_target is None else grid_target
        if not self._can_spawn_viruses_now(grid_view=gt):
            return False
        if np.random.random() > float(VIRUS_SPAWN_ON_BANG_PROB):
            return False

        n = int(np.random.randint(VIRUS_SPAWN_ON_BANG_CELLS_MIN, VIRUS_SPAWN_ON_BANG_CELLS_MAX + 1))
        r2 = int(radius) * int(radius)
        tries = max(50, n * 6)
        placed = 0
        for _ in range(tries):
            if placed >= n:
                break
            x = int(np.random.randint(cx - radius, cx + radius + 1))
            y = int(np.random.randint(cy - radius, cy + radius + 1))
            if x < 0 or x >= self.cols or y < 0 or y >= self.rows:
                continue
            dx = x - cx
            dy = y - cy
            if (dx * dx + dy * dy) <= r2:
                gt[y, x] = VIRUS_STATE
                self.virus_last_change_gen[y, x] = int(self.generation)
                placed += 1

        if placed > 0:
            self.virus_spawns += 1
            # A bang-spawn cancels the planned first-wave groups
            self.virus_groups_spawned_or_canceled = True
            if self.virus_epoch_start_gen is None:
                self.virus_epoch_start_gen = int(self.generation)
            self.log_event("VIRUS_SPAWN", extra=f"type=bang placed={placed} gen={int(self.generation)}")
            # cancel any pending spontaneous respawn window
            self.virus_quiet_start_gen = None
            self.virus_quiet_deadline_gen = None
            self.virus_quiet_blocked = False
            return True
        return False
    # end _maybe_spawn_viruses_from_bang

    def _apply_virus_infection(self, grid_in):
        """Convert any adjacent (8-neigh) white/red cells into virus if they touch a virus cell."""
        if not self.biohazard_enabled:
            return grid_in
        if not np.any(grid_in == VIRUS_STATE):
            return grid_in

        virus = (grid_in == VIRUS_STATE)
        v = virus.astype(np.uint8)
        pad = np.pad(v, ((1, 1), (1, 1)), mode='constant', constant_values=0)
        neigh = (
            pad[0:-2, 0:-2] + pad[0:-2, 1:-1] + pad[0:-2, 2:] +
            pad[1:-1, 0:-2] + pad[1:-1, 2:] +
            pad[2:, 0:-2] + pad[2:, 1:-1] + pad[2:, 2:]
        )
        touch_virus = neigh > 0
        infect_mask = touch_virus & ((grid_in == 1) | (grid_in == 2))
        if not np.any(infect_mask):
            return grid_in

        out = grid_in.copy()
        out[infect_mask] = VIRUS_STATE
        self.virus_infections += int(np.count_nonzero(infect_mask))
        self.virus_last_change_gen[infect_mask] = int(self.generation)
        return out
    # end _apply_virus_infection

    def _postprocess_virus_lifecycle(self, old_grid, new_grid):
        """Handle: planned group spawn, per-cell stagnation expiry, global TTL expiry, and end-of-epoch bookkeeping."""
        if not self.biohazard_enabled:
            if np.any(new_grid == VIRUS_STATE):
                new_grid[new_grid == VIRUS_STATE] = 0
            self.virus_epoch_start_gen = None
            return

        gen = int(self.generation)

        # 1) Planned first-wave groups
        if (not self.virus_groups_spawned_or_canceled) and (self.virus_groups_spawn_gen is not None):
            if gen >= int(self.virus_groups_spawn_gen):
                if self._can_spawn_viruses_now():
                    self._spawn_virus_groups(grid_target=new_grid)
                    # cancel any pending spontaneous respawn window
                    self.virus_quiet_start_gen = None
                    self.virus_quiet_deadline_gen = None
                    self.virus_quiet_blocked = False
                self.virus_groups_spawned_or_canceled = True

        # 2) Global TTL expiry
        if self.virus_epoch_start_gen is not None:
            if (gen - int(self.virus_epoch_start_gen)) >= int(VIRUS_GLOBAL_LIFETIME_GENS):
                if np.any(new_grid == VIRUS_STATE):
                    cnt = int(np.count_nonzero(new_grid == VIRUS_STATE))
                    new_grid[new_grid == VIRUS_STATE] = 0
                    self.virus_expire_global += cnt
                    self.log_event("VIRUS_EXPIRE_GLOBAL", extra=f"count={cnt} gen={gen}")
                self.virus_epoch_start_gen = None
                self.last_virus_end_gen = gen
                return

        # 3) Per-cell stagnation expiry
        virus_new = (new_grid == VIRUS_STATE)
        if np.any(virus_new):
            # cancel pending spontaneous respawn window while viruses exist
            self.virus_quiet_start_gen = None
            self.virus_quiet_deadline_gen = None
            self.virus_quiet_blocked = False
            virus_old = (old_grid == VIRUS_STATE)
            unchanged = virus_new & virus_old
            changed_or_new = virus_new & (~virus_old)
            if np.any(changed_or_new):
                self.virus_last_change_gen[changed_or_new] = gen
            stale = unchanged & ((gen - self.virus_last_change_gen) >= int(VIRUS_STAGNATION_GENS))
            if np.any(stale):
                cnt = int(np.count_nonzero(stale))
                new_grid[stale] = 0
                self.virus_expire_stagnation += cnt
                self.log_event("VIRUS_EXPIRE_STAGNATION", extra=f"count={cnt} gen={gen}")

            if self.virus_epoch_start_gen is None:
                self.virus_epoch_start_gen = gen
        else:
            if self.virus_epoch_start_gen is not None or np.any(old_grid == VIRUS_STATE):
                self.virus_epoch_start_gen = None
                self.last_virus_end_gen = gen
    
        # 4) Spontaneous respawn AFTER cooldown if there were no explosions for 100 gens
        #    Trigger condition: VirusIn == 0 (cooldown passed) and still no viruses on field.
        if (not np.any(new_grid == VIRUS_STATE)) and self._can_spawn_viruses_now():
            # Start / maintain a "quiet window" after cooldown ends
            if self.virus_quiet_start_gen is None:
                self.virus_quiet_start_gen = gen
                self.virus_quiet_deadline_gen = gen + 100
                self.virus_quiet_blocked = False

            # If an explosion happens during the window -> block this attempt
            if (self.last_explosion_gen is not None) and (self.last_explosion_gen >= int(self.virus_quiet_start_gen)) and (self.last_explosion_gen < int(self.virus_quiet_deadline_gen)):
                self.virus_quiet_blocked = True

            # Deadline reached -> if no explosions, spawn scattered virus groups (can overwrite other cells)
            if gen >= int(self.virus_quiet_deadline_gen):
                if not self.virus_quiet_blocked:
                    self._spawn_virus_groups(grid_target=new_grid)
                    # Reset window after successful spawn
                    self.virus_quiet_start_gen = None
                    self.virus_quiet_deadline_gen = None
                    self.virus_quiet_blocked = False
                else:
                    # Restart window from now (rolling "100 gens of calm" requirement)
                    self.virus_quiet_start_gen = gen
                    self.virus_quiet_deadline_gen = gen + 100
                    self.virus_quiet_blocked = False
# end _postprocess_virus_lifecycle
    def _generate_connected_offsets(self, n=4):
        offsets = {(0, 0)}
        neighbors8 = [(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if not (dy == 0 and dx == 0)]
        while len(offsets) < n:
            base = list(offsets)[np.random.randint(0, len(offsets))]
            dy, dx = neighbors8[np.random.randint(0, len(neighbors8))]
            offsets.add((base[0] + dy, base[1] + dx))
        return list(offsets)

    # end _generate_connected_offsets
    def try_place_group_of_4(self, gx, gy, color_state):
        for _ in range(PAINT_GROUP_MAX_TRIES):
            offsets = self._generate_connected_offsets(PAINT_GROUP_SIZE)
            coords = [(gy + dy, gx + dx) for (dy, dx) in offsets]

            ok = True
            for y, x in coords:
                if y < 0 or y >= self.rows or x < 0 or x >= self.cols:
                    ok = False
                    break
            if not ok:
                continue

            # Нельзя затирать клетки любого цвета => ставим только в пустые
            for y, x in coords:
                if self.grid[y, x] != 0:
                    ok = False
                    break
            if not ok:
                continue

            for y, x in coords:
                self.grid[y, x] = color_state
            return True
        return False

    # ----------------------------
    # Update logic
    # ----------------------------
    # end try_place_group_of_4
    def update_logic(self):
        old_grid0 = self.grid
    
        # 1) Virus infection step (before Life rules)
        old_grid = self._apply_virus_infection(old_grid0)
    
        is_white = (old_grid == 1)
        is_red = (old_grid == 2)
        is_virus = (old_grid == 3)
        is_alive = is_white | is_red | is_virus
    
        white_neighbors = self.count_neighbors_vectorized(is_white)
        red_neighbors = self.count_neighbors_vectorized(is_red)
        virus_neighbors = self.count_neighbors_vectorized(is_virus)
        total_neighbors = white_neighbors + red_neighbors + virus_neighbors
    
        survivors_mask = is_alive & ((total_neighbors == 2) | (total_neighbors == 3))
        newborn_mask = (~is_alive) & (total_neighbors == 3)
    
        new_grid = np.zeros_like(old_grid)
        new_grid[survivors_mask] = old_grid[survivors_mask]
    
        # majority color among 3 for births
        max_counts = np.maximum.reduce([white_neighbors, red_neighbors, virus_neighbors])
        is_max_w = (white_neighbors == max_counts)
        is_max_r = (red_neighbors == max_counts)
        is_max_v = (virus_neighbors == max_counts)
    
        # If unique max -> choose it
        unique_w = is_max_w & (~is_max_r) & (~is_max_v)
        unique_r = is_max_r & (~is_max_w) & (~is_max_v)
        unique_v = is_max_v & (~is_max_w) & (~is_max_r)
    
        new_grid[newborn_mask & unique_w] = 1
        new_grid[newborn_mask & unique_r] = 2
        new_grid[newborn_mask & unique_v] = 3
    
        # ties -> random among tied max colors
        tie_newborn = newborn_mask & ~(unique_w | unique_r | unique_v)
        if np.any(tie_newborn):
            rand = np.random.random(old_grid.shape)
            # 2-way ties
            wr = tie_newborn & is_max_w & is_max_r & (~is_max_v)
            wv = tie_newborn & is_max_w & is_max_v & (~is_max_r)
            rv = tie_newborn & is_max_r & is_max_v & (~is_max_w)
            # 3-way tie
            wrv = tie_newborn & is_max_w & is_max_r & is_max_v
    
            if np.any(wr):
                new_grid[wr] = np.where(rand[wr] < 0.5, 1, 2).astype(np.uint8)
            if np.any(wv):
                new_grid[wv] = np.where(rand[wv] < 0.5, 1, 3).astype(np.uint8)
            if np.any(rv):
                new_grid[rv] = np.where(rand[rv] < 0.5, 2, 3).astype(np.uint8)
            if np.any(wrv):
                # split into 3
                r3 = rand[wrv]
                out = np.empty_like(r3, dtype=np.uint8)
                out[r3 < (1/3)] = 1
                out[(r3 >= (1/3)) & (r3 < (2/3))] = 2
                out[r3 >= (2/3)] = 3
                new_grid[wrv] = out
    
        # Raiders (still only white/red interact)
        self._apply_raider_strikes(old_grid, new_grid)
    
        # Virus lifecycle (stagnation + global TTL) + spontaneous spawn scheduling
        self._postprocess_virus_lifecycle(old_grid, new_grid)
    
        # Activity (includes virus)
        (act_total, act_white, act_red, act_virus, osc_percent,
         active_total_count, active_white_count, active_red_count, active_virus_count) = self.compute_activity(old_grid0, new_grid)
    
        self.activity_total = act_total
        self.activity_white = act_white
        self.activity_red = act_red
        self.activity_virus = act_virus
        self.oscillating_percent = osc_percent
        self.active_total_count = active_total_count
        self.active_white_count = active_white_count
        self.active_red_count = active_red_count
        self.active_virus_count = active_virus_count
    
        # History for oscillator detection
        self.history.append(old_grid0.copy())
        if len(self.history) > self.history_limit:
            self.history.pop(0)
    
        self.grid = new_grid
        self.generation += 1
        self.gen_since_bang += 1
    
        self._append_stats_point(
            active_total=self.active_total_count,
            active_red=self.active_red_count,
            active_white=self.active_white_count,
            active_virus=self.active_virus_count,
        )
        self._invalidate_stats_cache()
        self.mpl_live.update(self.stats)
    
        # Big bang trigger by activity
        if self.activity_total < self.activity_trigger:
            self.low_activity_streak += 1
        else:
            self.low_activity_streak = 0
    
        if self.low_activity_streak >= self.activity_patience:
            if self.gen_since_bang >= self.min_gens_between_bangs:
                self.big_bang()
            else:
                self.low_activity_streak = 0
    
    # end update_logic
    def _controls_overlay_visible(self):
        now = time.time()
        return self.controls_toggle or (now < self.controls_start_until)

    # ----------------------------
    # Input
    # ----------------------------
    # end _controls_overlay_visible
    def handle_input(self):
        keys = pygame.key.get_pressed()
        shift_held = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

        # eraser hold
        mouse_pressed = pygame.mouse.get_pressed()
        mx, my = pygame.mouse.get_pos()
        gpos = self._screen_to_grid(mx, my)

        if gpos is not None and shift_held and mouse_pressed[0]:
            gx, gy = gpos
            self.grid[gy, gx] = 0

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
                    self.show_stats = not self.show_stats
                    self._invalidate_stats_cache()
                elif event.key == pygame.K_g:
                    ok = self.mpl_live.toggle()
                    if not ok:
                        self.log_event("MATPLOTLIB", extra="not available")
                elif event.key == pygame.K_r:
                    self.validate_and_initialize_by_density()
                    self.log_event("RESET", extra=f"density={self.density_percent}%")
                elif event.key == pygame.K_c:
                    self.grid.fill(0)
                    self.generation = 0
                    self.gen_since_bang = 0
                    self.low_activity_streak = 0
                    self.history.clear()
                    # reset virus state
                    self.virus_epoch_start_gen = None
                    self.last_virus_end_gen = -10**9
                    self.virus_last_change_gen.fill(-10**9)
                    self.virus_groups_spawned_or_canceled = False
                    self._plan_virus_groups_spawn()
                    self.virus_spawns = 0
                    self.virus_infections = 0
                    self.virus_expire_global = 0
                    self.virus_expire_stagnation = 0

                    self.stats.reset()
                    self._invalidate_stats_cache()
                    self._append_stats_point(active_total=0, active_red=0, active_white=0, active_virus=0)
                    self.controls_start_until = time.time() + 3.0
                    self.log_event("CLEAR")
                    self.mpl_live.update(self.stats)
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
                elif event.key == pygame.K_e:
                    self.enable_raider_strike = not self.enable_raider_strike
                    self.log_event("RAIDER_TOGGLE", extra=f"enabled={self.enable_raider_strike}")
                elif event.key == pygame.K_v:
                    # Вирусы + будущие санитары (BIOHAZARD) включаются/выключаются вместе
                    self.biohazard_enabled = not self.biohazard_enabled
                    if not self.biohazard_enabled:
                        # выключение: сразу вычищаем вирусы и сбрасываем эпоху
                        if np.any(self.grid == VIRUS_STATE):
                            self.grid[self.grid == VIRUS_STATE] = 0
                            self.last_virus_end_gen = int(self.generation)
                        self.virus_epoch_start_gen = None
                    self.log_event("BIOHAZARD", extra=f"enabled={self.biohazard_enabled}")
                elif event.key == pygame.K_y:
                    self.raider_debug = not self.raider_debug
                    self._raider_dbg_points.clear()
                    self._raider_dbg_counts = None
                    self.log_event("RAIDER_DEBUG_TOGGLE", extra=f"enabled={self.raider_debug}")

            elif event.type == pygame.MOUSEBUTTONDOWN:
                # click on controls overlay closes it
                if event.button in (1, 3):
                    if self._controls_overlay_visible():
                        mx2, my2 = pygame.mouse.get_pos()
                        if self.controls_rect and self.controls_rect.collidepoint(mx2, my2):
                            self.controls_toggle = False
                            self.controls_start_until = 0.0
                            continue

                # LMB: start long press (manual bang) if not shift
                if event.button == 1:
                    if not shift_held:
                        self.manual_blast.start_hold()

                # RMB: place RED group of 4 immediately (short click behavior)
                if event.button == 3:
                    pos = self._screen_to_grid(*pygame.mouse.get_pos())
                    if pos is not None:
                        gx, gy = pos
                        self.try_place_group_of_4(gx, gy, color_state=2)

            elif event.type == pygame.MOUSEBUTTONUP:
                # LMB: if long press was NOT triggered -> short click -> place WHITE group of 4
                if event.button == 1:
                    if not shift_held:
                        pos = self._screen_to_grid(*pygame.mouse.get_pos())
                        was_triggered = self.manual_blast.triggered
                        dur = self.manual_blast.hold_duration()
                        self.manual_blast.stop_hold()

                        if pos is not None and (not was_triggered) and (dur < self.manual_blast.hold_seconds):
                            gx, gy = pos
                            self.try_place_group_of_4(gx, gy, color_state=1)

        # long press trigger (manual bang)
        if gpos is not None and self.manual_blast.should_trigger():
            gx, gy = gpos
            self.manual_boom_at(gx, gy)
            self.manual_blast.mark_triggered()

    # ----------------------------
    # Overlays
    # ----------------------------
    # end handle_input
    def draw_controls_overlay(self):
        if self.show_stats:
            self.controls_rect = None
            return

        if not self._controls_overlay_visible():
            self.controls_rect = None
            return

        w = int(self.screen.get_width() * 0.65)
        h = int(self.screen.get_height() * 0.54)
        ox = (self.screen.get_width() - w) // 2
        oy = (self.screen.get_height() - h) // 2
        self.controls_rect = pygame.Rect(ox, oy, w, h)

        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 210))
        pygame.draw.rect(surf, (220, 220, 220, 255), (0, 0, w, h), 2)

        title = self.font.render("CONTROLS (click to close)", True, (255, 255, 0))
        surf.blit(title, (18, 14))

        raider = "ON" if self.enable_raider_strike else "OFF"
        dbg = "ON" if self.raider_debug else "OFF"
        bio = "ON" if self.biohazard_enabled else "OFF"
        lines = [
            "Space: Pause / Run",
            "H: Show / Hide this overlay",
            "F: Toggle Fullscreen",
            "T: Toggle stats overlay (real-time)",
            "G: Toggle matplotlib window (real-time)",
            f"E: Toggle Raider Strike (currently {raider})",
            f"Y: Toggle Raider Debug (currently {dbg})",
            f"V: Toggle Biohazard (viruses+sanitarians) (currently {bio})",
            "R: Restart (same density)",
            "C: Clear field",
            "Up/Down: Speed +/-",
            "1/2: Density -/+ 5% (restart)",
            "",
            "Mouse:",
            "L-Click: place WHITE group of 4 (connected)",
            "R-Click: place RED group of 4 (connected)",
            "Shift + L-Click (hold): Erase",
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

        self.screen.blit(surf, (ox, oy))

    # ----------------------------
    # HUD + Draw
    # ----------------------------
    # end draw_controls_overlay
    def draw_hud(self):
        count_white = int(np.sum(self.grid == 1))
        count_red = int(np.sum(self.grid == 2))
        count_virus = int(np.sum(self.grid == VIRUS_STATE)) if self.biohazard_enabled else 0

        # Trace: VirusIn отображает:
        # - обратный отсчёт до первой волны (пока она запланирована и не отменена);
        # - '-' когда вирусы уже есть на поле;
        # - обратный отсчёт до следующего разрешённого появления после полного исчезновения (кулдаун).
        virus_in_str = "-"
        if self.biohazard_enabled:
            has_virus_now = bool(np.any(self.grid == VIRUS_STATE))
            if has_virus_now:
                virus_in_str = "-"
            else:
                gen = int(self.generation)
                # 1) Первая волна: пока не заспавнена/не отменена — показываем отсчёт
                if getattr(self, "virus_groups_spawn_gen", None) is not None and (not getattr(self, "virus_groups_spawned_or_canceled", False)):
                    virus_in_str = str(max(0, int(self.virus_groups_spawn_gen) - gen))
                else:
                    # 2) После полного исчезновения: показываем кулдаун до следующего появления
                    last_end = getattr(self, "last_virus_end_gen", None)
                    if last_end is not None:
                        wait = int(VIRUS_RESPAWN_COOLDOWN_GENS) - (gen - int(last_end))
                        virus_in_str = str(max(0, wait))
                    else:
                        virus_in_str = "0"
        # Trace: remaining lifetime of current virus epoch (if any)
        virus_life_left = None
        if self.biohazard_enabled and getattr(self, "virus_epoch_start_gen", None) is not None:
            virus_life_left = max(0, int(VIRUS_GLOBAL_LIFETIME_GENS) - (int(self.generation) - int(self.virus_epoch_start_gen)))

        panel_h = 56
        s = pygame.Surface((self.screen.get_width(), panel_h))
        s.set_alpha(200)
        s.fill((0, 0, 0))
        self.screen.blit(s, (0, 0))

        raider = "ON" if self.enable_raider_strike else "OFF"
        bio = "ON" if self.biohazard_enabled else "OFF"

        # HUD intentionally keeps only the most important runtime stats.
        # Removed from HUD (but still counted): field size, since-bang counters, manual explosions,
        # and key-hints for T/G and bang-threshold.
        virus_trace = ""
        if self.biohazard_enabled:
            gens_to_virus_str = virus_in_str
            if virus_life_left is None:
                virus_life_left_str = "-"
            else:
                virus_life_left_str = str(int(virus_life_left))
            virus_trace = f" | VirusIn:{gens_to_virus_str} | V:{count_virus} | VLife:{virus_life_left_str}"

        stats = (
            f"Gen:{self.generation} | Expl:{self.explosions} | RaiderExpl:{self.raider_explosions} | "
            f"W:{count_white} R:{count_red} | Spd:{self.speed}/s | "
            f"ActTot:{self.activity_total:.4f}%"
            f"{virus_trace}"
            f" | H:Help | F:Fullscreen | E:Raider({raider}) | V:Bio({bio}) | Y:RaiderDbg"
        )
        t = self.small_font.render(stats, True, (230, 230, 230))
        self.screen.blit(t, (18, 20))

    # end draw_hud



    def _draw_raider_debug(self):
        if (not self.raider_debug) or (not self._raider_dbg_points):
            return

        now_t = time.time()
        # фильтруем протухшие
        self._raider_dbg_points = [p for p in self._raider_dbg_points if p[0] > now_t]
        if not self._raider_dbg_points:
            return

        sx = self.view_rect.w / float(self.cols)
        sy = self.view_rect.h / float(self.rows)

        # рисуем маркеры поверх поля (дешево)
        for (_, kind, gy, gx) in self._raider_dbg_points[-RAIDER_DEBUG_MAX_POINTS:]:
            px = int(self.view_rect.x + (gx + 0.5) * sx)
            py = int(self.view_rect.y + (gy + 0.5) * sy)
            if kind == 'boom':
                pygame.draw.circle(self.screen, (255, 240, 120), (px, py), 6, 1)
            else:  # 'cand'
                pygame.draw.circle(self.screen, (120, 200, 255), (px, py), 3, 1)

        # небольшая строка с этапами
        if self._raider_dbg_counts:
            d = self._raider_dbg_counts
            txt = f"RaiderDbg: cand={d['candidates']} bfs={d['bfs_ok']} iso={d['iso_ok']} contact={d['contact_ok']} enemy={d['enemy_ok']} prob={d['prob_ok']} boom={d['exploded']}"
            t = self.small_font.render(txt, True, (230, 230, 230))
            self.screen.blit(t, (18, 44))

    # end _draw_raider_debug
    def draw(self):
        rgb_array = self.palette[self.grid]
        surface = pygame.surfarray.make_surface(rgb_array.swapaxes(0, 1))
        if surface.get_width() != self.view_rect.w or surface.get_height() != self.view_rect.h:
            surface = pygame.transform.scale(surface, (self.view_rect.w, self.view_rect.h))

        self.screen.fill(COLOR_BG)
        self.screen.blit(surface, (self.view_rect.x, self.view_rect.y))
        self.draw_hud()

        self._draw_raider_debug()

        if self.show_stats:
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
    # end draw
    def run(self):
        while self.running:
            self.handle_input()

            current_time = time.time()
            if not self.paused and (current_time - self.last_update_time) > (1.0 / self.speed):
                self.update_logic()
                self.last_update_time = current_time

            self.mpl_live.update(self.stats)
            self.draw()
            self.clock.tick(TARGET_FPS)

        self.log_event("END")
        self.mpl_live.close()
        pygame.quit()


    # end run
if __name__ == "__main__":
    game = TwoCampGameOfLife(
        field_w_px=FIELD_PX_W,
        field_h_px=FIELD_PX_H,
        window_w=WINDOW_W,
        window_h=WINDOW_H,
        scale=4,
        density_percent=DENSITY_PERCENT,
        start_fullscreen=START_FULLSCREEN,
    )
    game.run()