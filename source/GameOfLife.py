"""
Simulation of Conway's Game of Life

Its very cool to take standard shapes, then change the birth and death values

For example:
    Legend: D=Dead, A=Alive

    D D D D D
    D A A A D
    D D D D D

    Then add a birth value of 2 (in addition to 3)
"""

import pygame, sys, os
from time import time
from random import randint

pygame.init()

y = 50
x = 25
os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (x,y)

# Dimensions
Border = 10
ScreenWidth = 950
ScreenHeight = 550
TileSize = 10
ControlPanelHeight = 50

adjustedWidth = ScreenWidth + Border * (2 - 6)
ButtonWidth = round(adjustedWidth * .45 / 3)
SelectorWidth = round(adjustedWidth * .55 / 2)

Screen = pygame.display.set_mode((ScreenWidth + Border * 2, ScreenHeight + Border * 3))

# Colors
def Grey(n):
    return (n, n, n)
White = Grey(255)
Black = Grey(0)
BackgroundColor = Grey(50)
ForegroundColor = Grey(200)

# Font
pygame.font.init()
DisplayFont = pygame.font.SysFont("Arial", 50)

# Timing
TimePerStage = 1 # in seconds

# Simple enumeration
Alive = True
Dead = False

# Text arrangement, coloring, and potential outlining
def _CirclePoints(r):
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

def _RenderWithBorder(text, font, color, outlineColor, outlineWidth):
    textsurface = font.render(text, True, color).convert_alpha()
    w = textsurface.get_width() + 2 * outlineWidth
    h = font.get_height()

    osurf = pygame.Surface((w, h + 2 * outlineWidth)).convert_alpha()
    osurf.fill((0, 0, 0, 0))

    surf = osurf.copy()

    osurf.blit(font.render(text, True, outlineColor).convert_alpha(), (0, 0))

    for dx, dy in _CirclePoints(outlineWidth):
        surf.blit(osurf, (dx + outlineWidth, dy + outlineWidth))

    surf.blit(textsurface, (outlineWidth, outlineWidth))
    return surf

def _ResizeText(text, width, height, color, angle, font, outlineWidth, outlineColor):
    # Create the text
    # No border
    if outlineWidth <= 0:
        surface = font.render(text, True, color)
    # An outline is requested
    else:
        # Generating an outline can be tricky depending on the fontsize and how much it is about to be scaled. 
        # Works best when fontSize is only slightly larger
        surface = _RenderWithBorder(text, font, color, outlineColor, outlineWidth)


    # Rotate the image
    surface = pygame.transform.rotate(
        surface,
        angle
    )

    # Scale the surface
    scale = 1
    if height != None:
        scale = min(height / surface.get_height(), scale)
    if width != None:
        scale = min(width / surface.get_width(), scale)
        
    surface = pygame.transform.scale(
        surface,
        (
            round(surface.get_width() * scale),
            round(surface.get_height() * scale)
        )
    )

    return surface
   
def ResizeMidLeftText(text, width, height, x, y, color=Black, angle=0, font=DisplayFont, outlineWidth=-1, outlineColor=None):
    surface = _ResizeText(text, width, height, color, angle, font, outlineWidth, outlineColor)

    # Position the text
    rect = surface.get_rect()
    rect.midleft = (x, y)

    return surface, rect 

def ResizeCenterText(text, width, height, x, y, color=Black, angle=0, font=DisplayFont, outlineWidth=-1, outlineColor=None):
    surface = _ResizeText(text, width, height, color, angle, font, outlineWidth, outlineColor)

    # Position the text
    rect = surface.get_rect()
    rect.center = (x, y)

    return surface, rect

def GetNeighbors(pos, height, width):
    for y in range(pos[0] - 1, pos[0] + 2):
        for x in range(pos[1] - 1, pos[1] + 2):
            if (y, x) == pos:
                continue
            if 0 <= y < height and 0 <= x < width:
                yield (y, x)

