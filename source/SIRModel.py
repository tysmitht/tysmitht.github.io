"""
Not complete.
Goal is to add a graph event handler
Shows the value of the closest graph at its closest point
Kind of like desmos
"""

import pygame, os
from math import ceil, floor, inf, sqrt
from enum import Enum, auto
pygame.init()

# Position the screen
y = 100
x = 100
os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (x,y)

# Dimensions
GraphWidth = 1250
GraphHeight = 500
Border = 10
GraphBorder = 5
XAxisShift = 50
YAxisShift = 50
AxisThickness = 4
SemiMajorAxisThickness = 2
SemiMinorAxisThickness = 1
FunctionLineThickness = 3

SliderWidth = GraphWidth / 2 - Border / 2
SliderHeight = 100
SliderSpace = 10
SliderDotRadius = 12
SliderLineThickness = 3

ScreenWidth = round(GraphWidth + Border * 2)
ScreenHeight = round(GraphHeight + Border * 4 + SliderHeight * 2)

Screen = pygame.display.set_mode((ScreenWidth, ScreenHeight))

# Helper constants
HorizontalSemiMajorAxisCount = 8
HorizontalSemiMinorAxisCount = 16 # (Desired in between lines - 1) * HorizontalSemiMajorAxisCount
VerticalSemiMajorAxisCount = 20
VerticalSemiMinorInBetweenCount = 5
EvaluationResolution = 1 # for increasing accuracy of numaerical solving
GraphClickRange = 5

# Initial Values
SInitial = .99
IInitial = .01
RInitial = 0

# Colors
White = (255, 255, 255)
Grey200 = (200, 200, 200)
Grey175 = (175, 175, 175)
Grey150 = (150, 150, 150)
Grey125 = (125, 125, 125)
Grey100 =  (100, 100, 100)
Grey75 = (75, 75, 75)
Grey50 = (50, 50, 50)
Grey25 = (25, 25, 25)
Black = (0, 0, 0)
Blue = (44, 44, 177)
LightBlue = (203, 233, 246)
Red = (177, 44, 44)
Green = (44, 177, 44)

# Font
pygame.font.init()
DisplayFont = pygame.font.SysFont("couriernew", 500, bold=1)

class GraphType(Enum):
    Susceptible = auto()
    Infected = auto()
    Recovered = auto()

def _ResizeText(text, width, height, color, angle):
    # Create the text
    surface = DisplayFont.render(text, True, color)

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
    
def ResizeCenterText(text, width, height, x, y, color=Black, angle=0):
    surface = _ResizeText(text, width, height, color, angle)

    # Position the text
    rect = surface.get_rect()
    rect.center = (x, y)

    return surface, rect

def ResizeMidRightText(text, width, height, x, y, color=Black, angle=0):
    surface = _ResizeText(text, width, height, color, angle)

    # Position the text
    rect = surface.get_rect()
    rect.midright = (x, y)

    return surface, rect

def ResizeMidLeftText(text, width, height, x, y, color=Black, angle=0):
    surface = _ResizeText(text, width, height, color, angle)

    # Position the text
    rect = surface.get_rect()
    rect.midleft = (x, y)

    return surface, rect 

def ResizeTopLeftText(text, width, height, x, y, color=Black, angle=0):
    surface = _ResizeText(text, width, height, color, angle)

    # Position the text
    rect = surface.get_rect()
    rect.topleft = (x, y)

    return surface, rect

def ResizeMidTopText(text, width, height, x, y, color=Black, angle=0):
    surface = _ResizeText(text, width, height, color, angle)

    # Position the text
    rect = surface.get_rect()
    rect.midtop = (x, y)

    return surface, rect

