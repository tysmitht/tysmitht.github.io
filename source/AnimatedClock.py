import pygame
from pygame import gfxdraw
import datetime
from math import pi

pygame.init()

clock = pygame.time.Clock()

# Dimensions
ScreenSize = 600
LineWidth = 10
Border = 20
ClockBorder = 8

Screen = pygame.display.set_mode((ScreenSize, ScreenSize))

# Colors
def Grey(n):
    return (n, n, n)
White = Grey(255)
Black = Grey(0)
Red = (225, 25, 25)
Green = (25, 225, 25)
Blue = (25, 25, 225)
HourColor = (89, 255, 0)
MinuteColor = (255, 0, 217)
SecondColor = (38, 0, 255)

# Conversion ratio from degrees to radians
DToR = pi / 180

# Offset for the angles
AngleOffset = -90 # Degrees

# Which segments are active for different values
# on a seven segment display
# Standard arrangement (a, b, c, d, e, f, g)

SevenSegmentActivationsKey =  {
    0  : (1, 1, 1, 1, 1, 1, 0),
    1  : (0, 1, 1, 0, 0, 0, 0),
    2  : (1, 1, 0, 1, 1, 0, 1),
    3  : (1, 1, 1, 1, 0, 0, 1),
    4  : (0, 1, 1, 0, 0, 1, 1),
    5  : (1, 0, 1, 1, 0, 1, 1),
    6  : (1, 0, 1, 1, 1, 1, 1),
    7  : (1, 1, 1, 0, 0, 0, 0),
    8  : (1, 1, 1, 1, 1, 1, 1),
    9  : (1, 1, 1, 0, 0, 1, 1),
    "p": (1, 1, 0, 0, 1, 1, 1),
    "a": (1, 1, 1, 0, 1, 1, 1),
}

