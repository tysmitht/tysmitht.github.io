"""
Inspired by a CGP Grey video about different plane boarding methods
https://www.youtube.com/watch?v=oAHbLRjF0vo
"""
import pygame, os
from time import time
from random import shuffle
from math import sin, cos, pi

pygame.init()

os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (25, 50)

# Dimensions
SeatSize = 40
EntranceWidth = 100
AisleHeight = SeatSize
Border = 10
PeopleRadius = 15
TimerRadius = 10
SliderSpace = 10
SliderDotRadius = 10
SliderLineThickness = 3
ScreenWidth = SeatSize * 16 + EntranceWidth + Border * 17
ScreenHeight = SeatSize * 6 + AisleHeight + Border * 8

# Colors
def Grey(n):
    return (n, n, n)
Black = Grey(0)
White = Grey(255)
FloorColor = Grey(175) # Under seats
AisleColor = Grey(150)
SeatColor = (47, 89, 190)
PeopleColor = [
    (249, 214, 39),
    (246, 89, 253),
    (115, 227, 43),
    (0, 125, 255),
    (247, 137, 62),
    (38, 239, 247),
    (0, 221, 22),
    (117, 172, 186),
    (148, 197, 94),
    (253, 75, 148),
    (227, 0, 30),
    (12, 180, 255),
]

# Font
pygame.font.init()
DisplayFont = pygame.font.SysFont("Arial", 50)

# Misc. Helpers
PersonSpeed = 100
StowTime = 1.75
FinishedDisplayTime = 5

PeopleImages = dict()
def GetPersonImage(color):
    # Check if its already been created
    global PeopleImages
    if color in PeopleImages:
        return PeopleImages[color]

    # Create the iamge of a person
    personImage = pygame.Surface((PeopleRadius * 2, PeopleRadius * 2))
    personImage.fill((255, 0, 0))
    personImage.set_colorkey((255, 0, 0))
    pygame.draw.circle(
        personImage,
        color,
        (
            round(personImage.get_width() / 2),
            round(personImage.get_height() / 2)
        ),
        PeopleRadius
    )
    pygame.draw.circle(
        personImage,
        Black,
        (
            round(personImage.get_width() * .5),
            round(personImage.get_height() * .35)
        ),
        2
    )
    pygame.draw.circle(
        personImage,
        Black,
        (
            round(personImage.get_width() * .85),
            round(personImage.get_height() * .35)
        ),
        2
    )
    pygame.draw.line(
        personImage,
        Black,
        (
            round(personImage.get_width() * .45),
            round(personImage.get_height() * .75)
        ),
        (
            round(personImage.get_width() * .85),
            round(personImage.get_height() * .75)
        ),
        2
    )

    PeopleImages[color] = personImage
    return personImage

# For drawing rounded rectangles
def RoundRect(surface, rect, color, rad=20, border=0, inside=(0,0,0,0)):
    """
    Draw a rect with rounded corners to surface.  Argument rad can be specified
    to adjust curvature of edges (given in pixels).  An optional border
    width can also be supplied; if not provided the rect will be filled.
    Both the color and optional interior color (the inside argument) support
    alpha.
    """
    rect = pygame.Rect(rect)
    zeroed_rect = rect.copy()
    zeroed_rect.topleft = 0,0
    image = pygame.Surface(rect.size).convert_alpha()
    image.fill((0,0,0,0))
    _RenderRegion(image, zeroed_rect, color, rad)
    if border:
        zeroed_rect.inflate_ip(-2*border, -2*border)
        _RenderRegion(image, zeroed_rect, inside, rad)
    surface.blit(image, rect)

def _RenderRegion(image, rect, color, rad):
    """Helper function for round_rect."""
    corners = rect.inflate(-2*rad, -2*rad)
    for attribute in ("topleft", "topright", "bottomleft", "bottomright"):
        pygame.draw.circle(image, color, getattr(corners,attribute), rad)
    image.fill(color, rect.inflate(-2*rad,0))
    image.fill(color, rect.inflate(0,-2*rad))

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

