import pygame
import time
import random
import math
import os
import numba as nb
import numpy as np

CORES = os.cpu_count()

# Dimensions
SCREEN = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SCREEN_WIDTH = SCREEN.get_width()
SCREEN_HEIGHT = SCREEN.get_height()

# Starts top right corner. Goes around clockwise
LAVA_LAMP_STRUCTURE_RATIOS = [
    [
        (0.59217877095, 0),
        (0.74022346369, 0.10788381743),
        (1, 0.69917012448),
        (0.75977653631, 0.84647302905),
        (0.98044692737, 1),
        (0.019553072629999946, 1),
        (0.24022346369000003, 0.84647302905),
        (0, 0.69917012448),
        (0.25977653631, 0.10788381743),
        (0.40782122904999996, 0)
    ],
    [
        (0.74, 0),
        (0.8, 0.14040114613180515),
        (1, 0.6160458452722063),
        (0.8266666666666667, 0.7392550143266475),
        (0.68, 0.8510028653295129),
        (0.8, 1),
        (0.19999999999999996, 1),
        (0.31999999999999995, 0.8510028653295129),
        (0.17333333333333334, 0.7392550143266475),
        (0, 0.6160458452722063),
        (0.19999999999999996, 0.14040114613180515),
        (0.26, 0.0)
    ],
    [
        (.9, 0),
        (.9, .1),
        (.9, .8),
        (.9, 1),
        (.1, 1),
        (.1, .8),
        (.1, .1),
        (.1, 0),
    ]
]

LAVA_LAMP_STRUCTURE_CANISTER_INDICES = [
    [1, 2, 7, 8],
    [1, 2, 3, 8, 9, 10],
    [1, 2, 5, 6]
]


# Colors
def grey(n):
    return n, n, n


BACKGROUND_COLOR = grey(195)
LAVA_LAMP_BASE_COLOR = grey(84)
RED_LAVA_LAMP_FLUID_COLOR = (240, 69, 8)
RED_LAVA_LAMP_WAX_COLOR = (254, 173, 17)
GREEN_LAVA_LAMP_FLUID_COLOR = (42, 195, 55)
GREEN_LAVA_LAMP_WAX_COLOR = (59, 253, 14)
BLUE_LAVA_LAMP_FLUID_COLOR = (1, 173, 240)
BLUE_LAVA_LAMP_WAX_COLOR = (10, 246, 254)


@nb.njit(fastmath=True)
def evaluate(x, y, bx, by, br_squared):
    if bx == x and by == y:
        return 1000
    dx = bx - x
    dy = by - y
    return br_squared / (dx * dx + dy * dy)


