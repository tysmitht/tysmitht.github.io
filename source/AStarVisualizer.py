import pygame, os
from enum import Enum, auto
from math import inf, sqrt, ceil
from time import time
from copy import deepcopy


# Adjust the screen position
y = 50
x = 25
os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (x,y)

pygame.init()

# Dimensions
ScreenSize = 500
TileSize = 16
TileBorder = 1
Border = 10
TextHeight = 50
TextBorder = 5

Screen = pygame.display.set_mode((ScreenSize, ScreenSize + TextHeight))

# Fonts
pygame.font.init()
DisplayFont = pygame.font.SysFont("couriernew", 50, bold=1)

# Timing
StageDelayTime = .1

# Colors
grey = lambda n: (n, n, n)
White = grey(255)
Black = grey(0)
Blue = (44, 44, 177)
LightBlue = (203, 233, 246)
Red = (177, 44, 44)
Green = (44, 177, 44)

class Tile(Enum):
    Wall = auto()
    Clear = auto()
    Start = auto()
    End = auto()
    Path = auto()

class Selection(Enum):
    Walls = auto()
    Start = auto()
    End = auto()

class SelectedButton:
    def __init__(self, msg, x, y, w, h, textBorder=TextBorder, textColor=Black, baseColor=grey(150), unselectedColor=Red, selectedColor=Green):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

        self.textBorder = textBorder
        
        self.baseColor = baseColor
        self.unselectedColor = unselectedColor
        self.selectedColor = selectedColor

        self.textSurface = DisplayFont.render(msg, True, textColor)
        scaleX = (self.w - textBorder * 2) / self.textSurface.get_width()
        scaleY = (self.h - textBorder * 2) / self.textSurface.get_height()
        scale = min(scaleX, scaleY)
        self.textSurface = pygame.transform.scale(
            self.textSurface,
            (
                round(self.textSurface.get_width() * scale),
                round(self.textSurface.get_height() * scale)
            )
        )

        self.textRect = self.textSurface.get_rect()
        self.textRect.center = (
            round(self.x + self.w / 2),
            round(self.y + self.h / 2)
        )

        self.selected = False

    def Draw(self, surface):
        if self.selected:
            pygame.draw.rect(
                surface,
                self.selectedColor,
                (
                    self.x,
                    self.y,
                    self.w,
                    self.h
                )
            )
        else:
            pygame.draw.rect(
                surface,
                self.unselectedColor,
                (
                    self.x,
                    self.y,
                    self.w,
                    self.h
                )
            )

        pygame.draw.rect(
            surface,
            self.baseColor,
            (
                self.x + self.textBorder,
                self.y + self.textBorder,
                self.w - self.textBorder * 2,
                self.h - self.textBorder * 2
            )
        )

        surface.blit(self.textSurface, self.textRect)

    def HandleEvent(self, event):
        """
        Returns True if its selected by this event
        """
        if self.selected:
            return False

        if event.type != pygame.MOUSEBUTTONDOWN:
            return False

        if self.x <= event.pos[0] and \
            event.pos[0] <= self.x + self.w and \
                self.y <= event.pos[1] and \
                    event.pos[1] <= self.y + self.h:
            self.selected = True
            return True
        else:
            return False

class Button:
    def __init__(self, msg, x, y, w, h, textBorder=TextBorder, textColor=Black, baseColor=grey(150), highlightColor=Green):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        
        self.baseColor = baseColor
        self.highlightColor = highlightColor

        self.textSurface = DisplayFont.render(msg, True, textColor)
        scaleX = (self.w - textBorder * 2) / self.textSurface.get_width()
        scaleY = (self.h - textBorder * 2) / self.textSurface.get_height()
        scale = min(scaleX, scaleY)
        self.textSurface = pygame.transform.scale(
            self.textSurface,
            (
                round(self.textSurface.get_width() * scale),
                round(self.textSurface.get_height() * scale)
            )
        )

        self.textRect = self.textSurface.get_rect()
        self.textRect.center = (
            round(self.x + self.w / 2),
            round(self.y + self.h / 2)
        )

    def Draw(self, surface):
        pos = pygame.mouse.get_pos()
        if self.x <= pos[0] and \
            pos[0] <= self.x + self.w and \
                self.y <= pos[1] and \
                    pos[1] <= self.y + self.h:
            color = self.highlightColor
        else:
            color = self.baseColor

        pygame.draw.rect(
            surface,
            color,
            (
                self.x,
                self.y,
                self.w,
                self.h
            )
        )

        surface.blit(self.textSurface, self.textRect)

    def IsPressed(self):
        pos = pygame.mouse.get_pos()
        if self.x <= pos[0] and \
            pos[0] <= self.x + self.w and \
                self.y <= pos[1] and \
                    pos[1] <= self.y + self.h:
            pressed = pygame.mouse.get_pressed()
            if pressed[0]:
                return True
        return False