def DrawArc(surface, center, radius, startAngle, stopAngle, color, width=1):
    if startAngle == stopAngle:
        return

    startAngle = round(startAngle % 360)
    stopAngle = round(stopAngle % 360)

    for dy in [-1, 1]:
        for dx in [-1, 1]:
            x,y = center
            x += dx
            y += dy
            for r in range(radius - width // 2, radius + width // 2):
                if startAngle == stopAngle:
                    gfxdraw.circle(surface, x, y, r, color)
                else:
                    gfxdraw.arc(surface, x, y, r, startAngle, stopAngle, color)

def DrawSevenSegmentNumber(surface, rect, activeColor, inactiveColor, drawableValue):
    """
    Hard coded like crazy!
    Shape:
        + A +
        F   B
        + G +
        E   C
        + D +
    """
    activations = SevenSegmentActivationsKey[drawableValue]
    ogWidth = 340
    ogHeight = 575

    # A
    pygame.draw.polygon(
        surface,
        activeColor if activations[0] else inactiveColor,
        [
            (round(rect.x + rect.w * 58 / ogWidth), round(rect.y + rect.h * 55 / ogHeight)),
            (round(rect.x + rect.w * 99 / ogWidth), round(rect.y + rect.h * 91 / ogHeight)),
            (round(rect.x + rect.w * 242 / ogWidth), round(rect.y + rect.h * 91 / ogHeight)),
            (round(rect.x + rect.w * 278 / ogWidth), round(rect.y + rect.h * 55 / ogHeight)),
            (round(rect.x + rect.w * 242 / ogWidth), round(rect.y + rect.h * 19 / ogHeight)),
            (round(rect.x + rect.w * 99 / ogWidth), round(rect.y + rect.h * 19 / ogHeight))
        ]
    )

    # B
    pygame.draw.polygon(
        surface,
        activeColor if activations[1] else inactiveColor,
        [
            (round(rect.x + rect.w * 287 / ogWidth), round(rect.y + rect.h * 64 / ogHeight)),
            (round(rect.x + rect.w * 251 / ogWidth), round(rect.y + rect.h * 100 / ogHeight)),
            (round(rect.x + rect.w * 251 / ogWidth), round(rect.y + rect.h * 244 / ogHeight)),
            (round(rect.x + rect.w * 287 / ogWidth), round(rect.y + rect.h * 280 / ogHeight)),
            (round(rect.x + rect.w * 323 / ogWidth), round(rect.y + rect.h * 244 / ogHeight)),
            (round(rect.x + rect.w * 323 / ogWidth), round(rect.y + rect.h * 100 / ogHeight))
        ]
    )

    # C
    pygame.draw.polygon(
        surface,
        activeColor if activations[2] else inactiveColor,
        [
            (round(rect.x + rect.w * 287 / ogWidth), round(rect.y + rect.h * 296 / ogHeight)),
            (round(rect.x + rect.w * 251 / ogWidth), round(rect.y + rect.h * 332 / ogHeight)),
            (round(rect.x + rect.w * 251 / ogWidth), round(rect.y + rect.h * 475 / ogHeight)),
            (round(rect.x + rect.w * 287 / ogWidth), round(rect.y + rect.h * 511 / ogHeight)),
            (round(rect.x + rect.w * 323 / ogWidth), round(rect.y + rect.h * 475 / ogHeight)),
            (round(rect.x + rect.w * 323 / ogWidth), round(rect.y + rect.h * 332 / ogHeight))
        ]
    )

    # D
    pygame.draw.polygon(
        surface,
        activeColor if activations[3] else inactiveColor,
        [
            (round(rect.x + rect.w * 58 / ogWidth), round(rect.y + rect.h * 520 / ogHeight)),
            (round(rect.x + rect.w * 99 / ogWidth), round(rect.y + rect.h * 556 / ogHeight)),
            (round(rect.x + rect.w * 242 / ogWidth), round(rect.y + rect.h * 556 / ogHeight)),
            (round(rect.x + rect.w * 278 / ogWidth), round(rect.y + rect.h * 520 / ogHeight)),
            (round(rect.x + rect.w * 242 / ogWidth), round(rect.y + rect.h * 484 / ogHeight)),
            (round(rect.x + rect.w * 99 / ogWidth), round(rect.y + rect.h * 484 / ogHeight))
        ]
    )

    # E
    pygame.draw.polygon(
        surface,
        activeColor if activations[4] else inactiveColor,
        [
            (round(rect.x + rect.w * 53 / ogWidth), round(rect.y + rect.h * 296 / ogHeight)),
            (round(rect.x + rect.w * 17 / ogWidth), round(rect.y + rect.h * 332 / ogHeight)),
            (round(rect.x + rect.w * 17 / ogWidth), round(rect.y + rect.h * 475 / ogHeight)),
            (round(rect.x + rect.w * 53 / ogWidth), round(rect.y + rect.h * 511 / ogHeight)),
            (round(rect.x + rect.w * 89 / ogWidth), round(rect.y + rect.h * 475 / ogHeight)),
            (round(rect.x + rect.w * 89 / ogWidth), round(rect.y + rect.h * 332 / ogHeight))
        ]
    )

    # F
    pygame.draw.polygon(
        surface,
        activeColor if activations[5] else inactiveColor,
        [
            (round(rect.x + rect.w * 53 / ogWidth), round(rect.y + rect.h * 64 / ogHeight)),
            (round(rect.x + rect.w * 17 / ogWidth), round(rect.y + rect.h * 100 / ogHeight)),
            (round(rect.x + rect.w * 17 / ogWidth), round(rect.y + rect.h * 244 / ogHeight)),
            (round(rect.x + rect.w * 53 / ogWidth), round(rect.y + rect.h * 280 / ogHeight)),
            (round(rect.x + rect.w * 89 / ogWidth), round(rect.y + rect.h * 244 / ogHeight)),
            (round(rect.x + rect.w * 89 / ogWidth), round(rect.y + rect.h * 100 / ogHeight))
        ]
    )

    # G
    pygame.draw.polygon(
        surface,
        activeColor if activations[6] else inactiveColor,
        [
            (round(rect.x + rect.w * 58 / ogWidth), round(rect.y + rect.h * 288 / ogHeight)),
            (round(rect.x + rect.w * 99 / ogWidth), round(rect.y + rect.h * 323 / ogHeight)),
            (round(rect.x + rect.w * 242 / ogWidth), round(rect.y + rect.h * 323 / ogHeight)),
            (round(rect.x + rect.w * 278 / ogWidth), round(rect.y + rect.h * 288 / ogHeight)),
            (round(rect.x + rect.w * 242 / ogWidth), round(rect.y + rect.h * 251 / ogHeight)),
            (round(rect.x + rect.w * 99 / ogWidth), round(rect.y + rect.h * 251 / ogHeight))
        ]
    )

def DrawDigitalClock(surface, rect, activeColor, inactiveColor, hours, minutes, seconds):
    """
    This draws the time as a digital clock using DrawSevenSegmentNumber(...)
    Only draws numbers and the colons
    Also hard coded heavily
    """
    dotRadius = round(rect.h / 20)
    for dotX in [rect.x + rect.w * 1 / 3, rect.x + rect.w * 2 / 3]:
        for dotY in [rect.y + rect.h * .3, rect.y + rect.h * .7]:
            pygame.draw.circle(
                surface,
                activeColor,
                (
                    round(dotX),
                    round(dotY)
                ),
                dotRadius
            )

    hours = str(hours)
    if len(hours) < 2:
        hours = "0" + hours

    minutes = str(minutes)
    if len(minutes) < 2:
        minutes = "0" + minutes

    seconds = str(seconds)
    if len(seconds) < 2:
        seconds = "0" + seconds

    numY = rect.y + rect.h * .15
    # numW = (rect.w / 3 - ClockBorder * 3) / 2
    numW = (rect.w / 3 - ClockBorder * 4) / 2
    numH =  rect.h * .7

    for i, num in enumerate([hours, minutes, seconds]):
        numX = rect.x + ClockBorder + i * rect.w / 3
        for digit in num:
            DrawSevenSegmentNumber(
                surface,
                pygame.Rect(
                    numX, numY,
                    numW, numH
                ),
                activeColor,
                inactiveColor,
                int(digit)
            )
            numX += numW + ClockBorder
    
class Selector:
    def __init__(self, rect, activeColor, inactiveColor):
        self.rect = rect
        self.activeColor = activeColor
        self.inactiveColor = inactiveColor

        self.state = True

    def Draw(self, surface):
        # Draw the flattened oval background
        color = self.activeColor if self.state else self.inactiveColor
        circleRad = self.rect.h / 2
        circleCenterX = [circleRad, self.rect.w - circleRad]
        for dx in circleCenterX:
            pygame.draw.circle(
                surface,
                color,
                (
                    round(self.rect.x + dx),
                    round(self.rect.y + self.rect.h / 2)
                ),
                round(circleRad)
            )

        pygame.draw.rect(
            surface,
            color,
            (
                round(self.rect.x + circleCenterX[0]),
                round(self.rect.y),
                round(self.rect.w - circleCenterX[0] - circleRad),
                round(self.rect.h)
            )
        )

        # Draw the sliding piece
        if self.state:
            slideX = circleCenterX[1]
        else:
            slideX = circleCenterX[0]

        pygame.draw.circle(
            surface,
            Grey(150),
            (
                round(self.rect.x + slideX),
                round(self.rect.y + self.rect.h / 2),
            ),
            round(circleRad)
        )

    def HandleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.state = not self.state

def Main():

    clockStateSelector = Selector(
        pygame.Rect(
            ScreenSize / 2 - 50,
            ScreenSize / 2 + 50 + Border,
            100,
            50
        ),
        Blue,
        Grey(75)
    )

    while True:

        ##############
        # Updating
        ##############

        for event in pygame.event.get():
            if event.type == pygame.QUIT or \
                (event.type == pygame.KEYDOWN and event.key == pygame.K_x):
                quit()

            clockStateSelector.HandleEvent(event)

        clock.tick(60)

        now = datetime.datetime.now()
        hours, minutes, seconds = now.hour, now.minute, now.second

        if clockStateSelector.state:
            # Check for afternoon or not
            if hours >= 12:
                afternoon = True
            else:
                afternoon = False
            
            # Adjust it to the correct value
            hours %= 12
            if hours == 0:
                hours = 12

        #############
        # Drawing
        #############

        Screen.fill(Grey(100))

        currentRadius = ScreenSize / 2 - Border

        # Seconds
        DrawArc(
            Screen,
            (
                round(ScreenSize / 2),
                round(ScreenSize / 2)
            ),
            round(currentRadius),
            AngleOffset,
            AngleOffset + seconds * 6,
            SecondColor,
            LineWidth
        )
        currentRadius -= LineWidth + Border

        # Minutes
        DrawArc(
            Screen,
            (
                round(ScreenSize / 2),
                round(ScreenSize / 2)
            ),
            round(currentRadius),
            AngleOffset,
            AngleOffset + minutes * 6,
            MinuteColor,
            LineWidth
        )
        currentRadius -= LineWidth + Border

        # Hours
        DrawArc(
            Screen,
            (
                round(ScreenSize / 2),
                round(ScreenSize / 2)
            ),
            round(currentRadius),
            AngleOffset,
            AngleOffset + hours * 360 / (12 if clockStateSelector.state else 24),
            HourColor,
            LineWidth
        )
        currentRadius -= LineWidth + Border

        DrawDigitalClock(
            Screen,
            pygame.Rect(
                ScreenSize / 2 - 175,
                ScreenSize / 2 - 50,
                350,
                100
            ),
            Red,
            Grey(100),
            hours, minutes, seconds
        )

        clockStateSelector.Draw(Screen)

        if clockStateSelector.state:
            if afternoon:
                code = "p"
            else:
                code = "a"

            numH = 50
            numW = numH * .6
            
            DrawSevenSegmentNumber(
                Screen,
                pygame.Rect(
                    ScreenSize / 2 + 50 + Border,
                    ScreenSize / 2 + 50 + Border,
                    numW,
                    numH
                ),
                Red,
                Grey(100),
                code
            )

        pygame.display.update()

if __name__ == "__main__":
    Main()

