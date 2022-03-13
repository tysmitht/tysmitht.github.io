import pygame
import random
import time
import os
import matplotlib.pyplot as plt
import json

# More ideas
#     https://www.geeksforgeeks.org/sorting-algorithms/
ALGORITHMS = [
    "Quick",
    "Merge",
    "Insertion",
    "Selection",
    "Tim",
    "Bubble",
    "Odd-Even",
    "Shell",
    "Cycle",
    "Comb",
    "Shaker",
    "Gnome"
]

TEMP_FILE = os.path.dirname(__file__) + "/Temp.png"
JSON_FILE = os.path.dirname(__file__) + "/data.json"

# Dimensions
SCREEN_WIDTH = 1080
SCREEN_HEIGHT = 720
BORDER = 20

ARRAY_SIZE = 1024
FINISHED_QUIT_DELAY = 1
SHUFFLE_TIME = 1
SORT_TIME = 10


# Colors
def grey(n):
    return (n, n, n)


Red = (220, 17, 33)
Yellow = (247, 210, 30)
Green = (48, 194, 10)


def tween(a, b, t):
    return a * (1 - t) + b * t


def red_green_gradient(t):
    if t <= .5:
        color_a = Red
        color_b = Yellow
        t *= 2
    else:
        color_a = Yellow
        color_b = Green
        t -= .5
        t *= 2

    new_color = tuple([
        tween(color_a[i], color_b[i], t)
        for i in range(len(color_a))
    ])

    return new_color


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
        "outline_color": (255, 255, 255)
    }

    args.update(kwargs)

    valid_placements = {"topleft", "bottomleft", "topright", "bottomright",
                        "midtop", "midleft", "midbottom", "midright", "center"}
    if args["placement"] not in valid_placements:
        raise ValueError(f"{args['placement']} is not a valid placement.")

    if args["font"] is None:
        global TEXT_FONT
        if "TEXT_FONT" not in globals():
            pygame.font.init()
            TEXT_FONT = pygame.font.SysFont("Arial", 250)
        args["font"] = TEXT_FONT

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


def swap(arr, i, j):
    if not (0 <= i < len(arr)) or not (0 <= j < len(arr)):
        raise IndexError

    temp = arr[i]
    arr[i] = arr[j]
    arr[j] = temp


def shuffle_ops(arr):
    operations = []
    for i in reversed(range(len(arr))):
        j = random.randint(0, i)
        operations.append(("s", i, j))
        swap(arr, i, j)
    return operations


def sorted_ops(arr):
    operations = []
    for i in range(len(arr) - 1):
        if arr[i] > arr[i + 1]:
            raise ValueError
    return operations


def quick_ops(arr):
    operations = []

    def partition_(arr, low, high):
        i = low - 1
        for j in range(low, high):
            if arr[j] < arr[high]:
                i += 1
                operations.append(("s", i, j))
                swap(arr, i, j)
        operations.append(("s", i + 1, high))
        swap(arr, i + 1, high)
        return i + 1

    def quick_sort_(arr, low, high):
        if low < high:
            pi = partition_(arr, low, high)

            quick_sort_(arr, low, pi - 1)
            quick_sort_(arr, pi + 1, high)

    quick_sort_(arr, 0, len(arr) - 1)
    return operations


def merge_ops(arr):
    operations = []

    def merge_sort_(arr, l, r):
        if l < r:
            m = int(l + (r - l) / 2)
            merge_sort_(arr, l, m)
            merge_sort_(arr, m + 1, r)
            merge_(arr, l, m, r)

    def merge_(arr, l, m, r):
        n1 = m - l + 1
        n2 = r - m

        L = [None for _ in range(n1)]
        R = [None for _ in range(n2)]

        # Copy data into temp arrays
        for i in range(n1):
            L[i] = arr[l + i]
        for j in range(n2):
            R[j] = arr[m + 1 + j]

        i = 0
        j = 0
        k = l
        while i < n1 and j < n2:
            if L[i] <= R[j]:
                operations.append(("w", L[i], k))
                arr[k] = L[i]
                i += 1
            else:
                operations.append(("w", R[j], k))
                arr[k] = R[j]
                j += 1
            k += 1

        while i < n1:
            operations.append(("w", L[i], k))
            arr[k] = L[i]
            i += 1
            k += 1

        while j < n2:
            operations.append(("w", R[j], k))
            arr[k] = R[j]
            j += 1
            k += 1

    merge_sort_(arr, 0, len(arr) - 1)
    return operations


