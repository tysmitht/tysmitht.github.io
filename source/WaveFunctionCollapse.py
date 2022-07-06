"""
Wave Function Collapse
author: Tyler Smith
Creation Date: 7/3/2022

Usage:
'python WaveFunctionCollapse.py'
Starts immediately.
Press 'r' to reset the scene.

The code is a bit messier than I
would've liked but the goal was to
reduce as much redundancy as possible.

Broad Overview (in order of execution):

TileMaker: This is really just a module
to contain the functionality for all
tile generation in location.
TileMaker::make is the driver.

AdjacencyMaker: This is a module to determine
which tiles are valid neighbors on each side
of other tiles. This is vital to the algorithm
so one collapsed tile can constrain
its neighbors.
AdjacencyMaker::make is the driver.

CollapseScene: Given the tiles and adjacencies,
run the algorithm. The algorithm is primarily 
in CollapseScene::update. 

Backtrcking is required. Rather than saving 
the entire state of the grid at each step 
(which would consume all of the RAM), only 
the changes are tracked with a ChainMap so 
backtracking a step is as simple as 
removing the last set of changes.
"""

import pygame
import numpy as np
import random
from time import time
from copy import deepcopy
from collections import ChainMap

# Dimensions
SCREEN_WIDTH = 720
SCREEN_HEIGHT = 480
TILE_SIZE = 20

# Colors
CIRCUIT_COLOR = (53, 53, 53)
CONNECTOR_COLOR = (159, 159, 159)
SUBSTRATE_COLOR = (20, 104, 11)
WIRE_COLOR = (40, 208, 122)

# CIRCUIT_COLOR = (53, 53, 53)
# CONNECTOR_COLOR = (100, 192, 232)
# SUBSTRATE_COLOR = (136, 53, 179)
# WIRE_COLOR = (174, 102, 203)

COLLAPSE_DELAY = 0.01 #.2

LEFT = 0
RIGHT = 1
UP = 2
DOWN = 3

# Make sure the tiles will fully cover the screen
if SCREEN_WIDTH % TILE_SIZE != 0 or SCREEN_HEIGHT % TILE_SIZE != 0:
    raise ValueError

