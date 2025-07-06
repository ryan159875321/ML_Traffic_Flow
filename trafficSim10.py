import pygame
import random
import math

pygame.init()

WIDTH, HEIGHT = 1600, 1200
GRID_SIZE = 40
CELL_SIZE = WIDTH // (GRID_SIZE + 10)

WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
ROAD_GRAY = (150, 150, 150)
RED = (255, 0, 0)
GREEN = (0, 200, 0)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dumb Traffic Lights - Optimised (60/90/120/180s Screengrabs)")

font = pygame.font.SysFont(None, 36)

random.seed(42)

intersection_spacing = 10
road_width = 2
roads = set()
intersections = []

for y in range(road_width, GRID_SIZE, intersection_spacing):
    for x in range(GRID_SIZE):
        roads.add((x, y))
        roads.add((x, y + 1))

for x in range(road_width, GRID_SIZE, intersection_spacing):
    for y in range(GRID_SIZE):
        roads.add((x, y))
        roads.add((x + 1, y))

for x in range(road_width, GRID_SIZE, intersection_spacing):
    for y in range(road_width, GRID_SIZE, intersection_spacing):
        intersections.append((x, y))

directions = {
    'right': (1, 0),
    'left': (-1, 0),
    'down': (0, 1),
    'up': (0, -1)
}

SAFE_DISTANCE = CELL_SIZE
cars_exited = 0
exit_at_60s = None
exit_at_90s = None
exit_at_120s = None
exit_at_180s = None
exit_at_300s = None

def distance_travelled(v):
    start_x, start_y = v.initial_pos
    current_x, current_y = v.grid_pos
    return abs(current_x - start_x) + abs(current_y - start_y)

class TrafficLightController:
    def __init__(self):
        self.timer = 0
        self.interval = 150
        self.all_red_duration = 30
        self.state = 'NS'
        self.lights = {}
        self.in_all_red = False
        self.all_red_timer = 0
        self.init_lights()

    def init_lights(self):
        for ix, iy in intersections:
            self.lights[(ix, iy)] = {
                'up': 'green' if self.state == 'NS' else 'red',
                'down': 'green' if self.state == 'NS' else 'red',
                'left': 'green' if self.state == 'EW' else 'red',
                'right': 'green' if self.state == 'EW' else 'red'
            }

    def update(self, vehicles):
        self.timer += 1
        if self.in_all_red:
            self.all_red_timer += 1
            if self.all_red_timer >= self.all_red_duration:
                self.in_all_red = False
                self.all_red_timer = 0
                self.state = 'EW' if self.state == 'NS' else 'NS'
                for key in self.lights:
                    self.lights[key]['up'] = 'green' if self.state == 'NS' else 'red'
                    self.lights[key]['down'] = 'green' if self.state == 'NS' else 'red'
                    self.lights[key]['left'] = 'green' if self.state == 'EW' else 'red'
                    self.lights[key]['right'] = 'green' if self.state == 'EW' else 'red'
            return
        if self.timer >= self.interval:
            self.timer = 0
            self.in_all_red = True
            for key in self.lights:
                for dir in self.lights[key]:
                    self.lights[key][dir] = 'red'

    def draw(self):
        for (ix, iy), lights in self.lights.items():
            for direction, color in lights.items():
                cx, cy = ix * CELL_SIZE, iy * CELL_SIZE
                offset = CELL_SIZE // 3
                if direction == 'up':
                    pos = (cx + CELL_SIZE, cy - offset)
                elif direction == 'down':
                    pos = (cx + CELL_SIZE, cy + 2 * CELL_SIZE + offset)
                elif direction == 'left':
                    pos = (cx - offset, cy + CELL_SIZE)
                elif direction == 'right':
                    pos = (cx + 2 * CELL_SIZE + offset, cy + CELL_SIZE)
                pygame.draw.rect(screen, GREEN if color == 'green' else RED, (pos[0], pos[1], 8, 8))