class Slider:
    def __init__(self, x, y, w, h, text, color, minValue = 0, maxValue = 10, initial=.5):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

        self.color = color
        self.text = text
        self.slideAmt = initial
        self.min = minValue
        self.max = maxValue
        self.movingSlider = False

        self.hasUpdated = False

        self.slideSurface = pygame.Surface((self.w, self.h))

    def GetSlideValue(self):
        return self.min * (1 - self.slideAmt) + self.max * self.slideAmt

    def IsUpdated(self):
        ret = self.hasUpdated
        self.hasUpdated = False
        return ret

    def OnSlider(self, pos):
        if pos[0] < self.x + SliderSpace \
            or pos[0] > self.x + self.w - SliderSpace \
                or pos[1] < self.y + self.h * 3/4 - SliderDotRadius \
                    or pos[1] > self.y + self.h * 3/4 + SliderDotRadius: 
            return False
        return True 

    def AdjustSlideAmt(self, pos):
        currentSlideAmt = self.slideAmt

        # Determine the new x position
        leftX = self.x + SliderSpace + SliderDotRadius
        rightX = self.x + self.w - SliderSpace - SliderDotRadius
        self.slideAmt = (pos[0] - leftX) / (rightX - leftX)

        # Make sure the slide amount is in range correctly
        if self.slideAmt < 0:
            self.slideAmt = 0
        elif self.slideAmt > 1:
            self.slideAmt = 1

        # If the slide amt changed, update the slider
        if currentSlideAmt != self.slideAmt:
            self.UpdateSurface()

    def HandleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.OnSlider(event.pos):
                self.movingSlider = True
                self.AdjustSlideAmt(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP:
            self.movingSlider = False
        elif event.type == pygame.MOUSEMOTION:
            if self.movingSlider:
                self.AdjustSlideAmt(event.pos)

    def UpdateSurface(self):
        self.hasUpdated = True

        self.slideSurface.fill(Grey175)

        # Create and draw the text
        currentValue = self.slideAmt * (self.max - self.min) + self.min
        currentValue = float(round(currentValue, 2))
        currentValueStr = str(currentValue)
        while len(currentValueStr) < 3:
            currentValueStr = currentValueStr + "0"
        textToDraw = self.text + currentValueStr

        textSurface, textRect = ResizeMidLeftText(
            textToDraw, 
            self.w - SliderSpace * 2,
            self.h / 2,
            SliderSpace,
            SliderSpace + (self.h / 2) / 2
        )

        self.slideSurface.blit(textSurface, textRect)

        # Draw the bar
        pygame.draw.line(
            self.slideSurface,
            self.color,
            (
                SliderSpace + SliderDotRadius * 2,
                self.h * 3 / 4,
            ),
            (
                self.w - SliderSpace - SliderDotRadius * 2,
                self.h * 3 / 4,
            ),
            SliderLineThickness
        )

        # Draw the endpoints
        pygame.draw.circle(
            self.slideSurface,
            self.color,
            (
                round(SliderSpace + SliderDotRadius),
                round(self.h * 3 / 4)
            ),
            SliderDotRadius,
            SliderLineThickness
        )
        pygame.draw.circle(
            self.slideSurface,
            self.color,
            (
                round(self.w - SliderSpace - SliderDotRadius),
                round(self.h * 3 / 4)
            ),
            SliderDotRadius,
            SliderLineThickness
        )

        # Draw the current position
        leftX = SliderSpace + SliderDotRadius
        rightX = self.w - SliderSpace - SliderDotRadius
        currentX = leftX + self.slideAmt * (rightX - leftX)
        
        pygame.draw.circle(
            self.slideSurface,
            self.color,
            (
                round(currentX),
                round(self.h * 3 / 4)
            ),
            SliderDotRadius
        )

    def Draw(self, surface):
        # Draw the background
        surface.blit(
            self.slideSurface,
            (
                self.x,
                self.y
            )
        )

class Graph:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.graphInternalH = self.h - XAxisShift * 2
        self.graphInternalW = self.w - YAxisShift * 2

        # For drawing the numbers primarily
        self.maxY = 1
        self.minY = 0
        self.maxX = 10
        self.minX = 0

        # Collection of coordinates for the graphs
        self.sValues = []
        self.iValues = []
        self.rValues = []

        self.selectedGraph = None
        self.displayingCoordinate = False

        self.graphSurface = pygame.Surface((w, h))

    def UpdateSurface(self, transRate, recovRate, maxX):
        self.maxX = maxX

        # Determine the number of vertical semi-major and semi-minor axes
        semiMajorAxisCount = (ceil(self.maxX) - floor(self.minX))
        semiMinorAxisCount = (VerticalSemiMinorInBetweenCount + 1) * semiMajorAxisCount

        # Draw the graph background
        self.graphSurface.fill(Grey175)

        # Draw the semi-minor axis lines
        # Horizontal
        for i in range(HorizontalSemiMinorAxisCount + 1):
            pygame.draw.line(
                self.graphSurface,
                Grey100,
                (
                    YAxisShift,
                    self.h - XAxisShift - self.graphInternalH * i / HorizontalSemiMinorAxisCount
                ),
                (
                    self.w - YAxisShift,
                    self.h - XAxisShift - self.graphInternalH * i / HorizontalSemiMinorAxisCount
                ),
                SemiMinorAxisThickness
            )

        # Vertical
        for i in range(semiMinorAxisCount + 1):
            if ceil(self.maxX) > 20 and i % 2 == 1:
                continue

            pygame.draw.line(
                self.graphSurface,
                Grey100,
                (
                    YAxisShift + self.graphInternalW * i / semiMinorAxisCount,
                    XAxisShift
                ),
                (
                    YAxisShift + self.graphInternalW * i / semiMinorAxisCount,
                    self.h - XAxisShift
                ),
                SemiMinorAxisThickness
            )

        # Draw the major axis lines
        # Horizontal
        for i in range(HorizontalSemiMajorAxisCount + 1):
            # Draw the line
            pygame.draw.line(
                self.graphSurface,
                Grey50,
                (
                    YAxisShift,
                    self.h - XAxisShift - self.graphInternalH * i / HorizontalSemiMajorAxisCount
                ),
                (
                    self.w - YAxisShift,
                    self.h - XAxisShift - self.graphInternalH * i / HorizontalSemiMajorAxisCount
                ),
                SemiMajorAxisThickness
            )

            # Create and draw the semi-major axis labels
            number = i * (self.maxY - self.minY) / HorizontalSemiMajorAxisCount
            numStr = str(number)
            numStr = numStr[:5]
            while len(numStr) < 5:
                numStr = numStr + "0"

            h = self.graphInternalH / (2 * HorizontalSemiMajorAxisCount)
            numSurface, numRect = ResizeMidRightText(
                numStr, 
                YAxisShift - GraphBorder * 2, 
                h, 
                YAxisShift - GraphBorder,
                self.h - XAxisShift - self.graphInternalH * i / HorizontalSemiMajorAxisCount
            )

            self.graphSurface.blit(numSurface, numRect)

        # Vertical
        for i in range(semiMajorAxisCount + 1):
            # Skip odd points if the graph is too compressed
            if ceil(self.maxX) > 20 and i % 2 == 1:
                continue
            
            pygame.draw.line(
                self.graphSurface,
                Grey50,
                (
                    YAxisShift + self.graphInternalW * i / semiMajorAxisCount,
                    XAxisShift
                ),
                (
                    YAxisShift + self.graphInternalW * i / semiMajorAxisCount,
                    self.h - XAxisShift
                ),
                SemiMajorAxisThickness
            )

            # Create and draw the semi-major axis labels
            # number = i * (self.maxX - self.minX) / VerticalSemiMajorAxisCount
            number = i
            numStr = str(number)
            w = self.graphInternalW / (2 * VerticalSemiMajorAxisCount)
            if 0 <= number <= 9:
                w /= 2

            numSurface, numRect = ResizeMidTopText(
                numStr, 
                w, 
                XAxisShift - GraphBorder * 2, 
                YAxisShift + self.graphInternalW * i / semiMajorAxisCount,
                self.h - XAxisShift
            )

            self.graphSurface.blit(numSurface, numRect)

        # Draw the axes
        pygame.draw.line(
            self.graphSurface,
            Black,
            (
                YAxisShift,
                XAxisShift
            ),
            (
                YAxisShift,
                self.h - XAxisShift
            ),
            AxisThickness
        )
        pygame.draw.line(
            self.graphSurface,
            Black,
            (
                YAxisShift,
                self.h - XAxisShift
            ),
            (
                self.w - YAxisShift,
                self.h - XAxisShift
            ),
            AxisThickness
        )

        ##########################################
        # Draw the funtions onto the surface
        ##########################################

        self.sValues, self.iValues, self.rValues = EvaluateSystem(transRate, recovRate, self.minX, self.maxX, (self.maxX - self.minX) / self.graphInternalW)

        for i in range(len(self.sValues) - 1):
            # Draw the susceptible
            pygame.draw.line(
                self.graphSurface,
                Blue,
                (
                    round(self.sValues[i][0] * self.graphInternalW / (ceil(self.maxX) - floor(self.minX)) + YAxisShift),
                    self.h - self.sValues[i][1] * self.graphInternalH - XAxisShift
                ),
                (
                    round(self.sValues[i+1][0] * self.graphInternalW / (ceil(self.maxX) - floor(self.minX)) + YAxisShift),
                    self.h - self.sValues[i+1][1] * self.graphInternalH - XAxisShift
                ),
                FunctionLineThickness
            )
            # Draw the infected
            pygame.draw.line(
                self.graphSurface,
                Red,
                (
                    round(self.iValues[i][0] * self.graphInternalW / (ceil(self.maxX) - floor(self.minX)) + YAxisShift),
                    self.h - self.iValues[i][1] * self.graphInternalH - XAxisShift
                ),
                (
                    round(self.iValues[i+1][0] * self.graphInternalW / (ceil(self.maxX) - floor(self.minX)) + YAxisShift),
                    self.h - self.iValues[i+1][1] * self.graphInternalH - XAxisShift
                ),
                FunctionLineThickness
            )
            # Draw the recovered
            pygame.draw.line(
                self.graphSurface,
                Green,
                (
                    round(self.rValues[i][0] * self.graphInternalW / (ceil(self.maxX) - floor(self.minX)) + YAxisShift),
                    self.h - self.rValues[i][1] * self.graphInternalH - XAxisShift
                ),
                (
                    round(self.rValues[i+1][0] * self.graphInternalW / (ceil(self.maxX) - floor(self.minX)) + YAxisShift),
                    self.h - self.rValues[i+1][1] * self.graphInternalH - XAxisShift
                ),
                FunctionLineThickness
            )

    def Draw(self, surface):
        surface.blit(
            self.graphSurface, 
            (
                self.x, 
                self.y
            )
        )

def Distance(p1, p2):
    return sqrt(
        (p1[0] - p2[0]) ** 2 +
        (p1[1] - p2[1]) ** 2
    )

def EvaluateSystem(transRate, recovRate, minT, maxT, dt):
    currentS = SInitial
    currentI = IInitial
    currentR = RInitial

    sValues = dict()
    iValues = dict()
    rValues = dict()

    sValues[0] = currentS
    iValues[0] = currentI
    rValues[0] = currentR

    dt /= EvaluationResolution

    t = 0
    reachedRange = False
    while t < maxT:
        # Determine the next x value to try
        if not reachedRange:
            if t + dt > minT:
                reachedRange = True
                t = minT
            else:
                t += dt
        else:
            t += dt

        dSdt = -transRate * currentS * currentI
        dIdt = transRate * currentS * currentI - recovRate * currentI
        dRdt = recovRate * currentI

        currentS += dSdt * dt
        currentI += dIdt * dt
        currentR += dRdt * dt

        sValues[t] = currentS
        iValues[t] = currentI
        rValues[t] = currentR
        
    sReturn = []
    iReturn = []
    rReturn = []
    t = minT
    # dt *= EvaluationResolution
    while t <= maxT:
        sReturn.append((t, sValues[t]))
        iReturn.append((t, iValues[t]))
        rReturn.append((t, rValues[t]))
        t += dt

    return sReturn, iReturn, rReturn

transSlider = Slider(
    Border,
    Border + GraphHeight + Border,
    SliderWidth,
    SliderHeight,
    "Trans. Rate: ",
    Black,
)
transSlider.UpdateSurface()

recovSlider = Slider(
    Border * 2 + SliderWidth,
    Border + GraphHeight + Border,
    SliderWidth,
    SliderHeight,
    "Recov. Rate: ",
    Black,
    minValue=.01, 
    maxValue=3
)
recovSlider.UpdateSurface()

maxTSlider = Slider(
    Border,
    Border + GraphHeight + Border + SliderHeight + Border,
    SliderWidth + Border + SliderWidth,
    SliderHeight,
    "Max. Time: ",
    Black,
    minValue = 1,
    maxValue=40,
)
maxTSlider.UpdateSurface()

infectionGraph = Graph(Border, Border, GraphWidth, GraphHeight)
infectionGraph.UpdateSurface(
    transSlider.GetSlideValue(), 
    recovSlider.GetSlideValue(),
    maxTSlider.GetSlideValue()
)

def Main():
    while True:

        ####################
        # Updating
        ####################

        for event in pygame.event.get():
            if event.type == pygame.QUIT or \
                (event.type == pygame.KEYDOWN and event.key == pygame.K_x):
                pygame.quit()
                quit()
            transSlider.HandleEvent(event)
            recovSlider.HandleEvent(event)
            maxTSlider.HandleEvent(event)
            # infectionGraph.HandleEvent(event)

        if transSlider.IsUpdated():
            infectionGraph.UpdateSurface(
                transSlider.GetSlideValue(), 
                recovSlider.GetSlideValue(),
                maxTSlider.GetSlideValue()
            )

        elif recovSlider.IsUpdated():
            infectionGraph.UpdateSurface(
                transSlider.GetSlideValue(), 
                recovSlider.GetSlideValue(),
                maxTSlider.GetSlideValue()
            )

        elif maxTSlider.IsUpdated():
            infectionGraph.UpdateSurface(
                transSlider.GetSlideValue(), 
                recovSlider.GetSlideValue(),
                maxTSlider.GetSlideValue()
            )


        #################
        # Drawing
        #################

        Screen.fill(Grey50)

        infectionGraph.Draw(Screen)

        transSlider.Draw(Screen)
        recovSlider.Draw(Screen)
        maxTSlider.Draw(Screen)

        pygame.display.update()


if __name__ == "__main__":
    Main()