import pygame
import time
import math
import random

METHOD_NAMES = [
    "Random Pair of Circle Points",
    "Random Point in Circle",
    "Random Point Along Radial Line"
]

TIME_PER_LINE = .01

# Dimensions
SCREEN_WIDTH = 1080
SCREEN_HEIGHT = 720
BORDER = 20
CIRCLE_RADIUS = (SCREEN_HEIGHT - 2 * BORDER) // 2
CIRCLE_CENTER = (BORDER + CIRCLE_RADIUS, BORDER + CIRCLE_RADIUS)
FRACTION_BAR_WIDTH = 3
FRACTION_BORDER = 5

# Colors
grey = lambda n: (n, n, n)
BLACK = grey(0)
WHITE = grey(255)
BLUE = (105, 187, 214)  # Totally stolen from 3B1B. It looks nice though

# Font
pygame.font.init()
DISPLAY_FONT = pygame.font.SysFont("Arial", 50, bold=True)


# For drawing rounded rectangles
def round_rect(surface, rect, color, rad=20, border=0, inside=(0, 0, 0, 0)):
    """
    Draw a rect with rounded corners to surface.  Argument rad can be specified
    to adjust curvature of edges (given in pixels).  An optional border
    width can also be supplied; if not provided the rect will be filled.
    Both the color and optional interior color (the inside argument) support
    alpha.
    """

    def render_region_(image, rect, color, rad):
        """Helper function for round_rect."""
        corners = rect.inflate(-2 * rad, -2 * rad)
        for attribute in ("topleft", "topright", "bottomleft", "bottomright"):
            pygame.draw.circle(image, color, getattr(corners, attribute), rad)
        image.fill(color, rect.inflate(-2 * rad, 0))
        image.fill(color, rect.inflate(0, -2 * rad))

    rect = pygame.Rect(rect)
    zeroed_rect = rect.copy()
    zeroed_rect.topleft = 0, 0
    image = pygame.Surface(rect.size).convert_alpha()
    image.fill((0, 0, 0, 0))
    render_region_(image, zeroed_rect, color, rad)
    if border:
        zeroed_rect.inflate_ip(-2 * border, -2 * border)
        render_region_(image, zeroed_rect, inside, rad)
    surface.blit(image, rect)


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


def pair_method():
    a1 = random.uniform(0, 2 * math.pi)
    a2 = random.uniform(0, 2 * math.pi)

    x1 = math.sin(a1)
    y1 = math.cos(a1)

    x2 = math.sin(a2)
    y2 = math.cos(a2)

    d = (x1 - x2) ** 2 + (y1 - y2) ** 2  # sqrt(3)^2 = 3

    return (x1, y1), (x2, y2), d > 3  # sqrt(3)^2


def point_in_circle_and_radial_line_helper(rx, ry):

    # there is a line from (0, 0) to (rx, ry)
    # The chord is perpendicular to that
    m_radius_line = (ry - 0) / (rx - 0)
    m_chord = -1 / m_radius_line

    # The chord has slope m_chord and the point (rx, ry)
    # y = mx + b. m is known. Find b
    b = ry - m_chord * rx

    # Find the intersection of the circle and this line
    # system of equations:
    #   x^2 + y^2 = 1
    #   y = mx + b

    # pre-calculate terms for cleanliness
    prod = m_chord * b
    root = math.sqrt(m_chord ** 2 - b ** 2 + 1)
    denom = m_chord ** 2 + 1

    x1 = (-prod + root) / denom
    x2 = (-prod - root) / denom

    # Solve for y
    y1 = m_chord * x1 + b
    y2 = m_chord * x2 + b

    d = (x1 - x2) ** 2 + (y1 - y2) ** 2  # sqrt(3)^2 = 3

    return (x1, y1), (x2, y2), d > 3  # sqrt(3)^2


def point_in_circle_method():
    rx = random.uniform(-1, 1)
    ry = random.uniform(-1, 1)

    while rx ** 2 + ry ** 2 >= 1:
        rx = random.uniform(-1, 1)
        ry = random.uniform(-1, 1)

    return point_in_circle_and_radial_line_helper(rx, ry)