def insertion_ops(arr):
    operations = []
    for i in range(1, len(arr)):
        j = i - 1
        while j >= 0 and arr[i] < arr[j]:
            operations.append(("s", i, j))
            swap(arr, i, j)
            i = j

            j -= 1

    return operations


def selection_ops(arr):
    operations = []
    for i in range(len(arr)):
        min_index = i
        for j in range(i + 1, len(arr)):
            if arr[j] < arr[min_index]:
                min_index = j

        operations.append(("s", i, min_index))
        swap(arr, min_index, i)

    return operations


def tim_ops(arr):
    operations = []

    def insertion_sort_(arr, left, right):
        for i in range(left + 1, right + 1):
            temp = arr[i]
            j = i - 1
            while j >= left and arr[j] > temp:
                operations.append(("w", arr[j], j + 1))
                arr[j + 1] = arr[j]
                j -= 1

            operations.append(("w", arr[i], j + 1))
            arr[j + 1] = temp

    def merge_(arr, l, m, r):
        n1 = m - l + 1
        n2 = r - m

        L = [None for _ in range(n1)]
        R = [None for _ in range(n2)]

        # Copy data into temp arrays
        for i in range(n1):
            L[i] = arr[l + i]
        for j in range(n2):
            R[j] = arr[m + 1 + j]

        i = 0
        j = 0
        k = l
        while i < n1 and j < n2:
            if L[i] <= R[j]:
                operations.append(("w", L[i], k))
                arr[k] = L[i]
                i += 1
            else:
                operations.append(("w", R[j], k))
                arr[k] = R[j]
                j += 1
            k += 1

        while i < n1:
            operations.append(("w", L[i], k))
            arr[k] = L[i]
            i += 1
            k += 1

        while j < n2:
            operations.append(("w", R[j], k))
            arr[k] = R[j]
            j += 1
            k += 1

    for i in range(0, len(arr), 32):
        insertion_sort_(arr, i, min(i + 32 - 1, len(arr) - 1))

    size = 32
    while size < len(arr):
        left = 0
        while left < len(arr):
            mid = left + size - 1
            right = min(left + 2 * size - 1, len(arr) - 1)

            if mid < right:
                merge_(arr, left, mid, right)

            left += 2 * size

        size *= 2

    return operations


def bubble_ops(arr):
    operations = []
    for i in range(len(arr)):
        for j in range(len(arr) - i - 1):
            if arr[j] > arr[j + 1]:
                operations.append(("s", j, j + 1))
                swap(arr, j, j + 1)
    return operations


def odd_even_ops(arr):
    operations = []
    is_sorted = False
    while not is_sorted:
        is_sorted = True

        for i in range(1, len(arr) - 1, 2):
            if arr[i] > arr[i + 1]:
                operations.append(("s", i, i + 1))
                swap(arr, i, i + 1)
                is_sorted = False

        for i in range(0, len(arr) - 1, 2):
            if arr[i] > arr[i + 1]:
                operations.append(("s", i, i + 1))
                swap(arr, i, i + 1)
                is_sorted = False

    return operations


def shell_ops(arr):
    operations = []

    gap = len(arr) // 2
    while gap > 0:
        for i in range(gap, len(arr)):
            temp = arr[i]

            j = i
            while j >= gap and arr[j - gap] > temp:
                operations.append(("w", arr[j - gap], j))
                arr[j] = arr[j - gap]
                j -= gap

            operations.append(("w", temp, j))
            arr[j] = temp

        gap //= 2

    return operations


def cycle_ops(arr):
    operations = []

    for cycleStart in range(0, len(arr) - 1):
        item = arr[cycleStart]

        # Find where to put the item.
        pos = cycleStart
        for i in range(cycleStart + 1, len(arr)):
            if arr[i] < item:
                pos += 1

        # If the item is already there, this is not a cycle.
        if pos == cycleStart:
            continue

        # Otherwise, put the item there or right after any duplicates.
        while item == arr[pos]:
            pos += 1
        operations.append(("w", item, pos))
        arr[pos], item = item, arr[pos]

        # Rotate the rest of the cycle.
        while pos != cycleStart:

            # Find where to put the item.
            pos = cycleStart
            for i in range(cycleStart + 1, len(arr)):
                if arr[i] < item:
                    pos += 1

            # Put the item there or right after any duplicates.
            while item == arr[pos]:
                pos += 1
            operations.append(("w", item, pos))
            arr[pos], item = item, arr[pos]

    return operations