class GridGenerator:
    def __init__(self):
        self.dimension = (ScreenSize - Border * 2) // TileSize
        self.grid = [
            [Tile.Clear for i in range(self.dimension)]
            for j in range(self.dimension)
        ]

        self.mouseDown = False
        self.lastMousePosition = (inf, inf)
        self.buttonTypeSelected = None
        self.placingWalls = False

    def Draw(self, surface):
        for y in range(self.dimension):
            for x in range(self.dimension):
                pygame.draw.rect(
                    surface,
                    grey(100),
                    (
                        x * TileSize + Border,
                        y * TileSize + Border,
                        TileSize,
                        TileSize
                    )
                )

                color = grey(175)
                if self.grid[y][x] == Tile.Wall:
                    color = grey(100)
                elif self.grid[y][x] == Tile.Start:
                    color = Green
                elif self.grid[y][x] == Tile.End:
                    color = Red
                elif self.grid[y][x]  == Tile.Path:
                    color = Blue

                pygame.draw.rect(
                    surface,
                    color,
                    (
                        x * TileSize + Border + TileBorder,
                        y * TileSize + Border + TileBorder,
                        TileSize - 2 * TileBorder,
                        TileSize - 2 * TileBorder
                    )
                )

    def DrawStage(self, surface, stage):
        for y in range(self.dimension):
            for x in range(self.dimension):
                pygame.draw.rect(
                    surface,
                    grey(100),
                    (
                        x * TileSize + Border,
                        y * TileSize + Border,
                        TileSize,
                        TileSize
                    )
                )

                color = grey(175)
                if self.grid[y][x] == Tile.Wall:
                    color = grey(100)
                elif self.grid[y][x] == Tile.Start:
                    color = Green
                elif self.grid[y][x] == Tile.End:
                    color = Red
                elif self.grid[y][x]  == Tile.Path or \
                    (y, x) in stage[1]:
                    color = Blue
                elif (y, x) in stage[0]:
                    color = LightBlue

                pygame.draw.rect(
                    surface,
                    color,
                    (
                        x * TileSize + Border + TileBorder,
                        y * TileSize + Border + TileBorder,
                        TileSize - 2 * TileBorder,
                        TileSize - 2 * TileBorder
                    )
                )

    def GetStartPoint(self):
        for y in range(len(self.grid)):
            for x in range(len(self.grid[y])):
                if self.grid[y][x] == Tile.Start:
                    return (y, x)
        return (inf, inf)

    def GetEndPoint(self):
        for y in range(len(self.grid)):
            for x in range(len(self.grid[y])):
                if self.grid[y][x] == Tile.End:
                    return (y, x)
        return (inf, inf)

    def ClearWalls(self):
        for y in range(self.dimension):
            for x in range(self.dimension):
                self.grid[y][x] = Tile.Clear

    def SetStart(self, pos):
        """
        Takes in a mouse position in pixels
        """
        # Make sure the click is on the grid
        if pos[0] < Border or pos[0] > ScreenSize - 2 * Border or \
            pos[1] < Border or pos[1] > ScreenSize - 2 * Border:
            return 
            
        for y in range(len(self.grid)):
            for x in range(len(self.grid[y])):
                if self.grid[y][x] == Tile.Start:
                    self.grid[y][x] = Tile.Clear

                    # I could do this,
                    # but its safer to leave it out to be safe
                    # break

        x = (pos[0] - Border) // TileSize
        y = (pos[1] - Border) // TileSize

        
        if 0 > x or 0 > y or \
            x >= self.dimension or y >= self.dimension:
            return

        self.grid[y][x] = Tile.Start

    def PlaceWall(self, y, x):

        if self.placingWalls:
            if self.grid[y][x] == Tile.Clear:
                self.grid[y][x] = Tile.Wall
        else:
            if self.grid[y][x] == Tile.Wall:
                self.grid[y][x] = Tile.Clear

    def SetWall(self, pos):
        distance = sqrt(
            (pos[1] - self.lastMousePosition[1]) ** 2 + \
            (pos[0] - self.lastMousePosition[0]) ** 2
        )

        intermediateSteps = int(1 * (distance // TileSize)) + 1

        dy = (-pos[1] + self.lastMousePosition[1]) / intermediateSteps
        dx = (-pos[0] + self.lastMousePosition[0]) / intermediateSteps
        for _ in range(intermediateSteps):
            try:
                x = round((pos[0] - Border) / TileSize)
                y = round((pos[1] - Border) / TileSize)

                if 0 > x or 0 > y or \
                    x >= self.dimension or y >= self.dimension:
                    return

                self.PlaceWall(y, x)

                pos = (
                    pos[0] + dx,
                    pos[1] + dy
                )
            except:
                raise ValueError(y, "and", x, "are not invalid indices")

    def SetEnd(self, pos):
        """
        Takes in a mouse position in pixels
        """
        # Make sure the click is on the grid
        if pos[0] < Border or pos[0] > ScreenSize - 2 * Border or \
            pos[1] < Border or pos[1] > ScreenSize - 2 * Border:
            return 

        for y in range(len(self.grid)):
            for x in range(len(self.grid[y])):
                if self.grid[y][x] == Tile.End:
                    self.grid[y][x] = Tile.Clear

                    # I could do this,
                    # but its safer to leave it out to be safe
                    # break

        x = (pos[0] - Border) // TileSize
        y = (pos[1] - Border) // TileSize

        
        if 0 > x or 0 > y or \
            x >= self.dimension or y >= self.dimension:
            return

        self.grid[y][x] = Tile.End

    def SetTiles(self, pos):
        if self.buttonTypeSelected == Selection.Start:
            self.SetStart(pos)
        elif self.buttonTypeSelected == Selection.End:
            self.SetEnd(pos)
        elif self.buttonTypeSelected == Selection.Walls:
            self.SetWall(pos)

    def HandleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.mouseDown = True
            self.lastMousePosition = event.pos

            # Determine if the current tile is a wall
            y = (event.pos[1] - Border) // TileSize
            x = (event.pos[0] - Border) // TileSize
        
            if 0 <= x < self.dimension and \
                0 <= y < self.dimension and\
                    self.grid[y][x] == Tile.Wall:
                self.placingWalls = False
            else:
                self.placingWalls = True
            self.SetTiles(event.pos)
            # if self.buttonTypeSelected == Selection.Walls:
            #     self.SetInvidualWall(event.pos)

        elif event.type == pygame.MOUSEBUTTONUP:
            self.mouseDown = False
            self.placingWalls = False
            # To cause an IndexError if we try to use this without the mouse being down
            self.lastMousePosition = (inf, inf) 

        elif event.type == pygame.MOUSEMOTION:
            if self.mouseDown and self.buttonTypeSelected == Selection.Walls:
                self.SetTiles(event.pos)
                self.lastMousePosition = event.pos

def Wait(seconds):
    start = time()
    while time() - start < seconds:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or \
                (event.type == pygame.KEYDOWN and event.key == pygame.K_x):
                pygame.quit()
                quit()

def ReconstructPath(cameFrom, current):
    totalPath = [current]
    while current in cameFrom.keys():
        current = cameFrom[current]
        totalPath = [current] + totalPath
    return totalPath

def BasicHueristic(startPoint, endPoint):
    return sqrt(
        (startPoint[0] - endPoint[0]) ** 2 +
        (startPoint[1] - endPoint[1]) ** 2
    )

def GetNeighbors(node, grid):
    """
    For generating the neighbors of a node safely
    Babies first (real) generator
    """
    for y in range(node[0] - 1, node[0] + 2):
        for x in range(node[1] - 1, node[1] + 2):
            # The node is not a neighobr of itself
            if (y, x) == node:
                continue
            if y < 0 or x < 0:
                continue

            # This is not the best, but it works so meh for now
            try:
                if grid[y][x] != Tile.Wall:
                    if y != node[0] and x != node[1]:
                        if grid[node[0]][x] == Tile.Wall and grid[y][node[1]] == Tile.Wall:
                            continue
                    yield (y, x)
            except IndexError:
                # Expected to happen on the edges
                pass

def DepthFirstSearch(grid, startPoint, endPoint, h=BasicHueristic):
    from random import choice
    """
    Goal is to simply return a path
    Not the best path, but a path
    For making sure that the system dealing with the result works fine
    """
    
    # Change this to a min heap at some point
    openSet = set()
    openSet.add(startPoint)

    visitedSet = set()

    cameFrom = dict()

    while len(openSet) > 0:

        # Get an element of the set
        current = None
        for tile in openSet:
            current = tile
            break

        if current == endPoint:
            return ReconstructPath(cameFrom, current)

        openSet.remove(current)
        visitedSet.add(current)

        for neighbor in GetNeighbors(current, grid):
            if neighbor not in openSet and neighbor not in visitedSet:
                cameFrom[neighbor] = current
                openSet.add(neighbor)

    # This is a failure case
    return []

def AStar(grid, startPoint, endPoint, h=BasicHueristic):
    """
    Returns the optimal path between the start and end points
    Return is a list of tuples:
        [(a, b), ... (c,d)]
    """
    stages = []
    # Change this to a min heap at some point
    openSet = set()
    visited = set()
    openSet.add(startPoint)

    cameFrom = dict()

    # Better choice would be a default dict somehow, but im not too worried about this run time
    gScore = dict()
    fScore = dict()
    for y in range(len(grid)):
        for x in range(len(grid[y])):
            gScore[(y, x)] = inf
            fScore[(y, x)] = inf
    gScore[startPoint] = 0
    fScore[startPoint] = h(startPoint, endPoint)

    while len(openSet) > 0:
        # Determine the node with the minimum fScore
        minFScore = inf
        current = None
        for node in openSet:
            if fScore[node] <= minFScore:
                minFScore = fScore[node]
                current = node

        if current == endPoint:
            return stages, ReconstructPath(cameFrom, current)

        openSet.remove(current)
        visited.add(current)

        stages.append([deepcopy(openSet), deepcopy(visited)])

        for neighbor in GetNeighbors(current, grid):
            # Im using the h function here
            # Only works because h is currently the simple distance function
            # Change to the distance function if need be
            tentativeGScore = gScore[current] + h(current, neighbor)

            if tentativeGScore < gScore[neighbor]:
                cameFrom[neighbor] = current
                gScore[neighbor] = tentativeGScore
                fScore[neighbor] = gScore[neighbor] + h(neighbor, endPoint)

                if neighbor not in openSet:
                    openSet.add(neighbor)

    # This is a failure case
    return []

def Visualize():
    NumberOfButtons = 5
    grid = GridGenerator()
    wallSelectedButton = SelectedButton(
        "Walls",
        Border,
        ScreenSize,
        (ScreenSize - Border * (NumberOfButtons + 1)) // NumberOfButtons,
        TextHeight - Border
    )
    startSelectedButton = SelectedButton(
        "Start",
        Border * 2 + (ScreenSize - Border * (NumberOfButtons + 1)) // NumberOfButtons,
        ScreenSize,
        (ScreenSize - Border * (NumberOfButtons + 1)) // NumberOfButtons,
        TextHeight - Border
    )
    endSelectedButton = SelectedButton(
        "End",
        Border * 3 + 2 * (ScreenSize - Border * (NumberOfButtons + 1)) // NumberOfButtons,
        ScreenSize,
        (ScreenSize - Border * (NumberOfButtons + 1)) // NumberOfButtons,
        TextHeight - Border
    )
    startButton = Button(
        "Start Sim",
        Border * 4 + 3 * (ScreenSize - Border * (NumberOfButtons + 1)) // NumberOfButtons,
        ScreenSize,
        (ScreenSize - Border * (NumberOfButtons + 1)) // NumberOfButtons,
        TextHeight - Border
    )
    clear = Button(
        "Clear",
        Border * 5 + 4 * (ScreenSize - Border * (NumberOfButtons + 1)) // NumberOfButtons,
        ScreenSize,
        (ScreenSize - Border * (NumberOfButtons + 1)) // NumberOfButtons,
        TextHeight - Border
    )

    selectedOperation = Selection.Start
    startSelectedButton.selected = True
    grid.buttonTypeSelected = Selection.Start
    while True:

        #######################################
        # Updating
        #######################################
        for event in pygame.event.get():
            if event.type == pygame.QUIT or \
                (event.type == pygame.KEYDOWN and event.key == pygame.K_x):
                pygame.quit()
                quit()

            if wallSelectedButton.HandleEvent(event):
                startSelectedButton.selected = False
                endSelectedButton.selected = False
                selectedOperation = Selection.Walls
                grid.buttonTypeSelected = Selection.Walls
            elif startSelectedButton.HandleEvent(event):
                wallSelectedButton.selected = False
                endSelectedButton.selected = False
                selectedOperation = Selection.Start
                grid.buttonTypeSelected = Selection.Start
            elif endSelectedButton.HandleEvent(event):
                startSelectedButton.selected = False
                wallSelectedButton.selected = False
                selectedOperation = Selection.End
                grid.buttonTypeSelected = Selection.End

            # GridGenerator
            # event handling
            grid.HandleEvent(event)

        if startButton.IsPressed():
            break

        if clear.IsPressed():
            grid.ClearWalls()

            
        #######################################
        # Drawing
        #######################################
        
        Screen.fill(grey(25))
        grid.Draw(Screen)
        wallSelectedButton.Draw(Screen)
        startSelectedButton.Draw(Screen)
        endSelectedButton.Draw(Screen)
        startButton.Draw(Screen)
        clear.Draw(Screen)

        pygame.display.update()

    

    stages, path = AStar(grid.grid, grid.GetStartPoint(), grid.GetEndPoint())
    for stage in stages:
        grid.DrawStage(Screen, stage)
        pygame.display.update()
        Wait(StageDelayTime)
    for y, x in path:
        grid.grid[y][x] = Tile.Path

    quitting = False
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or \
                (event.type == pygame.KEYDOWN and event.key == pygame.K_x):
                pygame.quit()
                quit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                quitting = True

        Screen.fill(grey(25))
        grid.Draw(Screen)
        pygame.display.update()

        if quitting:
            break


if __name__ == "__main__":
    while True:
        Visualize()
        