class TileMaker:
    # Increase to make wires thinner
    WIRE_OFFSET = round(TILE_SIZE * .35)
    TERMINAL_OFFSET = WIRE_OFFSET * .95
    TERMINAL_BORDER = round(TILE_SIZE * .2)
    CIRCUIT_EDGE_WIDTH = round(TILE_SIZE * .3)

    # Tile weights
    WIRE_WEIGHT = 10
    CONNECTOR_WEIGHT = 1
    CIRCUIT_WEIGHT = 50

    def _rotate90(self, tile):
        return pygame.transform.rotate(tile, 90)

    def _rotate180(self, tile):
        return pygame.transform.rotate(tile, 180)

    def _rotate270(self, tile):
        return pygame.transform.rotate(tile, 270)
    
    def _mirror_vert(self, tile):
        return pygame.transform.flip(tile, False, True)
    
    def _mirror_horiz(self, tile):
        return pygame.transform.flip(tile, True, False)

    def _tiles_almost_equal(self, tile_a, tile_b):
        a = pygame.surfarray.array3d(tile_a)
        b = pygame.surfarray.array3d(tile_b)
        
        entries = 1
        for s in a.shape:
            entries *= s

        return np.sum(a != b) < entries * .05

    def _blank_tile(self):
        tile = pygame.Surface((TILE_SIZE, TILE_SIZE))
        tile.set_colorkey((0, 0, 0))
        tile.fill((0, 0, 0))
        return tile

    def tile_substrate_blank(self):
        # Blank section of the circuit
        tile = self._blank_tile()
        tile.fill(SUBSTRATE_COLOR)
        return tile, TileMaker.WIRE_WEIGHT

    def tile_wire_diagonal_single(self, tile=None):
        # Wire on a diagonal on one corner
        if tile is None:
            tile = self.tile_substrate_blank()[0]

        pygame.draw.polygon(
            tile,
            WIRE_COLOR,
            [
                (0, TileMaker.WIRE_OFFSET),
                (0, TILE_SIZE - TileMaker.WIRE_OFFSET - 2),
                (TILE_SIZE - TileMaker.WIRE_OFFSET - 2, 0),
                (TileMaker.WIRE_OFFSET, 0)
            ]
        )
        return tile, TileMaker.WIRE_WEIGHT / 2

    def tile_wire_diagonal_double(self):
        # Wire on a diagonal on opposite corners
        tile = self.tile_wire_diagonal_single()[0]
        tile = self._rotate180(tile)
        return self.tile_wire_diagonal_single(tile)[0], TileMaker.WIRE_WEIGHT / 2

    def _tile_wire_edge_to_center(self, tile=None):
        # Helper. Draw a wire to the center of the tile
        if tile is None:
            tile = self.tile_substrate_blank()[0]

        pygame.draw.circle(
            tile,
            WIRE_COLOR,
            (
                TILE_SIZE // 2,
                TILE_SIZE // 2
            ),
            (TILE_SIZE - TileMaker.WIRE_OFFSET * 2) // 2
        )

        pygame.draw.rect(
            tile,
            WIRE_COLOR,
            (
                0,
                TileMaker.WIRE_OFFSET,
                TILE_SIZE // 2,
                TILE_SIZE - TileMaker.WIRE_OFFSET * 2
            )
        )

        return tile

    def tile_wire_straight(self):
        # Wire straight
        tile = self._tile_wire_edge_to_center()
        tile = self._rotate180(tile)
        return self._tile_wire_edge_to_center(tile), TileMaker.WIRE_WEIGHT

    def tile_wire_bend(self):
        # Wire, bend
        tile = self._tile_wire_edge_to_center()
        tile = self._rotate90(tile)
        return self._tile_wire_edge_to_center(tile), TileMaker.WIRE_WEIGHT

    def tile_wire_t(self):
        # Wire, T intersection
        tile = self.tile_wire_bend()[0]
        tile = self._rotate90(tile)
        return self._tile_wire_edge_to_center(tile), TileMaker.WIRE_WEIGHT

    def tile_wire_quad(self):
        # Wire, 4-way intersection
        tile = self.tile_wire_t()[0]
        tile = self._rotate90(tile)
        return self._tile_wire_edge_to_center(tile), TileMaker.WIRE_WEIGHT
    
    def tile_terminal_none(self, tile=None):
        # Wire terminal, no outputs
        if tile is None:
            tile = self.tile_substrate_blank()[0]

        b = TileMaker.TERMINAL_BORDER
        s = TileMaker.TERMINAL_OFFSET
        
        pygame.draw.polygon(
            tile,
            CONNECTOR_COLOR,
            [
                (b, s),
                (b, TILE_SIZE - s),
                (s, TILE_SIZE - b),
                (TILE_SIZE - s, TILE_SIZE - b),
                (TILE_SIZE - b, TILE_SIZE - s),
                (TILE_SIZE - b, s),
                (TILE_SIZE - s, b),
                (s, b),
            ]
        )
        return tile, TileMaker.CONNECTOR_WEIGHT
    
    def tile_terminal_one(self):
        # Wire terminal, one output
        tile = self._tile_wire_edge_to_center()
        return self.tile_terminal_none(tile)[0], TileMaker.CONNECTOR_WEIGHT
    
    def tile_terminal_opposite(self):
        # Wire terminal, two outputs, opposite
        tile = self.tile_wire_straight()[0]
        return self.tile_terminal_none(tile)[0], TileMaker.CONNECTOR_WEIGHT
    
    def tile_terminal_bend(self):
        # Wire terminal, two outputs, bend
        tile = self.tile_wire_bend()[0]
        return self.tile_terminal_none(tile)[0], TileMaker.CONNECTOR_WEIGHT
    
    def tile_terminal_t(self):
        # Wire terminal, three outputs, T intersection
        tile = self.tile_wire_t()[0]
        return self.tile_terminal_none(tile)[0], TileMaker.CONNECTOR_WEIGHT
    
    def tile_terminal_quad(self):
        # Wire terminal, four outputs, 4-way intersection
        tile = self.tile_wire_quad()[0]
        return self.tile_terminal_none(tile)[0], TileMaker.CONNECTOR_WEIGHT
    
    def tile_connector_bridge_blank(self, tile=None):
        # Connector bridge, no wire beneath
        if tile is None:
            tile = self.tile_substrate_blank()[0]
        
        pygame.draw.rect(
            tile,
            CONNECTOR_COLOR,
            (
                TileMaker.WIRE_OFFSET,
                0,
                TILE_SIZE - TileMaker.WIRE_OFFSET * 2,
                TILE_SIZE
            )
        )

        return tile, TileMaker.WIRE_WEIGHT
    
    def tile_connector_bridge_over(self):
        # Connector bridge, wire beneath
        tile = self.tile_wire_straight()[0]
        return self.tile_connector_bridge_blank(tile)[0], TileMaker.CONNECTOR_WEIGHT
    
    def tiles_connector_bridge_terminal_one(self):
        # Connector bridge, terminal_ending
        # Adding lots of copies of the same thing
        # Could be mroe efficient
        # Still shouldn't matter

        tiles = []
        for method_name in self.__dir__():
            if method_name[:14] != "tile_terminal_":
                continue
            method = getattr(self, method_name)
            tile = method()[0]

            rotations = [
                tile,
                self._rotate90(tile),
                self._rotate180(tile),
                self._rotate270(tile),
            ]

            for tile in rotations:
                pygame.draw.rect(
                    tile,
                    CONNECTOR_COLOR,
                    (
                        0,
                        TileMaker.WIRE_OFFSET,
                        TILE_SIZE // 2,
                        TILE_SIZE - TileMaker.WIRE_OFFSET * 2
                    )
                )

                tiles.append(tile)

        tiles = [(t, None) for t in tiles]
        self._remove_duplicates(tiles)
        tiles = [t for t, _ in tiles]

        return tiles, TileMaker.CONNECTOR_WEIGHT

    def _tiles_connector_bridge_terminal_two(self):
        # Connector bridge, terminal_ending
        # Adding lots of copies of the same thing
        # Could be mroe efficient
        # Still shouldn't matter

        tiles = []
        for tile in self.tiles_connector_bridge_terminal_one()[0]:
            rotations = [
                tile,
                self._rotate90(tile),
                self._rotate180(tile),
                self._rotate270(tile),
            ]

            for tile in rotations:
                pygame.draw.rect(
                    tile,
                    CONNECTOR_COLOR,
                    (
                        0,
                        TileMaker.WIRE_OFFSET,
                        TILE_SIZE // 2,
                        TILE_SIZE - TileMaker.WIRE_OFFSET * 2
                    )
                )

                tiles.append(tile)

        tiles = [(t, None) for t in tiles]
        self._remove_duplicates(tiles)
        tiles = [t for t, _ in tiles]

        return tiles, TileMaker.CONNECTOR_WEIGHT

    def _tiles_connector_bridge_terminal_three(self):
        # Connector bridge, terminal_ending
        # Adding lots of copies of the same thing
        # Could be mroe efficient
        # Still shouldn't matter

        tiles = []
        for tile in self.tiles_connector_bridge_terminal_two()[0]:
            rotations = [
                tile,
                self._rotate90(tile),
                self._rotate180(tile),
                self._rotate270(tile),
            ]

            for tile in rotations:
                pygame.draw.rect(
                    tile,
                    CONNECTOR_COLOR,
                    (
                        0,
                        TileMaker.WIRE_OFFSET,
                        TILE_SIZE // 2,
                        TILE_SIZE - TileMaker.WIRE_OFFSET * 2
                    )
                )

                tiles.append(tile)

        tiles = [(t, None) for t in tiles]
        self._remove_duplicates(tiles)
        tiles = [t for t, _ in tiles]

        return tiles, TileMaker.CONNECTOR_WEIGHT

    def tile_circuit_base(self):
        # This is the main bulk of a circuit
        tile = self._blank_tile()
        tile.fill(CIRCUIT_COLOR)
        return tile, 2 * TileMaker.CIRCUIT_WEIGHT

    def tile_circuit_cap(self):
        # This is the edge for a wire to leave the circuit
        tile = self.tile_wire_straight()[0]
        pygame.draw.rect(
            tile,
            CONNECTOR_COLOR,
            (
                0,
                TileMaker.WIRE_OFFSET,
                (TILE_SIZE - TileMaker.CIRCUIT_EDGE_WIDTH) // 3 + TileMaker.CIRCUIT_EDGE_WIDTH,
                TILE_SIZE - TileMaker.WIRE_OFFSET * 2
            )
        )
        pygame.draw.rect(
            tile,
            CIRCUIT_COLOR,
            (
                0,
                0,
                TileMaker.CIRCUIT_EDGE_WIDTH,
                TILE_SIZE
            )
        )
        return tile, TileMaker.CIRCUIT_WEIGHT

    def tile_circuit_corner(self):
        # This is the corner of the circuits
        tile = self.tile_substrate_blank()[0]
        pygame.draw.rect(
            tile,
            CIRCUIT_COLOR,
            (
                0,
                0,
                TileMaker.CIRCUIT_EDGE_WIDTH,
                TileMaker.CIRCUIT_EDGE_WIDTH
            )
        )
        return tile, TileMaker.CIRCUIT_WEIGHT

    def _remove_duplicates(self, tiles):
        tiles_to_remove = []
        for i in range(len(tiles)):
            for j in range(i + 1, len(tiles)):
                if self._tiles_almost_equal(tiles[i][0], tiles[j][0]):
                    if j not in tiles_to_remove:
                        tiles_to_remove.append(j)

        tiles_to_remove.sort()
        for i in reversed(tiles_to_remove):
            tiles.pop(i)

    def make(self, rotations_and_mirror=True):
        tiles = []
        for method_name in self.__dir__():
            method = getattr(self, method_name)
            if method_name[:5] == "tile_":
                m = method()
                weight = m[1]
                gen_tiles = [m[0]]
                if gen_tiles[0] is None:
                    continue
            elif method_name[:6] == "tiles_":
                m = method()
                weight = m[1]
                gen_tiles = [t for t in m[0] if t is not None]
                if len(gen_tiles) == 0:
                    continue
            else:
                continue

            for tile in gen_tiles:
                new_tiles = [tile]

                if rotations_and_mirror:
                    # Rotations
                    a = self._rotate90(tile)
                    b = self._rotate180(tile)
                    c = self._rotate270(tile)
                    new_tiles.extend([a, b, c])

                    # Mirrors
                    # There are 4 variations without mirroring
                    for i in range(4):
                        new_tiles.append(self._mirror_horiz(new_tiles[i]))
                        new_tiles.append(self._mirror_vert(new_tiles[i]))

                    new_tiles = [(t, weight) for t in new_tiles]

                    self._remove_duplicates(new_tiles)

                else:
                    new_tiles = [(tile, weight)]

                tiles.extend(new_tiles)

        # Remove duplicates
        self._remove_duplicates(tiles)

        weights = [w for t, w in tiles]
        tiles = [t for t, w in tiles]

        return tiles, weights

