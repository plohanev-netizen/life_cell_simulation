import pygame
import numpy as np
import time

# --- КОНСТАНТЫ ---
WIDTH, HEIGHT = 1200, 800
TARGET_FPS = 60

# Цвета (RGB)
COLOR_BG = (0, 0, 30)       # Темно-синий фон
COLOR_WHITE = (220, 220, 255) # Белые клетки
COLOR_RED = (220, 50, 50)   # Красные клетки

# --- НАСТРОЙКИ ИНИЦИАЛИЗАЦИИ ---
# Задайте желаемое начальное количество клеток
INITIAL_WHITE = 5000
INITIAL_RED = 5000

class TwoCampGameOfLife:
    def __init__(self, width, height, scale=4, init_white=1000, init_red=1000):
        pygame.init()
        self.width = width
        self.height = height
        self.scale = scale
        self.cols = width // scale
        self.rows = height // scale
        
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Game of Life: Two Camps")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 16, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 14)

        # Сетка: 0 - мертво, 1 - белые, 2 - красные
        self.grid = np.zeros((self.rows, self.cols), dtype=np.uint8)
        
        self.running = True
        self.paused = True
        self.speed = 15
        self.last_update_time = time.time()
        self.generation = 0
        
        # Палитра для быстрой отрисовки: [фон, белые, красные]
        self.palette = np.array([COLOR_BG, COLOR_WHITE, COLOR_RED], dtype=np.uint8)
        
        # Валидация и инициализация
        self.init_white = init_white
        self.init_red = init_red
        self.validate_and_initialize()

    def validate_and_initialize(self):
        total_cells = self.rows * self.cols
        separator_width_cells = max(15, int(self.cols * 0.20))
        available_cells = total_cells - (separator_width_cells * self.rows)
        
        requested_total = self.init_white + self.init_red
        
        if requested_total < 3:
             print("Ошибка: Минимальное общее количество клеток — 3. Установлены значения по умолчанию.")
             self.init_white, self.init_red = 100, 100
        elif requested_total > available_cells:
            print(f"Ошибка: Слишком много клеток ({requested_total}). Доступно: {available_cells}. Количество уменьшено пропорционально.")
            ratio = available_cells / requested_total
            self.init_white = int(self.init_white * ratio)
            self.init_red = int(self.init_red * ratio)

        self.randomize_grid()

    def randomize_grid(self):
        self.grid.fill(0)
        self.generation = 0
        
        center_x = self.cols // 2
        separator_width = max(15, int(self.cols * 0.20))
        left_limit = center_x - separator_width // 2
        right_start = center_x + separator_width // 2
        
        # Заполняем левый лагерь (Красные - state 2)
        left_indices = [(r, c) for r in range(self.rows) for c in range(left_limit)]
        if left_indices and self.init_red > 0:
            chosen_idx = np.random.choice(len(left_indices), min(len(left_indices), self.init_red), replace=False)
            for idx in chosen_idx:
                r, c = left_indices[idx]
                self.grid[r, c] = 2

        # Заполняем правый лагерь (Белые - state 1)
        right_indices = [(r, c) for r in range(self.rows) for c in range(right_start, self.cols)]
        if right_indices and self.init_white > 0:
            chosen_idx = np.random.choice(len(right_indices), min(len(right_indices), self.init_white), replace=False)
            for idx in chosen_idx:
                r, c = right_indices[idx]
                self.grid[r, c] = 1


    def count_neighbors_vectorized(self, grid_mask):
        """
        Считает соседей БЕЗ перехода границ (границы 'глухие').
        Использует срезы (slicing) вместо np.roll.
        """
        grid = grid_mask.astype(np.uint8)
        neighbors = np.zeros_like(grid, dtype=np.uint8)
        
        # Получаем размеры
        rows, cols = grid.shape
        
        # --- Сдвиги по вертикали и горизонтали ---
        
        # Сдвиг ВНИЗ (смотрим на соседей СВЕРХУ / North)
        # Мы берем все строки кроме последней ([:-1]) и кладем их со второй строки ([1:])
        neighbors[1:, :] += grid[:-1, :]
        
        # Сдвиг ВВЕРХ (смотрим на соседей СНИЗУ / South)
        neighbors[:-1, :] += grid[1:, :]
        
        # Сдвиг ВПРАВО (смотрим на соседей СЛЕВА / West)
        neighbors[:, 1:] += grid[:, :-1]
        
        # Сдвиг ВЛЕВО (смотрим на соседей СПРАВА / East)
        neighbors[:, :-1] += grid[:, 1:]
        
        # --- Сдвиги по диагоналям ---
        
        # North-West (Сдвиг Вниз и Вправо)
        neighbors[1:, 1:] += grid[:-1, :-1]
        
        # North-East (Сдвиг Вниз и Влево)
        neighbors[1:, :-1] += grid[:-1, 1:]
        
        # South-West (Сдвиг Вверх и Вправо)
        neighbors[:-1, 1:] += grid[1:, :-1]
        
        # South-East (Сдвиг Вверх и Влево)
        neighbors[:-1, :-1] += grid[1:, 1:]
        
        return neighbors

    def update_logic(self):
        # Маски для разных типов клеток
        is_white = (self.grid == 1)
        is_red = (self.grid == 2)
        is_alive = is_white | is_red

        # Считаем соседей каждого цвета
        white_neighbors = self.count_neighbors_vectorized(is_white)
        red_neighbors = self.count_neighbors_vectorized(is_red)
        total_neighbors = white_neighbors + red_neighbors

        # --- Правила Жизни ---
        # Выжившие: живая клетка с 2 или 3 соседями
        survivors_mask = is_alive & ((total_neighbors == 2) | (total_neighbors == 3))
        
        # Новорожденные: мертвая клетка с ровно 3 соседями
        newborn_mask = (~is_alive) & (total_neighbors == 3)

        # --- Определение цвета новорожденных ---
        new_grid = np.zeros_like(self.grid)
        
        # Выжившие сохраняют свой цвет
        new_grid[survivors_mask] = self.grid[survivors_mask]
        
        # Логика цвета для новорожденных
        majority_white = (white_neighbors > red_neighbors)
        majority_red = (red_neighbors > white_neighbors)
        tie = (white_neighbors == red_neighbors)
        
        # Применяем цвета
        new_grid[newborn_mask & majority_white] = 1
        new_grid[newborn_mask & majority_red] = 2
        
        # При ничьей выбираем случайно
        if np.any(newborn_mask & tie):
            random_choices = np.random.choice([1, 2], size=self.grid.shape).astype(np.uint8)
            new_grid[newborn_mask & tie] = random_choices[newborn_mask & tie]

        self.grid = new_grid
        self.generation += 1

    def handle_input(self):
        keys = pygame.key.get_pressed()
        shift_held = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE: self.paused = not self.paused
                elif event.key == pygame.K_r: self.randomize_grid()
                elif event.key == pygame.K_c: self.grid.fill(0); self.generation=0
                elif event.key == pygame.K_UP: self.speed = min(60, self.speed + 2)
                elif event.key == pygame.K_DOWN: self.speed = max(1, self.speed - 2)
        
        # Рисование мышью
        mouse_pressed = pygame.mouse.get_pressed()
        x, y = pygame.mouse.get_pos()
        grid_x, grid_y = x // self.scale, y // self.scale

        if 0 <= grid_x < self.cols and 0 <= grid_y < self.rows:
            if shift_held and mouse_pressed[0]: # Shift + ЛКМ = Ластик
                self.grid[grid_y, grid_x] = 0
            elif mouse_pressed[0]: # ЛКМ = Белые
                self.grid[grid_y, grid_x] = 1
            elif mouse_pressed[2]: # ПКМ = Красные
                self.grid[grid_y, grid_x] = 2

    def draw_hud(self):
        # Верхняя панель статистики
        count_white = np.sum(self.grid == 1)
        count_red = np.sum(self.grid == 2)
        
        panel_h = 35
        s = pygame.Surface((self.width, panel_h))
        s.set_alpha(200)
        s.fill((0, 0, 0))
        self.screen.blit(s, (0, 0))
        
        stats = f"Generation: {self.generation}  |  WHITE: {count_white}  |  RED: {count_red}  |  Speed: {self.speed}/s"
        text = self.font.render(stats, True, COLOR_WHITE)
        self.screen.blit(text, (20, 8))

        # Нижняя панель управления
        if self.paused:
            help_s = pygame.Surface((320, 90))
            help_s.set_alpha(180)
            help_s.fill((0,0,0))
            self.screen.blit(help_s, (10, self.height - 100))
            
            controls = ["PAUSED", "L-Click: White | R-Click: Red", "Shift+Click: Erase", "Space: Run | R: Reset | C: Clear", "Arrows: Adjust Speed"]
            for i, line in enumerate(controls):
                c = COLOR_WHITE if i > 0 else (255, 255, 0)
                t = self.small_font.render(line, True, c)
                self.screen.blit(t, (20, self.height - 90 + i*18))

    def draw(self):
        # Быстрая отрисовка через палитру
        rgb_array = self.palette[self.grid]
        surface = pygame.surfarray.make_surface(rgb_array.swapaxes(0, 1))
        if self.scale > 1:
            surface = pygame.transform.scale(surface, (self.width, self.height))
        self.screen.blit(surface, (0, 0))
        self.draw_hud()
        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_input()
            current_time = time.time()
            if not self.paused and current_time - self.last_update_time > (1.0 / self.speed):
                self.update_logic()
                self.last_update_time = current_time
            self.draw()
            self.clock.tick(TARGET_FPS)
        pygame.quit()

if __name__ == "__main__":
    # Можете менять параметры scale, init_white и init_red
    game = TwoCampGameOfLife(WIDTH, HEIGHT, scale=4, 
                             init_white=INITIAL_WHITE, 
                             init_red=INITIAL_RED)
    game.run()