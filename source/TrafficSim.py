"""
Simulation of a traffic jam.
Numerical representation of a real-life phenomenon.

Chaotic system. Tweaking any of the constants can make it not work
"""

import pygame
from pygame import gfxdraw
import math
import time
import random
import fractions
import numba as nb
import numpy as np

# Dimensions
SCREEN_WIDTH = 1080
SCREEN_HEIGHT = 480
BORDER = 20

ROAD_RADIUS = round(SCREEN_HEIGHT * .75 / 2)
ROAD_WIDTH = 20
CAR_RADIUS = 12
SAFE_CAR_GAP = math.pi / 16
SPEEDUP_DELAY = 1
SPEED_LIMIT = math.pi / 4

FPS = 60
UPS = 1000
UPDATE_TIME = 1 / UPS
GRAPH_TIME_RANGE = 10


# Colors
def grey(n):
    return n, n, n


CAR_COLORS = [
    (255, 0, 0),
    (255, 139, 0),
    (232, 255, 0),
    (93, 255, 0),
    (0, 255, 46),
    (0, 255, 185),
    (0, 185, 255),
    (0, 46, 255),
    (93, 0, 255),
    (232, 0, 255),
    (255, 0, 139),
]
CAR_GAP_GOAL = 2 * math.pi / len(CAR_COLORS)


def convert_float_to_pi_multiple_string(f):
    """
    Args:
        f: a floating point number

    Returns: aπ/b

    Not guaranteed to be 100% accurate by the nature of rational numbers
    """
    f /= math.pi
    frac = fractions.Fraction(f).limit_denominator(1000)
    num = frac.numerator
    den = frac.denominator

    if num != 1 and den != 1:
        return f"{frac.numerator}π/{frac.denominator}"
    elif num == 1 and den != 1:
        return f"π/{frac.denominator}"
    elif num == 1 and den == 1:
        return "π"
    elif num != 1 and den == 1:
        return f"{frac.numerator}π"


def ceil_next_multiple_2(f):
    f = math.ceil(f)

    # f is an integer. Maybe odd, maybe even
    # Notice f & 1 == 1 if f is odd, 0 otherwise
    # if f is even: f + f & 1 == f + 0 is even
    # if f is odd: f + f & 1 == f + 1 is even
    return f + (f & 1)


def pin_value(f, mini, maxi):
    # Ensure mini <= maxi
    if mini > maxi:
        maxi, mini = mini, maxi

    if f <= mini:
        return mini
    elif f >= maxi:
        return maxi
    else:
        return f