class AdjacencyMaker:
    def _can_pair(self, a, b):
        entries = 1
        for s in a.shape:
            entries *= s

        return np.sum(a != b) < entries * .05

    def _pair_left(self, a, b):
        # Can b be to the left of a?
        a = pygame.surfarray.array3d(a)
        b = pygame.surfarray.array3d(b)

        a_col = a[0,:,:]
        b_col = b[-1,:,:]
        return self._can_pair(a_col, b_col)

    def _pair_right(self, a, b):
        # Can b be to the right of a?
        return self._pair_left(b, a)

    def _pair_up(self, a, b):
        # Can b be to the up of a?
        a = pygame.surfarray.array3d(a)
        b = pygame.surfarray.array3d(b)

        a_row = a[:,0,:]
        b_row = b[:,-1,:]
        return self._can_pair(a_row, b_row)

    def _pair_down(self, a, b):
        # Can b be to the down of a?
        return self._pair_up(b, a)

    def make(self, tiles):
        adj = dict()
        for i, tile in enumerate(tiles):
            adj[i] = {
                LEFT: set(),
                RIGHT: set(),
                UP: set(),
                DOWN: set(),
            }

            for j, other in enumerate(tiles):
                if self._pair_left(tile, other):
                    adj[i][LEFT].add(j)

                if self._pair_right(tile, other):
                    adj[i][RIGHT].add(j)

                if self._pair_up(tile, other):
                    adj[i][UP].add(j)

                if self._pair_down(tile, other):
                    adj[i][DOWN].add(j)

        return adj