class Button:
    def __init__(self, msg, rect, secondaryMsg=None, standardColor=Grey(175), hoverColor=Grey(200)):
        self.rect = rect

        self.standardColor = standardColor
        if hoverColor == None:
            self.hoverColor = standardColor
        else:
            self.hoverColor = hoverColor

        if msg != "":
            self.textSurf, self.textRect = ResizeCenterText(
                msg,
                self.rect.w - Border,
                self.rect.h - Border,
                self.rect.x + self.rect.w // 2,
                self.rect.y + self.rect.h // 2
            )
        else:
            self.textSurf, self.textRect = None, None
        if secondaryMsg != None:
            self.secondTextSurf, self.secondTextRect = ResizeCenterText(
                secondaryMsg,
                self.rect.w - Border,
                self.rect.h - Border,
                self.rect.x + self.rect.w // 2,
                self.rect.y + self.rect.h // 2
            )
        else:
            self.secondTextSurf, self.secondTextRect = None, None

    def Draw(self, surface, state=False):
        if self.OnButton(pygame.mouse.get_pos()):
            pygame.draw.rect(surface, self.hoverColor, self.rect)
        else:
            pygame.draw.rect(surface, self.standardColor, self.rect)

        pygame.draw.rect(surface, Black, self.rect, 2)

        if not state:
            if self.textSurf is not None and self.textRect is not None:
                surface.blit(self.textSurf, self.textRect)
        else:
            if self.secondTextSurf is not None and self.secondTextRect is not None:
                surface.blit(self.secondTextSurf, self.secondTextRect)

    def OnButton(self, pos):
        return self.rect.collidepoint(pos)

class StateButton(Button):
    def __init__(self, rect, iState=False, standardColor=Grey(200), fillColor=Grey(50)):
        super().__init__("", rect, standardColor=standardColor)

        self.state = iState
        self.fillColor = fillColor

    def Draw(self, surface):
        if self.state:
            pygame.draw.rect(surface, self.fillColor, self.rect)
        else:
            pygame.draw.rect(surface, self.standardColor, self.rect)

        pygame.draw.rect(surface, Black, self.rect, 2)

    def HandleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.OnButton(event.pos):
                self.state = not self.state

class Selector:
    def __init__(self, rect, name, backgroundColor=Grey(175)):
        self.rect = rect

        self.bgColor = backgroundColor
                
        self.textSurf, self.textRect = ResizeMidLeftText(
            name,
            None,
            self.rect.h - Border,
            self.rect.x + Border,
            self.rect.y + self.rect.h // 2
        )

        buttonWidth = round((self.rect.w - Border * 3 - Border * 8 / 2 -  self.textRect.w) / 9)
        buttonHeight = round(self.rect.h - Border * 2)
        startingX = round(self.textRect.x + self.textRect.w + Border)
        dx = buttonWidth + Border // 2
        y = self.rect.y + Border

        self.buttons = {
            i : StateButton(
                pygame.Rect(
                    startingX + dx * i,
                    y,
                    buttonWidth,
                    buttonHeight
                )
            )
            for i in range(9)
        }

        # Not rigorous but meh
        if name == "Birth":
            for i in [3]:
                self.buttons[i].state = True
        elif name == "Death":
            for i in [0, 1, 4, 5, 6, 7, 8]:
                self.buttons[i].state = True

    def Draw(self, surface):
        pygame.draw.rect(
            surface,
            self.bgColor,
            self.rect
        )
        pygame.draw.rect(
            surface,
            Black,
            self.rect,
            2
        )

        surface.blit(self.textSurf, self.textRect)

        for button in self.buttons.values():
            button.Draw(surface)

    def HandleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for button in self.buttons.values():
                button.HandleEvent(event)

    def GetActiveValues(self):
        activeValues = set()
        for i, button in self.buttons.items():
            if button.state:
                activeValues.add(i)
        return activeValues