class MetaBall:
    INITIAL_VELOCITY_RANGE = (25, 50)
    SQUISH_BORDER = 10

    def __init__(self, pos, radius, lamp):
        self.pos = list(pos)
        self.radius = radius
        self.radius_squared = radius ** 2

        self.mass = math.pi * self.radius_squared

        angle = random.uniform(0, 2 * math.pi)
        vel_magnitude = random.uniform(MetaBall.INITIAL_VELOCITY_RANGE[0], MetaBall.INITIAL_VELOCITY_RANGE[1])
        self.vel = [
            math.cos(angle) * vel_magnitude / 2,  # Divide by two so it moves more in the y direction
            math.sin(angle) * vel_magnitude
        ]

        self.acceleration = [0, 0]

        self.lamp = lamp

        self.set_evaluation_all_data()

    def update(self, elapsed):
        # Update the acceleration
        y_range = self.lamp.y_range
        delta_y = self.pos[1] - sum(y_range) / 2
        F = -1 / 1000 * delta_y  # F = -k deltaY
        self.acceleration[1] = F / self.mass  # a = F / m

        for other in self.lamp.meta_balls:
            if other == self:
                continue

            dist_squared = (self.pos[0] - other.pos[0]) ** 2 + (self.pos[1] - other.pos[1]) ** 2
            if dist_squared < 10:
                continue
            F = 1 * self.mass * other.mass / dist_squared
            theta = math.atan2(self.pos[1] - other.pos[1], self.pos[0] - other.pos[0])
            self.acceleration[0] += F * math.cos(theta) / self.mass
            self.acceleration[1] += F * math.sin(theta) / self.mass

        # Update velocity
        self.vel[0] += self.acceleration[0] * elapsed
        self.vel[1] += self.acceleration[1] * elapsed

        # Update position
        self.pos[0] += self.vel[0] * elapsed
        self.pos[1] += self.vel[1] * elapsed

        # Enforce boundaries on the position
        y_range = self.lamp.y_range
        x_range = self.lamp.get_x_range(self.pos[1])
        if x_range is not None:
            contact = False
            if self.pos[0] < x_range[0] + self.radius - MetaBall.SQUISH_BORDER and self.vel[0] < 0:
                # self.vel[0] = -self.vel[0]
                self.acceleration[0] = 1000
                contact = True
            if self.pos[0] > x_range[1] - self.radius + MetaBall.SQUISH_BORDER and self.vel[0] > 0:
                # self.vel[0] = -self.vel[0]
                self.acceleration[0] = -1000
                contact = True

            if not contact:
                self.acceleration[0] = 0

        if self.pos[1] < y_range[0] + self.radius - MetaBall.SQUISH_BORDER and self.vel[1] < 0:
            self.vel[1] = -self.vel[1]
        if self.pos[1] > y_range[1] - self.radius + MetaBall.SQUISH_BORDER and self.vel[1] > 0:
            self.vel[1] = -self.vel[1]

        self.set_evaluation_pos_data()

    def set_evaluation_pos_data(self):
        self.evaluation_data[0] = self.pos[0]
        self.evaluation_data[1] = self.pos[1]

    def set_evaluation_all_data(self):
        self.evaluation_data = [self.pos[0], self.pos[1], self.radius_squared]