def point_along_radial_method():
    theta = random.uniform(0, 2 * math.pi)
    r = random.uniform(0, 1)

    rx = r * math.cos(theta)
    ry = r * math.sin(theta)

    return point_in_circle_and_radial_line_helper(rx, ry)


def draw_transparent_lines(surface, colors, color_indices, p1s, p2s, w, transparency):
    trans_surface = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
    trans_surface.fill(BLACK + (0, ))

    for p1, p2, color_index in zip(p1s, p2s, color_indices):
        pygame.draw.line(trans_surface, colors[color_index] + (transparency,), p1, p2, w)
        # pygame.draw.line(surface, colors[color_index], p1, p2, w)

    surface.blit(trans_surface, (0, 0))


class Button:
    STANDARD_COLOR = grey(50)
    HOVER_COLOR = grey(100)
    ACTIVE_COLOR = grey(175)

    def __init__(self, msg, rect, initially_active=False):
        self.rect = rect
        self.active = initially_active

        self.text_data = arrange_text(
            msg,
            rect.x + rect.w // 2,
            rect.y + rect.h // 2,
            placement="center",
            width=rect.w * .95,
            height=rect.h * .8,
            color=WHITE
        )

        self.clicked = False

    def draw(self, surface):
        if self.active:
            fill_color = Button.ACTIVE_COLOR
        elif self.on_button(pygame.mouse.get_pos()):
            fill_color = Button.HOVER_COLOR
        else:
            fill_color = Button.STANDARD_COLOR

        round_rect(surface, self.rect, fill_color)
        round_rect(surface, self.rect, WHITE, border=2)

        surface.blit(self.text_data.surface, self.text_data.rect)

    def on_button(self, pos):
        return self.rect.collidepoint(pos)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.on_button(event.pos):
                self.clicked = True