def ResizeMidTopText(text, width, height, x, y, color=Black, angle=0, font=DisplayFont, outlineWidth=-1, outlineColor=None):
    surface = _ResizeText(text, width, height, color, angle, font, outlineWidth, outlineColor)

    # Position the text
    rect = surface.get_rect()
    rect.midtop = (x, y)

    return surface, rect

class IncrementalSlider:
    def __init__(self, rect, text, increments, color=Black):
        self.rect = rect

        self.color = color
        self.text = text

        self.slideIndex = 0
        self.increments = increments

        self.movingSlider = False

        self.slideSurface = pygame.Surface((self.rect.w, self.rect.h))

        self.UpdateSurface()

    def GetSlideValue(self):
        return self.increments[self.slideIndex]

    def OnSlider(self, pos):
        if pos[0] < self.rect.x + SliderSpace \
            or pos[0] > self.rect.x + self.rect.w - SliderSpace \
                or pos[1] < self.rect.y + self.rect.h * 3/4 - SliderDotRadius \
                    or pos[1] > self.rect.y + self.rect.h * 3/4 + SliderDotRadius: 
            return False
        return True 

    def AdjustSlideIndex(self, pos):
        currentIndex = self.slideIndex

        # Determine the new x position
        leftX = self.rect.x + SliderSpace + SliderDotRadius
        rightX = self.rect.x + self.rect.w - SliderSpace - SliderDotRadius
        slidePos = (pos[0] - leftX) / (rightX - leftX)

        # Make sure the slide amount is in range correctly
        if slidePos < 0:
            slidePos = 0
        elif slidePos > 1:
            slidePos = 1

        # Would prefer an O(1) algorithm instead
        # This is O(len(self.increments))
        minDistance = 2 # Sepcifically greater than 1
        for i in range(len(self.increments)):
            dist = abs(slidePos - i / (len(self.increments) - 1))
            if dist < minDistance:
                minDistance = dist
                self.slideIndex = i

        # If the slide index changed, update the slider
        if currentIndex != self.slideIndex:
            self.UpdateSurface()

    def SetSlideIndex(self, element):
        """
        Sets the index appropriately if element is in self.increments
        """
        currentIndex = self.slideIndex
        if element in self.increments:
            self.slideIndex = self.increments.index(element)
        else:
            self.slideIndex = 0
        
        if currentIndex != self.slideIndex:
            self.UpdateSurface()

    def HandleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.OnSlider(event.pos):
                self.movingSlider = True
                self.AdjustSlideIndex(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP:
            self.movingSlider = False
        elif event.type == pygame.MOUSEMOTION:
            if self.movingSlider:
                self.AdjustSlideIndex(event.pos)

    def UpdateSurface(self, altText=None):
        self.slideSurface.fill(Grey(175))

        pygame.draw.rect(
            self.slideSurface,
            Black,
            (
                0,
                0,
                self.rect.w,
                self.rect.h
            ),
            1
        )

        # Create and draw the text
        if altText == None:
            textToDraw = self.text + str(self.GetSlideValue())
        else:
            textToDraw = self.text + str(altText)

        textSurface, textRect = ResizeMidLeftText(
            textToDraw, 
            None,
            self.rect.h / 2,
            SliderSpace,
            (self.rect.h / 2) / 2
        )

        self.slideSurface.blit(textSurface, textRect)

        # Draw the bar
        pygame.draw.line(
            self.slideSurface,
            self.color,
            (
                SliderSpace + SliderDotRadius * 2,
                self.rect.h * 3 / 4,
            ),
            (
                self.rect.w - SliderSpace - SliderDotRadius * 2,
                self.rect.h * 3 / 4,
            ),
            SliderLineThickness
        )

        # Draw the endpoints
        pygame.draw.circle(
            self.slideSurface,
            self.color,
            (
                round(SliderSpace + SliderDotRadius),
                round(self.rect.h * 3 / 4)
            ),
            SliderDotRadius,
            SliderLineThickness if 0 != self.slideIndex else 0
        )

        pygame.draw.circle(
            self.slideSurface,
            self.color,
            (
                round(self.rect.w - SliderSpace - SliderDotRadius),
                round(self.rect.h * 3 / 4)
            ),
            SliderDotRadius,
            SliderLineThickness if len(self.increments) - 1 != self.slideIndex else 0
        )

        # Draw the intermediate points
        leftX = SliderSpace + SliderDotRadius
        rightX = self.rect.w - SliderSpace - SliderDotRadius
        for i in range(1, len(self.increments) - 1):
            currentX = leftX + ((i / (len(self.increments) - 1)) * (rightX - leftX))

            pygame.draw.circle(
                self.slideSurface,
                self.color,
                (
                    round(currentX),
                    round(self.rect.h * 3 / 4)
                ),
                SliderDotRadius // 2 if i != self.slideIndex else SliderDotRadius
            )

    def Draw(self, surface):
        # Draw the background
        surface.blit(
            self.slideSurface,
            (
                self.rect.x,
                self.rect.y
            )
        )

class Button:
    def __init__(self, msg, rect, standardColor, hoverColor=None):
        self.rect = rect

        self.standardColor = standardColor
        if hoverColor is None:
            self.hoverColor = standardColor
        else:
            self.hoverColor = hoverColor

        self.textSurf, self.textRect = ResizeCenterText(
            msg,
            rect.w,
            rect.h,
            rect.x + rect.w // 2,
            rect.y + rect.h // 2
        )
        
        self.clicked = False

    def Draw(self, surface):
        if self.OnButton(pygame.mouse.get_pos()):
            RoundRect(surface, self.rect, self.hoverColor)
            RoundRect(surface, self.rect, Black, border=2)
        else:
            RoundRect(surface, self.rect, self.standardColor)
            RoundRect(surface, self.rect, Black, border=2)

        surface.blit(self.textSurf, self.textRect)

    def OnButton(self, pos):
        return self.rect.collidepoint(pos)

    def HandleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.OnButton(event.pos):
                self.clicked = True

class CountdownTimer:
    def __init__(self, _pos):
        self.pos = _pos
        self.totalTime = StowTime
        self.timeLeft = StowTime

        self.completed = False

    def Update(self, elapsed):
        if not self.completed:
            self.timeLeft -= elapsed
            if self.timeLeft <= 0:
                self.completed = True

    def Draw(self, surface):
        # Draw the timer background
        pygame.draw.circle(
            surface,
            Grey(125),
            (
                round(self.pos.x),
                round(self.pos.y)
            ),
            TimerRadius
        )

        # Draw the timer filled section
        angle = round((self.timeLeft / self.totalTime) * 360)
        cx = round(self.pos.x)
        cy = round(self.pos.y)

        # Start list of polygon points
        p = [(cx, cy)]

        # Get points on arc
        for n in range(angle):
            x = cx + round(TimerRadius * cos(n * pi / 180))
            y = cy + round(TimerRadius * sin(n * pi / 180))
            p.append((x, y))
        p.append((cx, cy))

        # Draw pie segment
        if len(p) > 2:
            pygame.draw.polygon(
                surface, 
                (143, 43, 7), 
                p
            )

        # Draw the Border
        pygame.draw.circle(
            surface,
            Black,
            (
                round(self.pos.x),
                round(self.pos.y)
            ),
            TimerRadius + 1,
            1
        )

class DigitalTimer:
    def __init__(self, _rect):
        self.rect = _rect
        self.time = 0
        self.paused = False

    def Update(self, elapsed):
        if not self.paused:
            self.time += elapsed

    def Draw(self, surface):
        minutes = int(self.time // 60)
        seconds = int(self.time % 60)
        if seconds <= 9:
            seconds = F"0{seconds}"

        text = F"{minutes}:{seconds}"

        textSurf, textRect = ResizeMidLeftText(
            text,
            None,
            self.rect.h,
            self.rect.x + Border,
            self.rect.y + self.rect.h // 2
        )

        RoundRect(
            surface,
            self.rect,
            Grey(175),
            rad=5
        )
        RoundRect(
            surface,
            self.rect,
            Black,
            border=1,
            rad=5
        )
        surface.blit(textSurf, textRect)

class Person:
    def __init__(self, _scene, _seatNumber, _pos, _color):
        self.scene = _scene
        self.seatNumber = _seatNumber
        self.pos = _pos
        self.vel = pygame.Vector2(1, 0)
        self.vel.scale_to_length(PersonSpeed)

        self.stowing = False
        self.stowed = False
        self.seated = False

        self.timer = None

        self.image = GetPersonImage(_color).copy() # copy() is probably unnecessary, just to be safe

    def Draw(self, surface):
        surface.blit(
            self.image,
            (
                round(self.pos.x - self.image.get_width() / 2),
                round(self.pos.y - self.image.get_height() / 2),
            )
        )

        if self.stowing:
            self.timer.draw(surface)

    def Update(self, elapsed):
        if not any([self.stowing, self.seated]):
            if not self.scene.PersonTooClose(self.pos) or self.stowed:
                self.pos += self.vel * elapsed
                seatPos = self.scene.seatToPos[self.seatNumber]
                if abs(seatPos.x - self.pos.x) < PeopleRadius / 10:
                    if not self.stowed:
                        self.stowing = True
                        if seatPos.y > self.pos.y:
                            self.pos.y += Border // 2
                        else:
                            self.pos.y -= Border // 2
                        self.timer = CountdownTimer(
                            pygame.Vector2(
                                self.pos.x,
                                self.pos.y - PeopleRadius - TimerRadius - 2
                            )
                        )
                    else:
                        if abs(seatPos.y - self.pos.y) < PeopleRadius / 10:
                            self.pos = seatPos
                            self.seated = True

        elif self.stowing:
            self.timer.Update(elapsed)
            if self.timer.completed:
                self.stowing = False
                self.stowed = True
                seatPos = self.scene.seatToPos[self.seatNumber]
                self.vel = seatPos - self.pos
                self.vel.scale_to_length(PersonSpeed)
                self.image = pygame.transform.flip(
                    self.image,
                    True, False
                )

class BoardingScene:
    def __init__(self, _surface, _planeSurface, _passengers, _seatToPos):
        self.surface = _surface
        self.planeSurface = _planeSurface

        self.people = _passengers
        for person in self.people:
            person.scene = self

        self.seatToPos = _seatToPos

        self.finishedTimer = None
        self.clock = DigitalTimer(
            pygame.Rect(
                Border,
                Border,
                EntranceWidth - Border * 2,
                40
            )

        )
        self.quitting = False

    def Draw(self):
        self.surface.fill(Black)
        self.surface.blit(
            self.planeSurface,
            (0, 0)
        )

        for person in self.people:
            person.draw(self.surface)
        self.clock.Draw(self.surface)

    def PersonTooClose(self, pos):
        for person in self.people:
            if person.pos == pos:
                continue

            if person.stowed:
                continue
        
            if person.pos.x < pos.x:
                continue
        
            distVector = person.pos - pos
            if distVector.magnitude() < PeopleRadius + Border + PeopleRadius:
                return True
                
        return False

    def AllPeopleStopped(self):
        for person in self.people:
            if not person.seated:
                return False
        return True

    def Update(self, elapsed):
        if self.AllPeopleStopped():
            self.clock.paused = True
            if self.finishedTimer == None:
                self.finishedTimer = CountdownTimer(pygame.Vector2())
                self.finishedTimer.totalTime = FinishedDisplayTime
                self.finishedTimer.timeLeft = FinishedDisplayTime
            else:
                self.finishedTimer.Update(elapsed)
                if self.finishedTimer.completed:
                    self.quitting = True

        else:
            for person in self.people:
                person.update(elapsed)
            self.clock.Update(elapsed)

    def Run(self):
        lastUpdateTime = time()
        while not self.quitting:

            ##############
            # Updating
            ##############

            for event in pygame.event.get():
                if event.type == pygame.QUIT or \
                    (event.type == pygame.KEYDOWN and event.key == pygame.K_x):
                    quit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_e:
                        self.quitting = True
                        break

            currentTime = time()
            elapsed = currentTime - lastUpdateTime
            lastUpdateTime = currentTime

            self.Update(elapsed)

            #############
            # Drawing
            #############

            self.Draw()

            pygame.display.update()

class SceneController:
    def __init__(self):
        self.surface = pygame.display.set_mode((ScreenWidth, ScreenHeight))

        self.titleSurf, self.titleRect = ResizeMidTopText(
            "Plane Boarding Simulation",
            None,
            round(ScreenHeight * .25),
            round(ScreenWidth * .5),
            Border,
            color=White,
            outlineWidth=2,
            outlineColor=Black
        )

        self.slider = IncrementalSlider(
            pygame.Rect(
                round(ScreenWidth * .15),
                round(ScreenHeight * .25),
                round(ScreenWidth * .7),
                round(ScreenHeight * .2)
            ),
            "Boarding Method: ",
            [
                "Random",
                "Back to Front",
                "Front to Back",
                "Window to Aisle Random",
                "Window to Aisle Perfected",
                "Steffen Perfect",
                "Steffen Modified"
            ]
        )

        self.runSimulationButton = Button(
            "Run Simulation",
            pygame.Rect(
                round(ScreenWidth * .25),
                round(ScreenHeight * .55),
                round(ScreenWidth * .5),
                round(ScreenHeight * .25)
            ),
            Grey(175),
            Grey(200)
        )

        self.planeSurface = pygame.Surface((ScreenWidth, ScreenHeight))

        self.seatToPos = dict()
        lastSeatNumber = 1

        # Draw the plane seats
        self.planeSurface.fill(FloorColor)
        for x in range(16):
            # Top row of seats
            for y in range(3):
                screenX = EntranceWidth + x * (SeatSize + Border) + Border
                screenY = y * (SeatSize + Border) + Border

                self.seatToPos[lastSeatNumber] = (
                    pygame.Vector2(
                        screenX + SeatSize // 2,
                        screenY + SeatSize // 2
                    )
                )
                lastSeatNumber += 1

                RoundRect(
                    self.planeSurface,
                    pygame.Rect(
                        screenX, screenY, SeatSize, SeatSize
                    ),
                    SeatColor,
                    rad=5
                )

                # seatNumSurf, seatNumRect = ResizeCenterText(
                #     str(lastSeatNumber - 1),
                #     SeatSize,
                #     SeatSize,
                #     screenX + SeatSize // 2,
                #     screenY + SeatSize // 2
                # )
                # self.planeSurface.blit(seatNumSurf, seatNumRect)

            # Draw the Aisle
            pygame.draw.rect(
                self.planeSurface,
                AisleColor,
                (
                    0, 
                    0,
                    EntranceWidth,
                    ScreenHeight
                )
            )
            pygame.draw.rect(
                self.planeSurface,
                AisleColor,
                (
                    0, 
                    3 * (SeatSize + Border) + Border,
                    ScreenWidth,
                    AisleHeight
                )
            )

            # Bottom of row of seats
            for y in range(3, 6):
                screenX = EntranceWidth + x * (SeatSize + Border) + Border
                screenY = y * (SeatSize + Border) + AisleHeight + Border * 2

                self.seatToPos[lastSeatNumber] = (
                    pygame.Vector2(
                        screenX + SeatSize // 2,
                        screenY + SeatSize // 2
                    )
                )
                lastSeatNumber += 1

                RoundRect(
                    self.planeSurface,
                    pygame.Rect(
                        screenX, screenY, SeatSize, SeatSize
                    ),
                    SeatColor,
                    rad=5
                )

    def CreatePassengers(self, order):
        currentX = -PeopleRadius * 2 - Border
        currentY = ScreenHeight / 2

        people = []
        for seatNum, color in order:
            people.append(
                Person(
                    self,
                    seatNum,
                    pygame.Vector2(
                        currentX,
                        currentY
                    ),
                    color
                )
            )
            currentX -= PeopleRadius * 2 + Border

        return people

    def RandomBoarding(self):
        seatOrder = [(i, PeopleColor[0]) for i in range(1, 16*6 + 1)]
        shuffle(seatOrder)
        
        return self.CreatePassengers(seatOrder)

    def BackToFrontBoarding(self):
        group4 = [(i, PeopleColor[0]) for i in range(73, 96 + 1)]
        group3 = [(i, PeopleColor[1]) for i in range(49, 72 + 1)]
        group2 = [(i, PeopleColor[2]) for i in range(25, 48 + 1)]
        group1 = [(i, PeopleColor[3]) for i in range(1, 24 + 1)]

        shuffle(group4)
        shuffle(group3)
        shuffle(group2)
        shuffle(group1)

        seatOrder = group4 + group3 + group2 + group1

        returnself.CreatePassengers(seatOrder)

    def FrontToBackBoarding(self):
        group4 = [(i, PeopleColor[4]) for i in range(73, 96 + 1)]
        group3 = [(i, PeopleColor[5]) for i in range(49, 72 + 1)]
        group2 = [(i, PeopleColor[6]) for i in range(25, 48 + 1)]
        group1 = [(i, PeopleColor[7]) for i in range(1, 24 + 1)]

        shuffle(group4)
        shuffle(group3)
        shuffle(group2)
        shuffle(group1)

        seatOrder = group1 + group2 + group3 + group4
        
        return self.CreatePassengers(seatOrder)

    def WindowToAisleRandomBoarding(self):
        windowGroup = [(i, PeopleColor[8]) for i in range(1, 96 + 1) if i % 6 == 1 or i % 6 == 0]
        middleGroup = [(i, PeopleColor[9]) for i in range(1, 96 + 1) if i % 6 == 2 or i % 6 == 5]
        aisleGroup = [(i, PeopleColor[10]) for i in range(1, 96 + 1) if i % 6 == 3 or i % 6 == 4]

        shuffle(windowGroup)
        shuffle(middleGroup)
        shuffle(aisleGroup)

        seatOrder = windowGroup + middleGroup + aisleGroup
        
        return self.CreatePassengers(seatOrder)

    def WindowToAislePerfectedBoarding(self):
        windowGroupA = [(i, PeopleColor[0]) for i in range(1, 96 + 1) if i % 6 == 1][::-1]
        windowGroupB = [(i, PeopleColor[1]) for i in range(1, 96 + 1) if i % 6 == 0][::-1]
        middleGroupA = [(i, PeopleColor[2]) for i in range(1, 96 + 1) if i % 6 == 2][::-1]
        middleGroupB = [(i, PeopleColor[3]) for i in range(1, 96 + 1) if i % 6 == 5][::-1]
        aisleGroupA = [(i, PeopleColor[4]) for i in range(1, 96 + 1) if i % 6 == 3][::-1]
        aisleGroupB = [(i, PeopleColor[5]) for i in range(1, 96 + 1) if i % 6 == 4][::-1]

        seatOrder = windowGroupA + windowGroupB + middleGroupA + middleGroupB + aisleGroupA + aisleGroupB
        
        return self.CreatePassengers(seatOrder)

    def SteffenModifiedBoarding(self):
        groups = [
            [(i, PeopleColor[0]) for i in range(1, 96 + 1) if i % 12 in {0, 11, 10}][::-1],
            [(i, PeopleColor[1]) for i in range(1, 96 + 1) if i % 12 in {7, 8, 9}][::-1],
            [(i, PeopleColor[2]) for i in range(1, 96 + 1) if i % 12 in {6, 5, 4}][::-1],
            [(i, PeopleColor[3]) for i in range(1, 96 + 1) if i % 12 in {1, 2, 3}][::-1],
        ]

        seatOrder = []
        for group in groups:
            shuffle(group)
            seatOrder.extend(group)
        
        return self.CreatePassengers(seatOrder)

    def SteffenPerfectBoarding(self):
        groups = [
            [(i, PeopleColor[0]) for i in range(1, 96 + 1) if i % 12 == 0][::-1],
            [(i, PeopleColor[1]) for i in range(1, 96 + 1) if i % 12 == 7][::-1],
            [(i, PeopleColor[2]) for i in range(1, 96 + 1) if i % 12 == 6][::-1],
            [(i, PeopleColor[3]) for i in range(1, 96 + 1) if i % 12 == 1][::-1],
            [(i, PeopleColor[4]) for i in range(1, 96 + 1) if i % 12 == 11][::-1],
            [(i, PeopleColor[5]) for i in range(1, 96 + 1) if i % 12 == 8][::-1],
            [(i, PeopleColor[6]) for i in range(1, 96 + 1) if i % 12 == 5][::-1],
            [(i, PeopleColor[7]) for i in range(1, 96 + 1) if i % 12 == 2][::-1],
            [(i, PeopleColor[8]) for i in range(1, 96 + 1) if i % 12 == 10][::-1],
            [(i, PeopleColor[9]) for i in range(1, 96 + 1) if i % 12 == 9][::-1],
            [(i, PeopleColor[10]) for i in range(1, 96 + 1) if i % 12 == 4][::-1],
            [(i, PeopleColor[11]) for i in range(1, 96 + 1) if i % 12 == 3][::-1]
        ]

        seatOrder = []
        for group in groups:
            seatOrder.extend(group)

        return self.CreatePassengers(seatOrder)

    def Run(self):

        while True:

            ##############
            # Updating
            ##############

            for event in pygame.event.get():
                if event.type == pygame.QUIT or \
                    (event.type == pygame.KEYDOWN and event.key == pygame.K_x):
                    quit()

                self.slider.HandleEvent(event)
                self.runSimulationButton.HandleEvent(event)

            if self.runSimulationButton.clicked:
                self.runSimulationButton.clicked = False
                if self.slider.GetSlideValue() == "Random":
                    passengers = self.RandomBoarding()
                elif self.slider.GetSlideValue() == "Back to Front":
                    passengers = self.BackToFrontBoarding()
                elif self.slider.GetSlideValue() == "Front to Back":
                    passengers = self.FrontToBackBoarding()
                elif self.slider.GetSlideValue() == "Window to Aisle Random":
                    passengers = self.WindowToAisleRandomBoarding()
                elif self.slider.GetSlideValue() == "Window to Aisle Perfected":
                    passengers = self.WindowToAislePerfectedBoarding()
                elif self.slider.GetSlideValue() == "Steffen Modified":
                    passengers = self.SteffenModifiedBoarding()
                elif self.slider.GetSlideValue() == "Steffen Perfect":
                    passengers = self.SteffenPerfectBoarding()

                BoardingScene(self.surface, self.planeSurface, passengers, self.seatToPos).Run()

            #############
            # Drawing
            #############

            self.surface.fill(Grey(150))

            self.surface.blit(self.titleSurf, self.titleRect)
            self.slider.Draw(self.surface)
            self.runSimulationButton.Draw(self.surface)

            pygame.display.update()

if __name__ == "__main__":
    SceneController().Run()