import pygame
import numpy as np
import time

# --- КОНСТАНТЫ ---
WIDTH, HEIGHT = 1000, 800
TARGET_FPS = 60

# Цвета (RGB)
COLOR_BG = (0, 0, 50)      # Темно-синий фон
COLOR_CELL = (255, 255, 255) # Белые клетки

class GameOfLife:
    def __init__(self, width, height, scale=4):
        pygame.init()
        self.width = width
        self.height = height
        self.scale = scale # Размер одной клетки (пиксели)
        
        # Реальное разрешение сетки
        self.cols = width // scale
        self.rows = height // scale
        
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Conway's Game of Life [PRO]")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Verdana", 14)

        # Основная сетка (NumPy массив)
        self.grid = np.zeros((self.rows, self.cols), dtype=np.uint8)
        
        # Состояние игры
        self.running = True
        self.paused = True # Начинаем с паузы, чтобы можно было порисовать
        self.speed = 10    # Скорость обновлений в секунду
        self.last_update_time = time.time()
        self.generation = 0
        
        # Создаем палитру для surfarray (быстрая отрисовка)
        # 0 -> COLOR_BG, 1 -> COLOR_CELL
        self.palette = np.array([COLOR_BG, COLOR_CELL], dtype=np.uint8)
        
        self.randomize_grid()

    def randomize_grid(self):
        """Заполняет сетку случайным шумом (15% живых)."""
        self.grid = np.random.choice([0, 1], size=(self.rows, self.cols), p=[0.85, 0.15]).astype(np.uint8)
        self.generation = 0

    def clear_grid(self):
        """Очищает поле."""
        self.grid.fill(0)
        self.generation = 0

    def update_logic(self):
        """Логика игры на NumPy (максимальная скорость)."""
        # Считаем соседей сдвигами массива (векторизация)
        # N, S, E, W, NE, NW, SE, SW
        neighbors = (
            np.roll(self.grid, 1, axis=0) +  # Вверх
            np.roll(self.grid, -1, axis=0) + # Вниз
            np.roll(self.grid, 1, axis=1) +  # Влево
            np.roll(self.grid, -1, axis=1) + # Вправо
            np.roll(np.roll(self.grid, 1, axis=0), 1, axis=1) +   # Вверх-Влево
            np.roll(np.roll(self.grid, 1, axis=0), -1, axis=1) +  # Вверх-Вправо
            np.roll(np.roll(self.grid, -1, axis=0), 1, axis=1) +  # Вниз-Влево
            np.roll(np.roll(self.grid, -1, axis=0), -1, axis=1)   # Вниз-Вправо
        )

        # Правила:
        # 1. Живая (1) и (2 или 3 соседа) -> Живая (1)
        # 2. Мертвая (0) и (3 соседа) -> Живая (1)
        # Все остальное -> 0
        self.grid = np.where((self.grid == 1) & ((neighbors == 2) | (neighbors == 3)), 1,
                             np.where((self.grid == 0) & (neighbors == 3), 1, 0)).astype(np.uint8)
        self.generation += 1

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_c:
                    self.clear_grid()
                elif event.key == pygame.K_r:
                    self.randomize_grid()
                elif event.key == pygame.K_UP:
                    self.speed = min(60, self.speed + 2)
                elif event.key == pygame.K_DOWN:
                    self.speed = max(1, self.speed - 2)
        
        # Рисование мышкой (работает даже во время паузы)
        if pygame.mouse.get_pressed()[0]: # Левая кнопка - оживить
            x, y = pygame.mouse.get_pos()
            grid_x, grid_y = x // self.scale, y // self.scale
            if 0 <= grid_x < self.cols and 0 <= grid_y < self.rows:
                self.grid[grid_y, grid_x] = 1
        
        elif pygame.mouse.get_pressed()[2]: # Правая кнопка - убить
            x, y = pygame.mouse.get_pos()
            grid_x, grid_y = x // self.scale, y // self.scale
            if 0 <= grid_x < self.cols and 0 <= grid_y < self.rows:
                self.grid[grid_y, grid_x] = 0

    def draw(self):
        # 1. Магия Surfarray: создаем изображение из массива чисел моментально
        # Сначала транслируем 0 и 1 в цвета, затем создаем поверхность
        # Примечание: swapaxes нужен, так как Pygame ожидает (width, height), а NumPy (rows, cols)
        rgb_array = self.palette[self.grid]
        surface = pygame.surfarray.make_surface(rgb_array.swapaxes(0, 1))
        
        # Масштабируем до размера экрана (если scale > 1)
        if self.scale > 1:
            surface = pygame.transform.scale(surface, (self.width, self.height))
        
        self.screen.blit(surface, (0, 0))

        # 2. Отрисовка интерфейса (HUD)
        self.draw_hud()
        
        pygame.display.flip()

    def draw_hud(self):
        # Полупрозрачная подложка
        panel_w, panel_h = 240, 130
        s = pygame.Surface((panel_w, panel_h))
        s.set_alpha(180)
        s.fill((0, 0, 0))
        self.screen.blit(s, (10, 10))
        
        info = [
            f"FPS: {int(self.clock.get_fps())}",
            f"Sim Speed: {self.speed}/sec",
            f"Generation: {self.generation}",
            f"Population: {np.sum(self.grid)}",
            f"Status: {'PAUSED' if self.paused else 'RUNNING'}",
            "",
            "Controls: Space, R, C, Mouse, Arrows"
        ]
        
        for i, line in enumerate(info):
            color = (0, 255, 0) if i < 5 else (200, 200, 200)
            text = self.font.render(line, True, color)
            self.screen.blit(text, (20, 20 + i * 18))

    def run(self):
        while self.running:
            self.handle_input()
            
            # Логика обновления отделена от отрисовки
            # Мы обновляем поле только если прошло достаточно времени (self.speed)
            current_time = time.time()
            if not self.paused:
                if current_time - self.last_update_time > (1.0 / self.speed):
                    self.update_logic()
                    self.last_update_time = current_time
            
            self.draw()
            self.clock.tick(TARGET_FPS) # Отрисовка всегда плавная (60 FPS)

        pygame.quit()

if __name__ == "__main__":
    # scale=4 означает, что одна клетка = 4x4 пикселя. 
    # Поле будет размером 250x200 (при окне 1000x800).
    game = GameOfLife(WIDTH, HEIGHT, scale=4)
    game.run()