def display_tiles(rotations_and_mirror=True):
    tiles, _ = TileMaker().make(rotations_and_mirror)

    SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    x, y = 0, 0
    dx = 1

    for tile in tiles:
        pygame.draw.rect(
            tile,
            (1, 1, 1),
            (
                0,
                0,
                TILE_SIZE,
                TILE_SIZE
            ),
            1
        )

        SCREEN.blit(tile, (x * TILE_SIZE, y * TILE_SIZE))

        x += dx
        if x * TILE_SIZE >= SCREEN_WIDTH or x < 0:
            dx *= -1
            y += 1
            if x < 0:
                x += 1
            else:
                x -= 1

    pygame.display.update()

    import time
    start = time.time()
    while time.time() - start < 100:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_x:
                    quit()

def display_adjacency():
    tiles, _ = TileMaker().make()
    adj = AdjacencyMaker().make(tiles)

    SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    for i, tile in enumerate(tiles):
        x, y = 0, 0
        dx = 1

        SCREEN.fill((1, 1, 1))
        SCREEN.blit(tile, (x * TILE_SIZE, y * TILE_SIZE))
        y += 1

        pygame.draw.rect(SCREEN, (255, 0, 0), (0, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
        x = 1
        dx = 1
        for j in adj[i][LEFT]:
            SCREEN.blit(tiles[j], (x * TILE_SIZE, y * TILE_SIZE))
            
            x += dx
            if x * TILE_SIZE >= SCREEN_WIDTH or x < 0:
                dx *= -1
                y += 1
                if x < 0:
                    x += 1
                else:
                    x -= 1
        y += 1

        pygame.draw.rect(SCREEN, (0, 255, 0), (0, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
        x = 1
        dx = 1
        for j in adj[i][RIGHT]:
            SCREEN.blit(tiles[j], (x * TILE_SIZE, y * TILE_SIZE))
            
            x += dx
            if x * TILE_SIZE >= SCREEN_WIDTH or x < 0:
                dx *= -1
                y += 1
                if x < 0:
                    x += 1
                else:
                    x -= 1
        y += 1

        pygame.draw.rect(SCREEN, (0, 0, 255), (0, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
        x = 1
        dx = 1
        for j in adj[i][UP]:
            SCREEN.blit(tiles[j], (x * TILE_SIZE, y * TILE_SIZE))
            
            x += dx
            if x * TILE_SIZE >= SCREEN_WIDTH or x < 0:
                dx *= -1
                y += 1
                if x < 0:
                    x += 1
                else:
                    x -= 1
        y += 1

        pygame.draw.rect(SCREEN, (0, 255, 255), (0, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
        x = 1
        dx = 1
        for j in adj[i][DOWN]:
            SCREEN.blit(tiles[j], (x * TILE_SIZE, y * TILE_SIZE))
            
            x += dx
            if x * TILE_SIZE >= SCREEN_WIDTH or x < 0:
                dx *= -1
                y += 1
                if x < 0:
                    x += 1
                else:
                    x -= 1
        y += 1

        pygame.display.update()

        import time
        start = time.time()
        do_next = False
        while time.time() - start < 100 and not do_next:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    quit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_x:
                        quit()
                    if event.key == pygame.K_n:
                        do_next = True


    BASE_COLOR = (100, 100, 100)

    def __init__(self):
        self.surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

        self.tiles, self.weights = TileMaker().make()
        self.adj = AdjacencyMaker().make(self.tiles)

        self.update_timer = COLLAPSE_DELAY

        self.reset()

    def reset(self):
        w = SCREEN_WIDTH // TILE_SIZE
        h = SCREEN_HEIGHT // TILE_SIZE

        all_tiles = set(range(len(self.tiles)))
        base_map = {(x, y): deepcopy(all_tiles) for x in range(w) for y in range(h)}
        self.chain = [base_map]

        #first choice, done manually to make sure its set up properly
        fc_x = random.randint(0, w - 1)
        fc_y = random.randint(0, h - 1)
        fc_tile = random.choice(list(all_tiles))
        self.chain[0][(fc_x, fc_y)] = deepcopy(all_tiles).difference({fc_tile})
        self.chain = [{(fc_x, fc_y): {fc_tile}}] + self.chain

    def backtrack(self):
        self.chain = self.chain[1:]

    def draw(self):
        self.surface.fill(CollapseScene.BASE_COLOR)

        for (x,y), tile_set in ChainMap(*self.chain).items():
            if len(tile_set) == 0:
                self.backtrack()
                self.draw()
                return
            elif len(tile_set) == 1:
                self.surface.blit(
                    self.tiles[next(iter(tile_set))],
                    (x * TILE_SIZE, y * TILE_SIZE)
                )

            # This tile is not fully collapsed so 
            #   just draw nothing? The surface is
            #   already filled with a blank color
            else:
                pass

    def pick(self):
        tiles_1d = []
        for (x,y), tile_set in ChainMap(*self.chain).items():
            tiles_1d.append((x, y, len(tile_set)))

        random.shuffle(tiles_1d)
        tiles_1d.sort(key=lambda x: x[2])
        for tile in tiles_1d:
            if tile[2] == 0:
                # self.reset()
                self.backtrack()
                return None, None

            elif tile[2] == 1:
                continue
            else:
                return tile[:2]

        # Nothing to do, done!
        return None, None

    def _weighted_choice(self, options):
        weights = [self.weights[t] for t in options]
        return random.choices(options, weights, k=1)[0]

    def collapse(self, x, y):
        options = ChainMap(*self.chain)[(x, y)]
        # tile = random.choice(list(options))
        tile = self._weighted_choice(list(options))
        self.chain[0][(x, y)] = deepcopy(options).difference({tile})
        self.chain = [{(x, y): {tile}}] + self.chain

    def propagate_helper(self, changed, trial, direction, nx, ny):
        to_remove = set()
        for trial_tile in trial:
            for changed_tile in changed:
                if trial_tile in self.adj[changed_tile][direction]:
                    break
            else:
                to_remove.add(trial_tile)

        # for r in to_remove:
            # trial.remove(r)
        self.chain[0][(nx, ny)] = trial.difference(to_remove)
        
        return len(to_remove) > 0

    def neighbors(self, x, y):
        directions = [
            (-1, 0, LEFT),
            (1, 0, RIGHT),
            (0, -1, UP),
            (0, 1, DOWN),
        ]

        chainmap = ChainMap(*self.chain)
        for dx, dy, dire in directions:
            nx = x + dx
            ny = y + dy

            try:
                chainmap[(nx, ny)]
                yield nx, ny, dire
            except KeyError:
                pass # That neighbor was off the grid

    def propagate(self, x, y):
        changed = [(x, y)]

        while len(changed) > 0:
            cx, cy = changed.pop()

            chainmap = ChainMap(*self.chain)
            for nx, ny, dire in self.neighbors(cx, cy):
                # current_set = self.grid[cy][cx]
                # neighbor_set = self.grid[ny][nx]
                current_set = chainmap[(cx, cy)]
                neighbor_set = chainmap[(nx, ny)]
                if self.propagate_helper(current_set, neighbor_set, dire, nx, ny):
                    # A change was made to the neighbor
                    changed.append((nx, ny))

    def update(self, elapsed):
        self.update_timer -= elapsed

        while self.update_timer < 0:
            self.update_timer += COLLAPSE_DELAY

            x, y = self.pick()
            if x is None and y is None:
                continue

            self.collapse(x, y)
            self.propagate(x, y)

    def run(self):

        last_update_time = time()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    quit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_x:
                        quit()

                    if event.key == pygame.K_r:
                        self.reset()

            current_time = time()
            elapsed = current_time - last_update_time
            last_update_time = current_time
            self.update(elapsed)

            self.draw()

            pygame.display.update()

class CollapseScene:
    BASE_COLOR = (100, 100, 100)

    def __init__(self):
        self.surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

        self.tiles, self.weights = TileMaker().make()
        self.adj = AdjacencyMaker().make(self.tiles)

        self.update_timer = COLLAPSE_DELAY

        self.reset()

    def reset(self):
        w = SCREEN_WIDTH // TILE_SIZE
        h = SCREEN_HEIGHT // TILE_SIZE

        all_tiles = set(range(len(self.tiles)))
        base_map = {(x, y): deepcopy(all_tiles) for x in range(w) for y in range(h)}
        self.chain = [base_map]

        #first choice, done manually to make sure its set up properly
        fc_x = random.randint(0, w - 1)
        fc_y = random.randint(0, h - 1)
        fc_tile = random.choice(list(all_tiles))
        self.chain[0][(fc_x, fc_y)] = deepcopy(all_tiles).difference({fc_tile})
        self.chain = [{(fc_x, fc_y): {fc_tile}}] + self.chain
        self.update_chainmap()

        self.completed = dict()

    def backtrack(self):
        if len(self.chain) == 0:
            self.reset()
        self.chain = self.chain[1:]
        self.update_chainmap()

    def update_chainmap(self):
        self.chainmap = ChainMap(*self.chain)

    def reduce_chainmap(self):
        while len(self.chain) > 20:
            removed = self.chain.pop()

            self.completed.update(removed)

    def grid_iter(self):
        found = set()
        for k, v in list(self.chainmap.items()) + list(self.completed.items()):
            if k in found:
                continue
            found.add(k)

            yield k, v

    def grid_getter(self, x, y):
        if (x, y) in self.chainmap:
            return self.chainmap[(x, y)]
        if (x, y) in self.completed:
            return self.completed[(x, y)]

        raise ValueError(f"({x}, {y}) not in maps")

    def draw(self):
        self.surface.fill(CollapseScene.BASE_COLOR)

        for (x,y), tile_set in self.grid_iter():
            if len(tile_set) == 0:
                self.backtrack()
                self.draw()
                return

            elif len(tile_set) == 1:
                self.surface.blit(
                    self.tiles[next(iter(tile_set))],
                    (x * TILE_SIZE, y * TILE_SIZE)
                )

            # This tile is not fully collapsed so 
            #   just draw nothing? The surface is
            #   already filled with a blank color
            else:
                pass

    def pick(self):
        tiles_1d = []
        for (x,y), tile_set in self.grid_iter():
            tiles_1d.append((x, y, len(tile_set)))

        random.shuffle(tiles_1d)
        tiles_1d.sort(key=lambda x: x[2])
        for tile in tiles_1d:
            if tile[2] == 0:
                # self.reset()
                self.backtrack()
                return None, None

            elif tile[2] == 1:
                continue
            else:
                return tile[:2]

        # Nothing to do, done!
        return None, None

    def _weighted_choice(self, options):
        weights = [self.weights[t] for t in options]
        return random.choices(options, weights, k=1)[0]

    def collapse(self, x, y):
        options = self.grid_getter(x, y)

        tile = self._weighted_choice(list(options))
        self.chain[0][(x, y)] = deepcopy(options).difference({tile})
        self.chain = [{(x, y): {tile}}] + self.chain
        self.reduce_chainmap()
        self.update_chainmap()

    def propagate_helper(self, changed, trial, direction, nx, ny):
        to_remove = set()
        for trial_tile in trial:
            for changed_tile in changed:
                if trial_tile in self.adj[changed_tile][direction]:
                    break
            else:
                to_remove.add(trial_tile)

        self.chain[0][(nx, ny)] = trial.difference(to_remove)
        self.update_chainmap()

        return len(to_remove) > 0

    def neighbors(self, x, y):
        directions = [
            (-1, 0, LEFT),
            (1, 0, RIGHT),
            (0, -1, UP),
            (0, 1, DOWN),
        ]

        w = SCREEN_WIDTH // TILE_SIZE
        h = SCREEN_HEIGHT // TILE_SIZE

        for dx, dy, dire in directions:
            nx = x + dx
            ny = y + dy

            if not (0 <= nx < w) or not (0 <= ny < h):
                continue

            yield nx, ny, dire

    def propagate(self, x, y):
        changed = [(x, y)]

        while len(changed) > 0:
            cx, cy = changed.pop()

            for nx, ny, dire in self.neighbors(cx, cy):
                current_set = self.grid_getter(cx, cy)
                neighbor_set = self.grid_getter(nx, ny)
                if self.propagate_helper(current_set, neighbor_set, dire, nx, ny):
                    # A change was made to the neighbor
                    changed.append((nx, ny))

    def update(self, elapsed):
        self.update_timer -= elapsed

        while self.update_timer < 0:
            self.update_timer += COLLAPSE_DELAY

            x, y = self.pick()
            if x is None and y is None:
                continue

            self.collapse(x, y)
            self.propagate(x, y)

    def run(self):

        last_update_time = time()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    quit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_x:
                        quit()

                    if event.key == pygame.K_r:
                        self.reset()

            current_time = time()
            elapsed = current_time - last_update_time
            last_update_time = current_time
            self.update(elapsed)

            self.draw()

            pygame.display.update()

if __name__ == "__main__":
    # display_tiles(True)
    # display_adjacency()
    CollapseScene().run()