def comb_ops(arr):
    operations = []

    def get_next_gap_(gap):
        gap = (gap * 10) // 13
        if gap < 1:
            return 1
        return gap

    gap = len(arr)
    swapped = True

    while gap != 1 or swapped:
        gap = get_next_gap_(gap)
        swapped = False

        for i in range(len(arr) - gap):
            if arr[i] > arr[i + gap]:
                operations.append(("s", i, i + gap))
                swap(arr, i, i + gap)
                swapped = True

    return operations


def shaker_ops(arr):
    operations = []

    swapped = True
    start = 0
    end = len(arr) - 1
    while swapped:
        swapped = False

        for i in range(start, end):
            if arr[i] > arr[i + 1]:
                operations.append(("s", i, i + 1))
                swap(arr, i, i + 1)
                swapped = True

        if not swapped:
            break

        swapped = False

        end -= 1
        for i in range(end - 1, start - 1, -1):
            if arr[i] > arr[i + 1]:
                operations.append(("s", i, i + 1))
                swap(arr, i, i + 1)
                swapped = True

        start += 1

    return operations


def gnome_ops(arr):
    operations = []
    i = 0
    while True:
        # If there is no previous pot
        if i == 0:
            i += 1
        # If there is no next pot
        elif i == len(arr) - 1:
            break
        # There is a pair of pots to compare
        else:
            if arr[i - 1] <= arr[i]:
                i += 1
            else:
                operations.append(("s", i, i - 1))
                swap(arr, i, i - 1)
                i -= 1
    return operations


class Button:
    DEFAULT_STANDARD_COLOR = grey(175)
    DEFAULT_HOVER_COLOR = grey(200)
    BORDER = 5

    def __init__(self, id, msg, rect, scene, standard_color=None,
                 hover_color=None, func=None, rounded=True, height_ratio=1 / 4):
        self.id = id
        self.rect = rect
        self.scene = scene

        if standard_color is None:
            self.standardColor = Button.DEFAULT_STANDARD_COLOR
        else:
            self.standardColor = standard_color
        if hover_color is None:
            self.hoverColor = Button.DEFAULT_HOVER_COLOR
        else:
            self.hoverColor = hover_color

        self.rounded = rounded

        self.text = arrange_text(
            msg,
            self.rect.x + self.rect.w // 2,
            self.rect.y + self.rect.h // 2,
            width=self.rect.w,
            height=self.rect.h * height_ratio,
            placement="center"
        )

        self.func = func

    def on_button(self, pos):
        return self.rect.collidepoint(pos)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.on_button(event.pos):
                self.func(self.scene, self.id)

    def draw(self, surface):
        color = self.standardColor
        if self.on_button(pygame.mouse.get_pos()):
            color = self.hoverColor

        if self.rounded:
            round_rect(surface, self.rect, color)
            round_rect(surface, self.rect, grey(0), border=Button.BORDER)
        else:
            pygame.draw.rect(surface, color, self.rect)
            pygame.draw.rect(surface, grey(0), self.rect, Button.BORDER)

        surface.blit(
            self.text.surface,
            self.text.rect
        )


class BaseScene:
    def __init__(self, surface, clock):
        self.surface = surface
        self.clock = clock
        self.done = False

    def handle_event(self, event):
        pass

    def update(self, elapsed):
        pass

    def draw(self):
        pass

    def run(self):

        last_update_time = time.time()
        while True:

            for event in pygame.event.get():
                if event.type == pygame.QUIT or \
                        event.type == pygame.KEYDOWN and event.key == pygame.K_x:
                    pygame.quit()
                    quit()

                self.handle_event(event)

            self.clock.tick(60)

            current_time = time.time()
            elapsed = current_time - last_update_time
            last_update_time = current_time
            self.update(elapsed)

            if self.done:
                return

            self.draw()

            pygame.display.update()