class Lamp:
    HEAT_FORCE = 20

    def __init__(self, cx, cy, w, h, shape_index, fluid_color, wax_color, num_metaballs):
        # Create and position the rect
        self.rect = pygame.Rect(0, 0, round(w), round(h))
        self.rect.center = (round(cx), round(cy))

        self.fluid_color = fluid_color
        self.wax_color = wax_color

        # Calculate where the vertices of the lamp are located
        self.shape_index = shape_index
        self.structure_points = [
            (
                round(self.rect.x + self.rect.w * LAVA_LAMP_STRUCTURE_RATIOS[shape_index][i][0]),
                round(self.rect.y + self.rect.h * LAVA_LAMP_STRUCTURE_RATIOS[shape_index][i][1])
            )
            for i in range(len(LAVA_LAMP_STRUCTURE_RATIOS[self.shape_index]))
        ]

        # This is the range of pixels that the canister is located
        self.y_range = np.array([-1, -1])

        # This is a temporary surface to calculate the range of pixels the fluids are located in
        canister_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.draw.polygon(
            canister_surface,
            self.fluid_color,
            [self.structure_points[i] for i in LAVA_LAMP_STRUCTURE_CANISTER_INDICES[self.shape_index]]
        )
        array = pygame.PixelArray(canister_surface)

        # Determine the range of y pixels
        for y in range(self.rect.y - 5, self.rect.y + self.rect.h + 5):
            if array[int(cx), y] > 0 and array[int(cx), y - 1] == 0:
                self.y_range[0] = y
            elif array[int(cx), y] == 0 and array[int(cx), y - 1] > 0:
                self.y_range[1] = y - 1

        # Determine teh range of x pixels for each y level
        self.x_ranges = np.empty((self.y_range[1] - self.y_range[0] + 1, 2), dtype=int)
        for y in range(self.y_range[0], self.y_range[1] + 1):
            if array[int(cx), y] > 0:
                for x in range(self.rect.x - 5, self.rect.x + self.rect.w + 5):
                    if array[x, y] > 0 and array[x - 1, y] == 0:
                        # This definitely happens before the elif
                        self.x_ranges[y - self.y_range[0]][0] = x
                    elif array[x, y] == 0 and array[x - 1, y] > 0:
                        self.x_ranges[y - self.y_range[0]][1] = x - 1

        # Position some meta balls in the lamp
        self.meta_balls = []
        for _ in range(num_metaballs):
            ball_radius = random.choice(range(20, 46, 5))
            positionInvalid = True
            while positionInvalid:
                pos_y = random.randint(self.y_range[0] + ball_radius, self.y_range[1] - ball_radius)
                if self.x_ranges[pos_y - self.y_range[0]][0] + ball_radius >= \
                        self.x_ranges[pos_y - self.y_range[0]][1] - ball_radius:
                    continue

                pos_x = random.randint(
                    self.x_ranges[pos_y - self.y_range[0]][0] + ball_radius,
                    self.x_ranges[pos_y - self.y_range[0]][1] - ball_radius
                )

                positionInvalid = False

            self.meta_balls.append(MetaBall((pos_x, pos_y), ball_radius, self))

        # Generate the base structure of the lamp
        #   Includes the structure and the base fluid
        #   Done this way because apparently draw.polygon is slow as heck
        self.base_surface = pygame.Surface((self.rect.w, self.rect.h))
        self.base_surface.set_colorkey(grey(0))

        # Draw the shape of the lava lamp
        pygame.draw.polygon(
            self.base_surface,
            LAVA_LAMP_BASE_COLOR,
            [(p[0] - self.rect.x, p[1] - self.rect.y) for p in self.structure_points]
        )

        pygame.draw.polygon(
            self.base_surface,
            self.fluid_color,
            [(self.structure_points[i][0] - self.rect.x, self.structure_points[i][1] - self.rect.y)
             for i in LAVA_LAMP_STRUCTURE_CANISTER_INDICES[self.shape_index]]
        )

        # Create a small surface for use in drawing the wax particles
        self.wax_surface = pygame.Surface((self.rect.w, self.rect.h))
        self.wax_surface.set_colorkey(grey(0))

    def get_x_range(self, y):
        if not (self.y_range[0] <= y <= self.y_range[1]):
            return None
        y = int(y)
        return self.x_ranges[y - self.y_range[0]]

    def update(self, elapsed):
        for ball in self.meta_balls:
            ball.update(elapsed)

    @staticmethod
    @nb.njit(parallel=True, fastmath=True)
    def draw_canister_helper(screen_array, wax_color, canister_y_range, canister_ranges,
                             metaball_data, uniform_box_size, threshold, offset_x, offset_y):
        """
        Holy hell this a mess. Good luck future me.
        Args:
            screen_array: The pixel array for the screen
            wax_color: The color this will be applying to the screen
            canister_y_range: The range of y values to consider
            canister_ranges: For a given y, what is the valid range of xs
            metaball_data: The position and radius of all metaballs
            uniform_box_size: What size chunk will the range be divided intox
            threshold: What threshold is needed for a chunk to be considered
        """
        num_y_boxes = math.ceil(int(canister_y_range[1] - canister_y_range[0]) / uniform_box_size)

        # One loop per core
        for start in nb.prange(CORES):
            # Loop over y level boxes for this core
            for yi in range(start, num_y_boxes, CORES):
                # Calculate the y pixel corresponding to the top of this box
                y = yi * uniform_box_size + canister_y_range[0]

                # Loop over the x level boxes at this y level
                num_x_boxes = math.ceil(
                    int(canister_ranges[y - canister_y_range[0]][1] -
                        canister_ranges[y - canister_y_range[0]][0])
                    / uniform_box_size
                )

                for xi in range(-1, num_x_boxes + 1):
                    # Calculate the x pixel corresponding to the left of this box
                    x = xi * uniform_box_size + canister_ranges[y - canister_y_range[0]][0]

                    # Loop over and sum the evaluation relative to each metaball
                    #   at the center of this uniform box
                    total = 0
                    for bx, by, br in metaball_data:
                        total += evaluate(x + uniform_box_size // 2, y + uniform_box_size // 2, bx, by, br)

                        # If the total is greater than the threshold, then that means this
                        #   box probably contains some filled in pixels
                        if total >= threshold:
                            for yy in range(y, min(y + uniform_box_size, canister_y_range[1]) + 1):
                                for xx in range(
                                        max(x, canister_ranges[yy - canister_y_range[0]][0]),
                                        min(x + uniform_box_size, canister_ranges[yy - canister_y_range[0]][1]) + 1
                                ):
                                    total = 0
                                    for bx, by, br in metaball_data:
                                        total += evaluate(xx, yy, bx, by, br)
                                        if total >= 1:
                                            # The pixel (xx, yy) is close enough to a metaball(s) so fill it in
                                            screen_array[xx + offset_x, yy + offset_y] = wax_color
                                            break
                            break

        return screen_array

    def draw_canister(self, surface):
        ball_data = np.array([b.evaluation_data for b in self.meta_balls])

        self.wax_surface.fill(grey(0))
        screen_array = np.array(pygame.PixelArray(self.wax_surface))

        r, g, b = self.wax_color

        Lamp.draw_canister_helper(
            screen_array,
            (r << 16) + (g << 8) + b,
            self.y_range,
            self.x_ranges,
            ball_data,
            10,
            .5,
            -self.rect.x,
            -self.rect.y
        )
        pygame.surfarray.blit_array(self.wax_surface, screen_array)
        surface.blit(self.wax_surface, (self.rect.x, self.rect.y))

    def draw(self, surface):
        surface.blit(self.base_surface, (self.rect.x, self.rect.y))

        self.draw_canister(surface)


class MainScene:
    def __init__(self):
        self.surface = SCREEN
        self.clock = pygame.time.Clock()

        lamp_data = [
            # (CenterX, CenterY, LampShape FluidColor, WaxColor, MetaBallCount)
            (SCREEN_WIDTH * 1 / 4, SCREEN_HEIGHT / 2, 0, RED_LAVA_LAMP_FLUID_COLOR, RED_LAVA_LAMP_WAX_COLOR, 8),
            (SCREEN_WIDTH * 2 / 4, SCREEN_HEIGHT / 2, 1, GREEN_LAVA_LAMP_FLUID_COLOR, GREEN_LAVA_LAMP_WAX_COLOR, 8),
            (SCREEN_WIDTH * 3 / 4, SCREEN_HEIGHT / 2, 2, BLUE_LAVA_LAMP_FLUID_COLOR, BLUE_LAVA_LAMP_WAX_COLOR, 8),
        ]

        self.lamps = []

        for cx, cy, shape, fluid, wax, num in lamp_data:
            self.lamps.append(
                Lamp(
                    cx, cy,
                    SCREEN_WIDTH * .2, SCREEN_HEIGHT * .8,
                    shape,
                    fluid, wax,
                    num
                )
            )

    def update(self, elapsed):
        for lamp in self.lamps:
            lamp.update(elapsed)

    def draw(self):
        self.surface.fill(BACKGROUND_COLOR)

        for lamp in self.lamps:
            lamp.draw(self.surface)

    def run(self):

        fps_total = 0
        fps_count = 0

        total_time = 0
        last_update_time = time.time()
        # while total_time < 20:
        while True:

            for event in pygame.event.get():
                if event.type == pygame.QUIT or \
                        event.type == pygame.KEYDOWN and event.key == pygame.K_x:
                    print(fps_total / fps_count)
                    pygame.quit()
                    quit()

            current_time = time.time()
            elapsed = current_time - last_update_time
            last_update_time = current_time
            total_time += elapsed
            self.update(elapsed)

            self.draw()

            pygame.display.update()

            self.clock.tick(60)
            fps_total += self.clock.get_fps()
            fps_count += 1

        print(fps_total / fps_count)


if __name__ == '__main__':
    MainScene().run()