class Vehicle:
    def __init__(self, grid_x, grid_y, direction):
        self.direction = direction
        self.dx, self.dy = directions[direction]
        self.speed = 1.5
        self.x = grid_x * CELL_SIZE
        self.y = grid_y * CELL_SIZE
        self.color = (0, 0, 0) if random.random() < 0.85 else (255, 0, 255)
        self.grid_pos = (grid_x, grid_y)
        self.entered_grid = False
        self.initial_pos = (grid_x, grid_y)

    def move(self, vehicles):
        if self.should_stop(vehicles):
            return
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed
        self.grid_pos = (int(self.x // CELL_SIZE), int(self.y // CELL_SIZE))

        gx, gy = self.grid_pos
        if (gx, gy) in roads:
            self.entered_grid = True

    def is_off_screen(self):
        return (self.x < -CELL_SIZE or self.x > WIDTH or self.y < -CELL_SIZE or self.y > HEIGHT)

    def in_intersection(self):
        gx, gy = self.grid_pos
        for ix, iy in intersections:
            if ix <= gx < ix + 2 and iy <= gy < iy + 2:
                return True
        return False

    def should_stop(self, vehicles):
        if self.in_intersection():
            return False
        next_x = int((self.x + self.dx * CELL_SIZE) // CELL_SIZE)
        next_y = int((self.y + self.dy * CELL_SIZE) // CELL_SIZE)
        if (next_x, next_y) in roads:
            for ix, iy in intersections:
                if ix <= next_x < ix + 2 and iy <= next_y < iy + 2:
                    if traffic_lights.lights[(ix, iy)][self.direction] != 'green':
                        return True
        for other in vehicles:
            if other == self:
                continue
            if self.is_ahead(other) and self.distance_to(other) < SAFE_DISTANCE:
                return True
        return False

    def is_ahead(self, other):
        if self.direction == 'right' and self.y == other.y and other.x > self.x:
            return True
        if self.direction == 'left' and self.y == other.y and other.x < self.x:
            return True
        if self.direction == 'down' and self.x == other.x and other.y > self.y:
            return True
        if self.direction == 'up' and self.x == other.x and other.y < self.y:
            return True
        return False

    def distance_to(self, other):
        return math.hypot(self.x - other.x, self.y - other.y)

vehicles = []
simulation_time_frames = 0
traffic_lights = TrafficLightController()

def spawn_vehicle():
    spawn_points = []
    for y in range(road_width, GRID_SIZE, intersection_spacing):
        spawn_points.append((0, y, 'right'))
        spawn_points.append((GRID_SIZE - 1, y + 1, 'left'))
    for x in range(road_width, GRID_SIZE, intersection_spacing):
        spawn_points.append((x, 0, 'down'))
        spawn_points.append((x, GRID_SIZE - 1, 'up'))
    if len(vehicles) < 120:
        random.shuffle(spawn_points)
        for x, y, direction in spawn_points:
            spawn_clear = True
            for v in vehicles:
                if math.hypot(v.x - x * CELL_SIZE, v.y - y * CELL_SIZE) < SAFE_DISTANCE:
                    spawn_clear = False
                    break
            if spawn_clear:
                vehicles.append(Vehicle(x, y, direction))
                break

clock = pygame.time.Clock()
running = True

while running:
    screen.fill(WHITE)
    simulation_time_frames += 1
    elapsed_seconds = simulation_time_frames / 30

    if exit_at_60s is None and simulation_time_frames >= 1800:
        exit_at_60s = cars_exited
    if exit_at_90s is None and simulation_time_frames >= 2700:
        exit_at_90s = cars_exited
    if exit_at_120s is None and simulation_time_frames >= 3600:
        exit_at_120s = cars_exited
    if exit_at_180s is None and simulation_time_frames >= 5400:
        exit_at_180s = cars_exited
    if exit_at_300s is None and simulation_time_frames >= 9000:
        exit_at_300s = cars_exited

    for x, y in roads:
        pygame.draw.rect(screen, ROAD_GRAY, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
    for x, y in intersections:
        pygame.draw.rect(screen, GRAY, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE * 2, CELL_SIZE * 2))

    traffic_lights.update(vehicles)
    traffic_lights.draw()

    screen.blit(font.render(f"Time: {elapsed_seconds:.1f}s", True, (0, 0, 0)), (10, 10))
    screen.blit(font.render(f"Exited: {cars_exited}", True, (0, 0, 0)), (10, 50))

    if exit_at_60s is not None:
        screen.blit(font.render(f"At 60s: {exit_at_60s} exited", True, (0, 0, 0)), (10, 90))
    if exit_at_90s is not None:
        screen.blit(font.render(f"At 90s: {exit_at_90s} exited", True, (0, 0, 0)), (10, 130))
    if exit_at_120s is not None:
        screen.blit(font.render(f"At 120s: {exit_at_120s} exited", True, (0, 0, 0)), (10, 170))
    if exit_at_180s is not None:
        screen.blit(font.render(f"At 180s: {exit_at_180s} exited", True, (0, 0, 0)), (10, 210))
    if exit_at_300s is not None:
        screen.blit(font.render(f"At 300s: {exit_at_300s} exited", True, (0, 0, 0)), (10, 250))


    if random.random() < 0.35:
        spawn_vehicle()

    for v in vehicles[:]:
        v.move(vehicles)
        if v.is_off_screen():
            if v.entered_grid and distance_travelled(v) >= 5:
                cars_exited += 1
            vehicles.remove(v)

    for v in vehicles:
        pygame.draw.rect(screen, v.color, (int(v.x), int(v.y), CELL_SIZE // 2, CELL_SIZE // 2))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