class AnimScene(BaseScene):
    def __init__(self, surface, clock, array, ops, op_delay):
        super().__init__(surface, clock)

        self.array = array

        self.ops = ops
        self.op_step = 0
        self.op_timer = .25
        self.op_delay = op_delay

        self.quit = False
        self.quit_timer = FINISHED_QUIT_DELAY

        self.channel_number = 0

    def update(self, elapsed):
        self.op_timer -= elapsed
        while self.op_timer < 0:
            self.op_timer += self.op_delay

            if self.op_step < len(self.ops):
                # Do the next operation
                next_op = self.ops[self.op_step]

                # Swap
                if next_op[0] == "s":
                    swap(self.array, next_op[1], next_op[2])
                elif next_op[0] == "w":
                    self.array[next_op[2]] = next_op[1]

                self.op_step += 1

        if self.op_step >= len(self.ops):
            self.quit_timer -= elapsed
            if self.quit_timer < 0:
                self.done = True

    def draw(self):
        self.surface.fill(grey(150))

        for i, y in enumerate(self.array):
            pygame.draw.line(
                self.surface,
                red_green_gradient(y / ARRAY_SIZE),
                (
                    BORDER + i,
                    SCREEN_HEIGHT - BORDER
                ),
                (
                    BORDER + i,
                    round(SCREEN_HEIGHT - BORDER - y * 2 / 3)
                ),
                1
            )


class MainScene(BaseScene):
    def __init__(self, surface, clock):
        super().__init__(surface, clock)

        self.buttons = []
        self.idAlgoMap = dict()
        w = (SCREEN_WIDTH - BORDER * 5) / 4
        h = (SCREEN_HEIGHT - BORDER * 4) / 3
        for i, algo in enumerate(ALGORITHMS):
            r = i // 4
            c = i % 4
            x = BORDER + (w + BORDER) * c
            y = BORDER + (h + BORDER) * r
            self.buttons.append(
                Button(
                    i,
                    algo,
                    pygame.Rect(x, y, w, h),
                    self,
                    func=MainScene.run_algorithm
                )
            )

        i += 1
        r = i // 4
        c = i % 4
        x = BORDER + (w + BORDER) * c
        y = BORDER + (h + BORDER) * r
        self.buttons.append(
            Button(
                i,
                "Tests",
                pygame.Rect(x, y, w, h),
                self,
                func=MainScene.run_tests
            )
        )

    def run_algorithm(self, id):
        print("ID:", id)
        print("\tAlgo:", ALGORITHMS[id])

        # Shuffle
        arr = list(range(0, ARRAY_SIZE))
        ops = shuffle_ops(arr[::])
        AnimScene(self.surface, self.clock, arr, ops, SHUFFLE_TIME / len(ops)).run()

        # Do the sorting
        if ALGORITHMS[id] == "Quick":
            ops = quick_ops(arr[::])
        elif ALGORITHMS[id] == "Merge":
            ops = merge_ops(arr[::])
        elif ALGORITHMS[id] == "Insertion":
            ops = insertion_ops(arr[::])
        elif ALGORITHMS[id] == "Selection":
            ops = selection_ops(arr[::])
        elif ALGORITHMS[id] == "Tim":
            ops = tim_ops(arr[::])
        elif ALGORITHMS[id] == "Bubble":
            ops = bubble_ops(arr[::])
        elif ALGORITHMS[id] == "Odd-Even":
            ops = odd_even_ops(arr[::])
        elif ALGORITHMS[id] == "Shell":
            ops = shell_ops(arr[::])
        elif ALGORITHMS[id] == "Cycle":
            ops = cycle_ops(arr[::])
        elif ALGORITHMS[id] == "Comb":
            ops = comb_ops(arr[::])
        elif ALGORITHMS[id] == "Shaker":
            ops = shaker_ops(arr[::])
        elif ALGORITHMS[id] == "Gnome":
            ops = gnome_ops(arr[::])
        else:
            raise ValueError

        AnimScene(self.surface, self.clock, arr, ops, SORT_TIME / len(ops)).run()

    def run_tests(self, id):
        TestScene(self.surface, self.clock).run()

    def handle_event(self, event):
        for b in self.buttons:
            b.handle_event(event)

    def draw(self):
        self.surface.fill(grey(150))

        for b in self.buttons:
            b.draw(self.surface)


if __name__ == "__main__":
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    MainScene(screen, clock).run()