class MainScene:
    BACKGROUND_COLOR = grey(25)

    def __init__(self):
        self.surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

        self.method_index = 0

        self.methods = [
            pair_method,
            point_in_circle_method,
            point_along_radial_method
        ]

        x = (BORDER + CIRCLE_RADIUS) * 2
        y = BORDER
        w = SCREEN_WIDTH - BORDER - x
        h = (SCREEN_HEIGHT - BORDER * 5) // (3 + 3)  # 3 buttons and the formula area

        self.text_height = h / 2

        self.buttons = [
            Button(METHOD_NAMES[i], pygame.Rect(x, y + (h + BORDER) * i, w, h))
            for i in range(3)
        ]
        self.buttons[self.method_index].active = True

        self.circle_surface = None
        self.reset_circle()

        self.valid_count = 0
        self.invalid_count = 0

        self.total_elapsed_time = -1

    def reset_circle(self):
        size = CIRCLE_RADIUS * 2 + BORDER * 2
        self.circle_surface = pygame.Surface((size, size))
        self.circle_surface.set_colorkey(BLACK)

        self.circle_surface.fill(MainScene.BACKGROUND_COLOR)

        pygame.draw.circle(
            self.circle_surface,
            BLACK,
            (
                BORDER + CIRCLE_RADIUS,
                BORDER + CIRCLE_RADIUS,
            ),
            CIRCLE_RADIUS
        )
        pygame.draw.circle(
            self.circle_surface,
            grey(200),
            (
                BORDER + CIRCLE_RADIUS,
                BORDER + CIRCLE_RADIUS,
            ),
            CIRCLE_RADIUS + 3,
            3
        )

    def handle_event(self, event):
        for button in self.buttons:
            button.handle_event(event)

        for i, button in enumerate(self.buttons):
            if i == self.method_index:
                button.clicked = False
                continue
            if button.clicked:
                for b in self.buttons:
                    b.clicked = False
                    b.active = False
                self.buttons[i].active = True
                self.method_index = i
                self.reset_circle()
                self.valid_count = 0
                self.invalid_count = 0
                self.total_elapsed_time = -.5
                break

    def update(self, elapsed):
        p1s = []
        p2s = []
        color_indices = []
        colors = [BLUE, WHITE]

        self.total_elapsed_time += elapsed
        while self.total_elapsed_time > TIME_PER_LINE:
            self.total_elapsed_time -= TIME_PER_LINE

            data = self.methods[self.method_index]()

            (x1, y1), (x2, y2), valid = data

            p1s.append(
                (
                    (BORDER + CIRCLE_RADIUS) + (x1 * CIRCLE_RADIUS),  # center + dx
                    (BORDER + CIRCLE_RADIUS) + (y1 * CIRCLE_RADIUS),  # center + dy
                )
            )

            p2s.append(
                (
                    (BORDER + CIRCLE_RADIUS) + (x2 * CIRCLE_RADIUS),  # center + dx
                    (BORDER + CIRCLE_RADIUS) + (y2 * CIRCLE_RADIUS),  # center + dy
                )
            )

            if valid:
                color_indices.append(0)
                self.valid_count += 1
            else:
                color_indices.append(1)
                self.invalid_count += 1

        if len(p1s) > 0:
            draw_transparent_lines(self.circle_surface, colors, color_indices, p1s, p2s, 1, 127)

    def draw_formula(self):
        if self.invalid_count + self.valid_count == 0:
            return

        w = SCREEN_WIDTH - BORDER - (BORDER + CIRCLE_RADIUS) * 2
        y = self.buttons[-1].rect.y + self.buttons[-1].rect.h + BORDER
        h = SCREEN_HEIGHT - y - BORDER
        center_y = y + h / 2
        center_x = (BORDER + CIRCLE_RADIUS) + SCREEN_WIDTH / 2
        numerator = arrange_text(
            str(self.valid_count),
            center_x,
            center_y - self.text_height - FRACTION_BORDER * 2 - FRACTION_BAR_WIDTH,
            placement="midbottom",
            width=w,
            height=self.text_height,
            color=BLUE
        )

        denominator_a = arrange_text(
            str(self.valid_count),
            center_x,
            center_y - self.text_height,
            placement="midtop",
            width=w,
            height=self.text_height,
            color=BLUE
        )

        denominator_b = arrange_text(
            f" + {self.invalid_count}",
            center_x,
            center_y - self.text_height,
            placement="midtop",
            width=w,
            height=self.text_height,
            color=WHITE
        )

        denominator = pygame.Surface((denominator_a.rect.w + denominator_b.rect.w, self.text_height))
        denominator.set_colorkey(BLACK)
        denominator.blit(denominator_a.surface, (0, 0))
        denominator.blit(denominator_b.surface, (denominator.get_width() - denominator_b.rect.w, 0))

        den_rect = denominator.get_rect()
        den_rect.midtop = (center_x, center_y - self.text_height)

        pygame.draw.line(
            self.surface,
            WHITE,
            (
                center_x - den_rect.w / 2,
                center_y - self.text_height - FRACTION_BORDER
            ),
            (
                center_x + den_rect.w / 2,
                center_y - self.text_height - FRACTION_BORDER
            ),
            FRACTION_BAR_WIDTH
        )

        result_val = self.valid_count / (self.valid_count + self.invalid_count)
        result_str = '{:.6f}'.format(result_val)

        result = arrange_text(
            f"= {result_str}",
            center_x,
            center_y + self.text_height,
            placement="midbottom",
            width=w,
            height=self.text_height,
            color=WHITE
        )

        self.surface.blit(numerator.surface, numerator.rect)
        self.surface.blit(denominator, den_rect)
        self.surface.blit(result.surface, result.rect)

    def draw(self):
        self.surface.fill(MainScene.BACKGROUND_COLOR)
        self.surface.blit(self.circle_surface, (0, 0))

        for button in self.buttons:
            button.draw(self.surface)

        self.draw_formula()

    def run(self):

        last_update_time = time.time()
        paused = True

        while True:

            ##############
            # Updating
            ##############

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_x:
                        pygame.quit()
                        quit()
                    if event.key == pygame.K_p:
                        paused = not paused
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_event(event)

            current_time = time.time()
            elapsed = current_time - last_update_time
            last_update_time = current_time

            if not paused:
                self.update(elapsed)

            #############
            # Drawing
            #############

            self.draw()

            pygame.display.update()


if __name__ == "__main__":
    MainScene().run()
