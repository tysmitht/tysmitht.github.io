import pygame
from math import pi, cos, sin
from time import time

pygame.init()

# Dimensions
ScreenSize = 500
Border = 10
CircleRadius = (ScreenSize - 7 * Border) // (6 * 2)

Screen = pygame.display.set_mode((ScreenSize, ScreenSize))

# Colors
def Grey(n):
    return (n, n, n)
Black = Grey(0)
White = Grey(255)
CircleColors = [ 
    (229, 25, 74),
    (245, 130, 49),
    (60, 179, 75),
    (67, 100, 216),
    (239, 50, 230)
]

# Speed
BaseSpeed = pi / 8 # Radians per second


def AverageColor(a, b):
    return (
        (a[0] + b[0]) // 2,
        (a[1] + b[1]) // 2,
        (a[2] + b[2]) // 2
    )

class Circle:
    def __init__(self, center, color, speed, direction):
        self.center = center
        self.color = color
        self.speed = speed
        self.theta = 0
        self.dire = direction


    def Update(self, elapsed):
        self.theta += self.speed * elapsed
        if self.theta >= 2*pi:
            self.theta -= 2 * pi

    def Reset(self):
        self.theta = 0

    def GetCirclePoint(self):
        return (
            round(self.center[0] + CircleRadius * cos(self.theta)),
            round(self.center[1] + CircleRadius * sin(self.theta))
        )

    def GetX(self):
        return self.GetCirclePoint()[0]

    def GetY(self):
        return self.GetCirclePoint()[1]

    def Draw(self, surface):
        pygame.draw.circle(
            surface,
            self.color,
            self.center,
            CircleRadius,
            1
        )

        circlePoint = self.GetCirclePoint()

        # pygame.draw.circle(
        #     surface,
        #     White,
        #     circlePoint,
        #     3
        # )

        if self.dire == "h":
            outsidePoint = (
                ScreenSize + 1, circlePoint[1]
            )
        else:
            outsidePoint = (
                circlePoint[0], ScreenSize + 1
            )


        pygame.draw.line(
            surface,
            White,
            circlePoint,
            outsidePoint,
            1
        )

class Curve:
    def __init__(self, xCircle, yCircle):
        self.xCircle = xCircle
        self.yCircle = yCircle
        self.color = AverageColor(xCircle.color, yCircle.color)
        self.points = set()

    def Update(self):
        self.points.add(
            (
                round(self.xCircle.GetX()),
                round(self.yCircle.GetY())
            )
        )

    def Reset(self):
        self.points = set()

    def Draw(self, surface):
        for point in self.points:
            surface.set_at(point, self.color)


def Main():

    verticalCircles = [
        Circle(
            (
                (Border + CircleRadius) * 2 + CircleRadius + i * (Border + 2 * CircleRadius),
                Border + CircleRadius
            ),
            color,
            BaseSpeed * (i+1),
            "v"
        )
        for i, color in enumerate(CircleColors)
    ]

    horizontalCircles = [
        Circle(
            (
                Border + CircleRadius,
                (Border + CircleRadius) * 2 + CircleRadius + i * (Border + 2 * CircleRadius)
            ),
            color,
            BaseSpeed * (i+1),
            "h"
        )
        for i, color in enumerate(CircleColors)
    ]

    curves = []
    for vert in verticalCircles:
        for hori in horizontalCircles:
            curves.append(Curve(vert, hori))

    lastUpdateTime = time()
    totalTime = 0

    while True:

        ######################
        # Updating
        ######################

        for event in pygame.event.get():
            if event.type == pygame.QUIT or \
                (event.type == pygame.KEYDOWN and event.key == pygame.K_x):
                quit()

        currentTime = time()
        elapsed = currentTime - lastUpdateTime
        lastUpdateTime = currentTime
        totalTime += elapsed

        if totalTime * BaseSpeed > 2 * pi:
            totalTime = 0
            for circle in verticalCircles+horizontalCircles:
                circle.Reset()

            for curve in curves:
                curve.Reset()


        for circle in verticalCircles+horizontalCircles:
            circle.Update(elapsed)

        for curve in curves:
            curve.Update()

        #########################
        # Drawing
        #########################

        Screen.fill(Black)

        for curve in curves:
            curve.Draw(Screen)

        for circle in verticalCircles+horizontalCircles:
            circle.Draw(Screen)

        pygame.display.update()

if __name__ == "__main__":
    Main()