def draw_arc(surface, center, radius, start_angle, stop_angle, color, width=1):
    # Convert from Vector2 to tuple
    center = (round(center.x), round(center.y))

    if start_angle == stop_angle:
        return

    start_angle = round(start_angle % 360)
    stop_angle = round(stop_angle % 360)

    for dy in [-1, 1]:
        for dx in [-1, -1, 1]:
            x, y = center
            x += dx
            y += dy
            for r in range(radius - width // 2, radius + width // 2):
                if start_angle == stop_angle:
                    gfxdraw.circle(surface, x, y, r, color)
                else:
                    gfxdraw.arc(surface, x, y, r, start_angle, stop_angle, color)


def arrange_text(text: str, x: float, y: float, **kwargs):
    """
    Wrapper function for creating and arranging text surfaces
    Args:
        text: The text to display

        x: X position of the text's placement

        y: Y position of the text's placement

        **kwargs:
            width: Max width allowed. Default: None, no restriction

            height: Max height allowed. Default: None, no restriction

            placement: Placement of the the text relative to the position. Default: topleft
            color: Font color. Default: Black
            angle: Degrees of rotation. Default: 0, no rotation
            font: SysFont to use for rendering. Default: Arial
            outline_width: How wide the text outline should be. Default: -1, no outline
            outline_color: What color the outline will be. Default: White

    Returns:
        TextSurface struct which contains the surface and its rect
    """

    class TextSurface:
        def __init__(self, s, r):
            self.surface = s
            self.rect = r

    def scale_text(surface, args):
        scale = 1
        if args["height"] is not None:
            scale = min(args["height"] / surface.get_height(), scale)
        if args["width"] is not None:
            scale = min(args["width"] / surface.get_width(), scale)

        surface = pygame.transform.scale(
            surface,
            (
                round(surface.get_width() * scale),
                round(surface.get_height() * scale)
            )
        )
        return surface

    def render_with_border_(text, args):
        def circle_points_(r):
            r = round(r)
            x, y, e = r, 0, 1 - r
            points = []
            while x >= y:
                points.append((x, y))
                y += 1
                if e < 0:
                    e += 2 * y - 1
                else:
                    x -= 1
                    e += 2 * (y - x) - 1
            points += [(y, x) for x, y in points if x > y]
            points += [(-x, y) for x, y in points if x]
            points += [(x, -y) for x, y in points if y]
            points.sort()
            return points

        text_surface = scale_text(args["font"].render(text, True, args["color"]).convert_alpha(), args)
        w = text_surface.get_width() + 2 * args["outline_width"]
        h = args["font"].get_height()

        osurf = pygame.Surface((w, h + 2 * args["outline_width"])).convert_alpha()
        osurf.fill((0, 0, 0, 0))

        surf = osurf.copy()

        osurf.blit(scale_text(args["font"].render(text, True, args["outline_color"]).convert_alpha(), args), (0, 0))

        for dx, dy in circle_points_(args["outline_width"]):
            surf.blit(osurf, (dx + args["outline_width"], dy + args["outline_width"]))

        surf.blit(text_surface, (args["outline_width"], args["outline_width"]))
        return surf

    args = {
        "width": None,
        "height": None,
        "placement": "topleft",
        "color": (0, 0, 0),
        "angle": 0,
        "font": None,
        "outline_width": -1,
        "outline_color": (255, 255, 255),
        "bold": False,
        "italic": False
    }

    args.update(kwargs)

    valid_placements = {"topleft", "bottomleft", "topright", "bottomright",
                        "midtop", "midleft", "midbottom", "midright", "center"}
    if args["placement"] not in valid_placements:
        raise ValueError(f"{args['placement']} is not a valid placement.")

    if args["font"] is None:
        if not args["bold"] and not args["italic"]:
            global TEXT_FONT
            if "TEXT_FONT" not in globals():
                pygame.font.init()
                TEXT_FONT = pygame.font.SysFont("Arial", 250)
            args["font"] = TEXT_FONT
        elif not args["bold"] and args["italic"]:
            global TEXT_FONT_ITALIC
            if "TEXT_FONT_ITALIC" not in globals():
                pygame.font.init()
                TEXT_FONT_ITALIC = pygame.font.SysFont("Arial", 250, italic=True)
            args["font"] = TEXT_FONT_ITALIC
        elif args["bold"] and not args["italic"]:
            global TEXT_FONT_BOLD
            if "TEXT_FONT_BOLD" not in globals():
                pygame.font.init()
                TEXT_FONT_BOLD = pygame.font.SysFont("Arial", 250, bold=True)
            args["font"] = TEXT_FONT_BOLD
        elif args["bold"] and args["italic"]:
            global TEXT_FONT_BOLD_ITALIC
            if "TEXT_FONT_BOLD_ITALIC" not in globals():
                pygame.font.init()
                TEXT_FONT_BOLD_ITALIC = pygame.font.SysFont("Arial", 250, bold=True, italic=True)
            args["font"] = TEXT_FONT_BOLD_ITALIC

    # Create the text
    # No border
    if args["outline_width"] <= 0:
        surface = scale_text(args["font"].render(text, True, args["color"]).convert_alpha(), args)
    # An outline is requested
    else:
        surface = render_with_border_(text, args)

    # Rotate the image
    surface = pygame.transform.rotate(
        surface,
        args["angle"]
    )

    # Position the text
    rect = surface.get_rect()
    setattr(rect, args["placement"], (round(x), round(y)))

    return TextSurface(surface, rect)


class HalfCircleButton:
    BORDER_WIDTH = 3
    BORDER_COLOR = (0, 0, 0)
    BACKGROUND_COLOR = (175, 175, 175)
    HOVER_COLOR = (200, 200, 200)
    LINE_WIDTH = 3

    def __init__(self, center, radius, scene, func, msg, half):
        self.center = center
        self.radius = radius
        self.circle_half = half

        self.scene = scene
        self.func = func

        self.surfaces = dict()

        self.text = None
        self.generate_base_surfaces(msg)

    def generate_base_surfaces(self, msg):
        # if self.on_button(pygame.mouse.get_pos()):
        #     back_color = HalfCircleButton.HOVER_COLOR
        # else:
        #     back_color = HalfCircleButton.BACKGROUND_COLOR

        text = arrange_text(
            msg,
            self.radius,
            self.radius + (5 if self.circle_half == "bottom" else -5),
            width=self.radius,
            height=self.radius / 2,
            placement="midtop" if self.circle_half == "bottom" else "midbottom"
        )

        for label, color in [("hover", HalfCircleButton.HOVER_COLOR), ("no-hover", HalfCircleButton.BACKGROUND_COLOR)]:
            transparent_color = (255, 127, 127)
            surf = pygame.Surface((self.radius * 2, self.radius * 2))
            surf.set_colorkey(transparent_color)
            surf.fill(transparent_color)

            # Draw the circle
            pygame.draw.circle(
                surf,
                color,
                (self.radius, self.radius),
                self.radius
            )
            pygame.draw.circle(
                surf,
                HalfCircleButton.BORDER_COLOR,
                (self.radius, self.radius),
                self.radius,
                HalfCircleButton.BORDER_WIDTH
            )

            # Remove the unneeded sections of the surface
            if self.circle_half == "bottom":
                pygame.draw.rect(
                    surf,
                    transparent_color,
                    (
                        -10,
                        0,
                        self.radius * 2 + 20,
                        self.radius
                    )
                )
            else:
                pygame.draw.rect(
                    surf,
                    transparent_color,
                    (
                        -10,
                        self.radius,
                        self.radius * 2 + 20,
                        self.radius + 10
                    )
                )

            # Draw the line at the center
            pygame.draw.line(
                surf,
                HalfCircleButton.BORDER_COLOR,
                (0, self.radius),
                (self.radius * 2, self.radius),
                HalfCircleButton.BORDER_WIDTH,
            )
            surf.blit(text.surface, text.rect)

            self.surfaces[label] = surf

    def set_text(self, msg):
        self.generate_base_surfaces(msg)

    def on_button(self, pos):
        if (pos[0] - self.center.x) ** 2 + (pos[1] - self.center.y) ** 2 > self.radius ** 2:
            return False

        if self.circle_half == "bottom":
            if pos[1] < self.center.y:
                return False

        else:
            if pos[1] > self.center.y:
                return False

        return True

    def draw(self, surface):
        if self.on_button(pygame.mouse.get_pos()):
            surface.blit(
                self.surfaces["hover"],
                (self.center.x - self.radius, self.center.y - self.radius)
            )
        else:
            surface.blit(
                self.surfaces["no-hover"],
                (self.center.x - self.radius, self.center.y - self.radius)
            )

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.on_button(event.pos):
                self.func(self.scene)


class Graph:
    BORDER_WIDTH = 3
    BORDER_COLOR = (0, 0, 0)
    BACKGROUND_COLOR = (175, 175, 175)
    POPUP_BACKGROUND_COLOR = (150, 150, 150)
    POPUP_TEXT_MAX_SIZE = (100, 100)
    POPUP_BORDER = 10
    AXIS_SPACE = 75
    LINE_COLOR = (100, 100, 100)
    LINE_WIDTH = 3

    def __init__(self, rect):
        self.rect = rect
        self.surface = pygame.Surface((self.rect.w, self.rect.h))
        self.base_surface = pygame.Surface((self.rect.w, self.rect.h))

        self.data = None

        self.num_text = dict()

        self.generate_base_surface()
        self.update_surface()

    def generate_base_surface(self):
        self.base_surface.fill(Graph.BACKGROUND_COLOR)

        pygame.draw.rect(
            self.base_surface,
            Graph.BORDER_COLOR,
            (
                0,
                0,
                round(self.rect.w - 1),
                round(self.rect.h - 1)
            ),
            Graph.LINE_WIDTH
        )

        # Draw the y labels and y semi-axis lines
        for amount in [0, .25, .5, .75, 1]:
            y_val = SPEED_LIMIT * amount
            y_pixel = round((BORDER - self.rect.h + Graph.AXIS_SPACE) * amount + self.rect.h - Graph.AXIS_SPACE)

            pygame.draw.line(
                self.base_surface,
                Graph.LINE_COLOR,
                (Graph.AXIS_SPACE, y_pixel),
                (self.rect.w - BORDER, y_pixel),
                Graph.LINE_WIDTH
            )

            # Skip specific text labels
            if amount in {0, .25, .75}:
                continue

            # Create and blit the text
            text = arrange_text(
                convert_float_to_pi_multiple_string(y_val),
                Graph.AXIS_SPACE - 2,
                y_pixel,
                height=self.rect.h * .075,
                width=Graph.AXIS_SPACE / 2,
                placement="midright"
            )
            self.base_surface.blit(text.surface, text.rect)

        pygame.draw.lines(
            self.base_surface,
            grey(0),
            False,
            [
                (Graph.AXIS_SPACE, self.rect.h - Graph.AXIS_SPACE),
                (self.rect.w - BORDER, self.rect.h - Graph.AXIS_SPACE)
            ],
            Graph.LINE_WIDTH
        )

        # y axis label
        text = arrange_text(
            "Speed (radians)",
            2,
            self.rect.h // 2,
            height=Graph.AXIS_SPACE / 2,
            # width=Graph.AXIS_SPACE / 2,
            angle=90,
            placement="midleft"
        )
        self.base_surface.blit(text.surface, text.rect)

        # x axis label
        text = arrange_text(
            "Time (seconds)",
            self.rect.w // 2,
            self.rect.h - 2,
            height=Graph.AXIS_SPACE / 2,
            placement="midbottom"
        )
        self.base_surface.blit(text.surface, text.rect)

    def reset(self):
        self.__init__(self.rect)

    @staticmethod
    @nb.njit
    def simplify_line_points(line):
        if line.shape[0] < 3:
            return line

        mask = np.zeros(line.shape[0]) == 0  # Initially all true
        for i in range(0, line.shape[0] - 2):
            avg = (line[i, 1] + line[i + 2, 1]) / 2
            if abs(avg - line[i + 1, 1]) < .001:
                mask[i + 1] = False
        return line[mask]

    def add_data(self, when, points, do_update):
        # self.data[0].append(when)
        # self.data[1].append(points)

        if self.data is None:
            self.data = [
                np.array([when]),
                np.array([points])
            ]
        else:
            self.data[0] = np.append(self.data[0], when)
            self.data[1] = np.vstack([self.data[1], points])

        # Remove the older data
        for i in range(len(self.data)):
            if self.data[0][i] >= when - GRAPH_TIME_RANGE:
                break
        self.data[0] = self.data[0][i:]
        self.data[1] = self.data[1][i:]

        if do_update:
            self.update_surface()

    @staticmethod
    @nb.njit
    def update_surface_helper(min_x_val, max_x_val, min_x_pixel, max_x_pixel, w, h, when, speeds, axis_space, lines):
        start_index: int = 0
        for x in range(axis_space, w - BORDER):
            time_needed = ((x - min_x_pixel) / (max_x_pixel - min_x_pixel)) * (
                    max_x_val - min_x_val) + min_x_val
            for i in range(start_index, len(when)):
                start_index = i
                if time_needed <= when[i]:

                    for j, y_val in enumerate(speeds[i]):
                        amount = (y_val - 0) / (SPEED_LIMIT - 0)
                        # y_pixel = round(
                        #     (BORDER - h + axis_space) * amount + h - axis_space
                        # )
                        y_pixel = (BORDER - h + axis_space) * amount + h - axis_space
                        lines[j, x - axis_space, :] = float(x), y_pixel

                    break
        return lines

    def update_surface(self):
        self.surface.blit(self.base_surface, (0, 0))

        # Make sure theres at least some data
        if self.data is None or len(self.data[0]) < 5:
            return

        # Draw the x labels and the x semi-axis line
        min_x_val = self.data[0][0]
        max_x_val = self.data[0][-1]
        min_x_pixel = Graph.AXIS_SPACE
        max_x_pixel = self.rect.w - BORDER

        x_val = ceil_next_multiple_2(min_x_val)
        while x_val < max_x_val:
            x_pixel = round(((x_val - min_x_val) / (max_x_val - min_x_val)) * (max_x_pixel - min_x_pixel) + min_x_pixel)

            pygame.draw.line(
                self.surface,
                Graph.LINE_COLOR,
                (x_pixel, BORDER),
                (x_pixel, self.rect.h - Graph.AXIS_SPACE),
                Graph.LINE_WIDTH
            )

            if x_val in self.num_text:
                text = self.num_text[x_val]
                text.rect.midtop = (x_pixel, self.rect.h - Graph.AXIS_SPACE)
            else:
                text = arrange_text(
                    str(x_val),
                    x_pixel,
                    self.rect.h - Graph.AXIS_SPACE,
                    height=Graph.AXIS_SPACE / 2,
                    placement="midtop"
                )
                self.num_text[x_val] = text

            self.surface.blit(text.surface, text.rect)

            x_val += 2

        pygame.draw.line(
            self.surface,
            grey(0),
            (Graph.AXIS_SPACE, BORDER),
            (Graph.AXIS_SPACE, self.rect.h - Graph.AXIS_SPACE),
            Graph.LINE_WIDTH
        )

        lines = np.empty((len(CAR_COLORS), self.rect.w - Graph.AXIS_SPACE - BORDER, 2), float)

        lines = Graph.update_surface_helper(
            min_x_val, max_x_val, min_x_pixel, max_x_pixel,
            self.rect.w, self.rect.h,
            self.data[0], self.data[1],
            Graph.AXIS_SPACE,
            lines
        )

        for i, line in enumerate(lines):
            pygame.draw.lines(
                self.surface,
                CAR_COLORS[i],
                False,
                Graph.simplify_line_points(line),
                # line,
                Graph.LINE_WIDTH
            )

    def draw(self, surface):
        surface.blit(
            self.surface,
            (
                round(self.rect.x),
                round(self.rect.y)
            )
        )


class Car:
    def __init__(self, color, initial_theta):
        self.color = color

        self.theta = initial_theta
        self.vel = SPEED_LIMIT
        self.accel = 0

        self.new_theta = None
        self.new_vel = None

        self.accel_method_num = 1

    def accel_method_one(self, next_car):
        d1 = abs(next_car.theta - self.theta)
        d2 = abs(2 * math.pi - d1)
        dist = min(d1, d2)
        safe_dist = dist - SAFE_CAR_GAP

        if dist < CAR_GAP_GOAL:
            if safe_dist != 0:
                # Kinematic equation: vf^2 = vi^2 + 2a * deltaX
                self.accel = (0 ** 2 - self.vel ** 2) / (2 * safe_dist)
            else:
                self.accel = 0
        elif dist > CAR_GAP_GOAL:
            self.accel = math.pi / 3
        else:
            self.accel = 0

    def accel_method_two(self, next_car, prev_car):
        nc_d1 = abs(next_car.theta - self.theta)
        nc_d2 = abs(2 * math.pi - nc_d1)
        nc_dist = min(nc_d1, nc_d2)
        nc_safe_dist = nc_dist - SAFE_CAR_GAP

        cp_d1 = abs(self.theta - prev_car.theta)
        cp_d2 = abs(2 * math.pi - cp_d1)
        cp_dist = min(cp_d1, cp_d2)

        if nc_dist < cp_dist:
            if nc_safe_dist != 0:
                # Kinematic equation: vf^2 = vi^2 + 2a * deltaX
                self.accel = (0 ** 2 - self.vel ** 2) / (2 * nc_safe_dist)
            else:
                self.accel = 0
        elif nc_dist > cp_dist:
            self.accel = math.pi / 3
        else:
            self.accel = 0

    def update(self, elapsed, next_car, prev_car):
        if self.accel_method_num == 1:
            self.accel_method_one(next_car)
        else:
            self.accel_method_two(next_car, prev_car)

        self.new_vel = pin_value(self.vel + self.accel * elapsed, 0, SPEED_LIMIT)
        self.new_theta = (self.theta + self.new_vel * elapsed) % (2 * math.pi)

        # self.vel += self.accel * elapsed
        # self.vel = max(self.vel, 0)
        # self.vel = min(self.vel, SPEED_LIMIT)

        # self.theta = (self.theta + self.vel * elapsed) % (2 * math.pi)

    def commit_update(self):
        self.vel = self.new_vel
        self.theta = self.new_theta

    def draw(self, surface, center, radius):
        pygame.draw.circle(
            surface,
            self.color,
            (
                round(center.x + radius * math.cos(self.theta)),
                round(center.y + radius * math.sin(self.theta))
            ),
            CAR_RADIUS
        )


class MainScene:
    BACKGROUND_COLOR = grey(150)

    def __init__(self):
        self.surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.base_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        self.cars = []
        for i, color in enumerate(CAR_COLORS):
            self.cars.append(
                Car(
                    color,
                    i * CAR_GAP_GOAL
                )
            )

        self.loopCenter = pygame.math.Vector2(
            SCREEN_WIDTH - BORDER - ROAD_RADIUS - ROAD_WIDTH,
            round(SCREEN_HEIGHT * .5)
        )

        self.graph = Graph(
            pygame.Rect(
                BORDER,
                BORDER,
                self.loopCenter.x - ROAD_RADIUS - ROAD_WIDTH * 2 - BORDER,
                SCREEN_HEIGHT - BORDER * 2
            )
        )

        self.method_button = HalfCircleButton(
            self.loopCenter,
            ROAD_RADIUS * .7,
            self,
            MainScene.toggle_accel_method,
            "Front",
            "top"
        )

        self.brake_button = HalfCircleButton(
            self.loopCenter,
            ROAD_RADIUS * .7,
            self,
            MainScene.brake,
            "Brake",
            "bottom"
        )

        self.current_time = 0
        self.remaining_update_time = 0
        self.paused = False

        self.generate_base_surface()

    def generate_base_surface(self):
        self.base_surface.fill(MainScene.BACKGROUND_COLOR)

        pygame.draw.circle(
            self.base_surface,
            grey(0),
            self.loopCenter,
            ROAD_RADIUS + ROAD_WIDTH
        )
        pygame.draw.circle(
            self.base_surface,
            MainScene.BACKGROUND_COLOR,
            self.loopCenter,
            ROAD_RADIUS - ROAD_WIDTH
        )

        for i in range(30):
            i *= 2
            draw_arc(
                self.base_surface,
                self.loopCenter,
                ROAD_RADIUS,
                i * 6,
                i * 6 + 6,
                grey(255),
                2
            )

    def brake(self):
        random.choice(self.cars).vel *= .25

    def toggle_accel_method(self):
        if self.cars[0].accel_method_num == 1:
            new_method = 2
            self.method_button.set_text("Center")
        else:
            new_method = 1
            self.method_button.set_text("Front")

        for car in self.cars:
            car.accel_method_num = new_method

    def graph_data_points(self):
        return [car.vel for car in self.cars]

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            # Pause
            if event.key == pygame.K_p:
                self.paused = not self.paused
            # Reset
            if event.key == pygame.K_r:
                self.__init__()

        self.method_button.handle_event(event)
        self.brake_button.handle_event(event)

    def update(self, elapsed):
        self.remaining_update_time += elapsed

        while self.remaining_update_time > UPDATE_TIME:
            self.current_time += UPDATE_TIME

            for i in range(-1, len(self.cars) - 1):
                self.cars[i].update(UPDATE_TIME, self.cars[i + 1], self.cars[i - 1])

            for c in self.cars:
                c.commit_update()

            self.graph.add_data(self.current_time, self.graph_data_points(), False)

            self.remaining_update_time -= UPDATE_TIME

        self.graph.update_surface()

    def draw(self):
        self.surface.blit(self.base_surface, (0, 0))

        for c in self.cars:
            c.draw(
                self.surface,
                self.loopCenter,
                ROAD_RADIUS
            )

        self.graph.draw(self.surface)

        self.method_button.draw(self.surface)
        self.brake_button.draw(self.surface)

    def run(self):

        pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN])

        last_update_time = time.time()

        while True:
            ##############
            # Updating
            ##############

            for event in pygame.event.get():
                if event.type == pygame.QUIT or \
                        (event.type == pygame.KEYDOWN and event.key == pygame.K_x):
                    quit()

                self.handle_event(event)

            # elapsed = 1 / FPS

            current_time = time.time()
            elapsed = current_time - last_update_time
            last_update_time = current_time

            if not self.paused:
                self.update(elapsed)

            #############
            # Drawing
            #############

            self.draw()

            pygame.display.update()

            self.clock.tick(FPS)

if __name__ == "__main__":
    MainScene().run()