class Field:
    def __init__(self, rect):
        self.rect = rect
        self.tileWidth = self.rect.w // TileSize
        self.tileHeight = self.rect.h // TileSize

        self.grid = [[Dead for _ in range(self.tileWidth)] for _ in range(self.tileHeight)]

    def Draw(self, surface):
        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                if cell == Alive:
                    cellColor = BackgroundColor
                else:
                    cellColor = ForegroundColor

                # Draw the actual cell
                pygame.draw.rect(
                    surface,
                    cellColor,
                    (
                        x * TileSize + self.rect.x,
                        y * TileSize + self.rect.y,
                        TileSize,
                        TileSize
                    )
                )
                
        pygame.draw.rect(
            surface,
            Black,
            self.rect,
            2
        )

    def HandleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                y = (event.pos[1] - self.rect.y) // TileSize
                x = (event.pos[0] - self.rect.x) // TileSize
                
                self.grid[y][x] = Alive if self.grid[y][x] == Dead else Dead

    def Randomize(self):
        for y in range(len(self.grid)):
            for x in range(len(self.grid[y])):
                if randint(0, 1) == 0:
                    self.grid[y][x] = Dead
                else:
                    self.grid[y][x] = Alive

    def Clear(self):
        self.grid = [[Dead for _ in range(self.tileWidth)] for _ in range(self.tileHeight)]

    def Progress(self, birthValues, deathValues):
        """
        Simulate one round of the game
        """
        # Should be a deepcopy
        # Just doing this because its a easy way to get an equivalently sized matrix
        newGrid = [[None for _ in range(self.tileWidth)] for _ in range(self.tileHeight)]

        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                aliveNeighborCount = 0
                for n in GetNeighbors((y, x), self.tileHeight, self.tileWidth):
                    if self.grid[n[0]][n[1]] == Alive:
                        aliveNeighborCount += 1

                if self.grid[y][x] == Alive:
                    if aliveNeighborCount in deathValues:
                        newGrid[y][x] = Dead
                    else:
                        newGrid[y][x] = Alive
                else:
                    if aliveNeighborCount in birthValues:
                        newGrid[y][x] = Alive
                    else:
                        newGrid[y][x] = Dead
        self.grid = newGrid

def Main():

    paused = True

    field = Field(
        pygame.Rect(
            Border, Border,
            ScreenWidth,
            ScreenHeight - ControlPanelHeight
        )
    )

    currentX = Border
    currentY = ScreenHeight - ControlPanelHeight + Border * 2

    randomizeButton = Button(
        "Randomize",
        pygame.Rect(
            currentX,
            currentY,
            ButtonWidth,
            ControlPanelHeight
        )
    )
    currentX += ButtonWidth + Border

    clearButton = Button(
        "Clear",
        pygame.Rect(
            currentX,
            currentY,
            ButtonWidth,
            ControlPanelHeight
        )
    )
    currentX += ButtonWidth + Border

    pauseButton = Button(
        "Pause",
        pygame.Rect(
            currentX,
            currentY,
            ButtonWidth,
            ControlPanelHeight
        ),
        secondaryMsg="Unpause"
    )
    currentX += ButtonWidth + Border

    birthSelector = Selector(
        pygame.Rect(
            currentX,
            currentY,
            SelectorWidth,
            ControlPanelHeight
        ),
        "Birth"
    )
    currentX += SelectorWidth + Border

    deathSelector = Selector(
        pygame.Rect(
            currentX,
            currentY,
            SelectorWidth,
            ControlPanelHeight
        ),
        "Death"
    )
    currentX += SelectorWidth + Border

    lastStageTime = time()

    while True:
        
        ######################
        # Updating
        ######################

        for event in pygame.event.get():
            if event.type == pygame.QUIT or \
                (event.type == pygame.KEYDOWN and event.key == pygame.K_x):
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if randomizeButton.OnButton(event.pos):
                    field.Randomize()
                    
                elif clearButton.OnButton(event.pos):
                    field.Clear()
                    
                elif pauseButton.OnButton(event.pos):
                    paused = not paused

            field.HandleEvent(event)
            birthSelector.HandleEvent(event)
            deathSelector.HandleEvent(event)
 
        currentTime = time()
        if not paused and currentTime - lastStageTime > TimePerStage:
            lastStageTime = currentTime
            field.Progress(
                birthSelector.GetActiveValues(),
                deathSelector.GetActiveValues()
            )

        ########################
        # Drawing
        ########################

        Screen.fill(Grey(150))

        field.Draw(Screen)
        randomizeButton.Draw(Screen)
        clearButton.Draw(Screen)
        pauseButton.Draw(Screen, paused)
        birthSelector.Draw(Screen)
        deathSelector.Draw(Screen)

        pygame.display.update()

if __name__ == "__main__":
    Main()
