import pygame
import re
import math
import time

pygame.init()

# Dimensions
ScreenWidth = 1080
ScreenHeight = 720
Border = 10
WindowHeight = 40
ShadowWidth = 3

# Colors
def Grey(n):
    return (n, n, n)
Black = Grey(0)
White = Grey(255)
DarkBorderColor = Grey(75)
LightBorderColor = Grey(125)

# Font
pygame.font.init()
DisplayFont = pygame.font.SysFont("Arial", 70)

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

class ExpressionTree:
    def is_number(s):
        try:
            float(s)
            return True
        except:
            return False

    class Node:
        def __init__(self, data, _type):
            self.data = data
            self.left = None
            self.right = None

            self.type = _type

        def Solve(self):
            if self.type == "number":
                return self.data

                raise ValueError(f"{self.data} is not a number")

            elif self.type == "function":
                childEval = self.left.Solve()
                if self.data == "sin":
                    return math.sin(childEval)
                elif self.data == "cos":
                    return math.cos(childEval)
                elif self.data == "tan":
                    return math.tan(childEval)
                elif self.data == "csc":
                    return 1 / math.sin(childEval)
                elif self.data == "sec":
                    return 1 / math.cos(childEval)
                elif self.data == "cot":
                    return 1 / math.tan(childEval)
                elif self.data == "asin":
                    return math.asin(childEval)
                elif self.data == "acos":
                    return math.acos(childEval)
                elif self.data == "atan":
                    return math.atan(childEval)
                elif self.data == "sqrt":
                    return math.sqrt(childEval)
                elif self.data == "ln":
                    return math.log(childEval)
                elif self.data == "log":
                    return math.log10(childEval)
                elif self.data == "log2":
                    return math.log2(childEval)
                elif self.data == "abs":
                    return math.fabs(childEval)
                elif self.data == "!":
                    return math.factorial(childEval)
                else:
                    raise TypeError(f"{self.data} is not a function")

            elif self.type == "operator":
                leftEval = self.left.Solve()
                rightEval = self.right.Solve()
                if self.data == "+":
                    return leftEval + rightEval
                elif self.data == "-":
                    return leftEval - rightEval
                elif self.data == "*":
                    return leftEval * rightEval
                elif self.data == "/":
                    return leftEval / rightEval
                elif self.data == "^":
                    return leftEval ** rightEval
                else:
                    raise TypeError(f"{self.data} is not an operator")

            else:
                raise TypeError(f"{self.type} is not a valid expression node type")

    def __init__(self, expression):
        tokens = re.findall("[\^+/*()-]|\!|abs|sqrt|csc|sec|cot|asin|acos|atan|sin|cos|tan|ln|log2|log|e|pi|\d*\.?\d*", expression)
    
        i = 0
        while i < len(tokens):
            if tokens[i] == "":
                tokens = tokens[:i] + tokens[i+1:]
                continue
            i += 1

        self.functions = {"!", "abs", "sqrt", "csc", "sec", "cot", "asin", "acos", "atan", "sin", "cos", "tan", "ln", "log2", "log"}

        self.root = self.Create(tokens)

    def Solve(self):
        return self.root.Solve()

    def Create(self, tokens):
        if tokens[0] == "-":
            tokens = [0] + tokens

        while "(" in tokens:
            bracketStack = []
            parenLeftIndex = tokens.index("(")

            for i in range(parenLeftIndex + 1, len(tokens)):
                if tokens[i] == "(":
                    bracketStack.append("(")
                elif tokens[i] == ")":
                    if len(bracketStack) == 0:
                        parenRightIndex = i
                        break
                    else:
                        bracketStack.pop()
            
            parenTree = self.Create(tokens[parenLeftIndex + 1:parenRightIndex])

            tokens = tokens[:parenLeftIndex] + [parenTree] + tokens[parenRightIndex + 1:]

        # Work on the constants and numbers
        for i in range(len(tokens)):
            if tokens[i] == "e":
                tokens[i] = math.e
            elif tokens[i] == "pi":
                tokens[i] = math.pi

            if ExpressionTree.is_number(tokens[i]):
                tokens[i] = ExpressionTree.Node(float(tokens[i]), "number")

        # Deal with the functions
        for func in self.functions:
            while func in tokens:
                funcIndex = tokens.index(func)
                funcTree = ExpressionTree.Node(func, "function")
                if func == "!":
                    funcTree.left = tokens[funcIndex - 1]
                    tokens[funcIndex] = funcTree
                    tokens = tokens[:funcIndex - 1] + [funcTree] + tokens[funcIndex + 1:]
                else:
                    funcTree.left = tokens[funcIndex + 1]
                    tokens[funcIndex] = funcTree
                    tokens = tokens[:funcIndex] + [funcTree] + tokens[funcIndex + 2:]

        # Operators
        # Ordered by precedence
        #   First block: ^
        #   Second block: */
        #   Third block: +-
        i = 0
        while i < len(tokens):
            if tokens[i] == "^":
                operatorTree = ExpressionTree.Node(tokens[i], "operator")
                operatorTree.left = tokens[i - 1]
                operatorTree.right = tokens[i + 1]
                tokens = tokens[:i - 1] + [operatorTree] + tokens[i + 2:]
                i -= 1
                continue

            i += 1

        i = 0
        while i < len(tokens):
            if tokens[i] in {"*", "/"}:
                operatorTree = ExpressionTree.Node(tokens[i], "operator")
                operatorTree.left = tokens[i - 1]
                operatorTree.right = tokens[i + 1]
                tokens = tokens[:i - 1] + [operatorTree] + tokens[i + 2:]
                i -= 1
                continue

            i += 1

        i = 0
        while i < len(tokens):
            if tokens[i] in {"+", "-"}:
                operatorTree = ExpressionTree.Node(tokens[i], "operator")
                operatorTree.left = tokens[i - 1]
                operatorTree.right = tokens[i + 1]
                tokens = tokens[:i - 1] + [operatorTree] + tokens[i + 2:]
                i -= 1
                continue

            i += 1

        return tokens[0]

class Button:
    DefaultStandardColor = Grey(100)
    DefaultPressedColor = Grey(125)
    def __init__(self, msg, rect, standardColor=None, pressedColor=None):
        self.rect = rect

        if standardColor == None:
            self.standardColor = Button.DefaultStandardColor
        if pressedColor == None:
            self.pressedColor = Button.DefaultPressedColor

        self.textSurf, self.textRect = ResizeCenterText(
            msg,
            round(rect.w * .9),
            rect.h,
            rect.x + rect.w // 2,
            rect.y + rect.h // 2
        )
        
        self.clicked = False
        self.pressed = False

    def Draw(self, surface):
        color = self.standardColor
        if self.pressed:
            color = self.pressedColor

        pygame.draw.rect(
            surface,
            color,
            self.rect
        )
        
        pygame.draw.lines(
            surface,
            LightBorderColor,
            False,
            [
                (
                    self.rect.x,
                    self.rect.y + self.rect.h
                ),
                (
                    self.rect.x,
                    self.rect.y
                ),
                (
                    self.rect.x + self.rect.w,
                    self.rect.y
                )
            ],
            ShadowWidth
        )
        
        pygame.draw.lines(
            surface,
            DarkBorderColor,
            False,
            [
                (
                    self.rect.x,
                    self.rect.y + self.rect.h
                ),
                (
                    self.rect.x + self.rect.w,
                    self.rect.y + self.rect.h
                ),
                (
                    self.rect.x + self.rect.w,
                    self.rect.y
                ),
            ],
            ShadowWidth
        )

        surface.blit(self.textSurf, self.textRect)

    def OnButton(self, pos):
        return self.rect.collidepoint(pos)

    def HandleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.OnButton(event.pos):
                self.clicked = True
                self.pressed = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.pressed = False
        elif event.type == pygame.MOUSEMOTION:
            if not self.OnButton(event.pos):
                self.pressed = False

class InputBox:
    ValidCharacters = set(" 0123456789.()^*/+-!abssqrtsincostancscseccotasinacosatanlnloglog2epi")

    CharSurfWidthMapping = dict()
    for character in ValidCharacters:
        cSurf, cRect = ResizeCenterText(
            character,
            None,
            WindowHeight,
            0, 0
        )
        CharSurfWidthMapping[character] = (cSurf, cRect.w)
    del character, cSurf, cRect

    HeldKeyFirstTimer = .8
    HeldKeyRepeatedCharacterDelay = .05

    def __init__(self, rect, scene, text="", backgroundColor=(175, 175, 175)):
        self.rect = rect
        self.scene = scene

        self.backgroundColor = backgroundColor

        self.text = text

        self.cursorIndex = 0

        self.inputSurface = pygame.Surface((self.rect.w, self.rect.h))
        self.surfaceNeedsUpdate = False
        self.UpdateSurface()

        self.backspacing = False
        self.rightArrow = False
        self.leftArrow = False
        self.keyHoldTimer = -1

    def SetText(self, text):
        self.text = text
        if self.cursorIndex > len(self.text):
            self.cursorIndex = len(self.text)
        self.UpdateSurface()

    def Write(self, text):
        for char in text:
            if char in InputBox.ValidCharacters:
                self.text = self.text[:self.cursorIndex] + char + self.text[self.cursorIndex:]
                self.cursorIndex += 1
                self.surfaceNeedsUpdate = True

    def Clear(self):
        self.SetText("")

    def _PerformBackspace(self, once=False):
        self.text = self.text[:max(0, self.cursorIndex - 1)] + self.text[self.cursorIndex:]
        if self.cursorIndex >= 1: self.cursorIndex -= 1  
        if not once: self.backspacing = True
        self.surfaceNeedsUpdate = True

    def _PerformRightArrow(self):
        if self.cursorIndex < len(self.text):
            self.cursorIndex += 1
        self.rightArrow = True

    def _PerformLeftArrow(self):
        if self.cursorIndex >= 1:
            self.cursorIndex -= 1
        self.leftArrow = True

    def HandleEvent(self, event):
        if event.type == pygame.KEYUP:
            self.backspacing = False
            self.rightArrow = False
            self.leftArrow = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.scene.DoSolve(self.text)

            elif event.key == pygame.K_BACKSPACE:
                self._PerformBackspace()
                self.keyHoldTimer = InputBox.HeldKeyFirstTimer

            elif event.key == pygame.K_RIGHT:
                self._PerformRightArrow()
                self.keyHoldTimer = InputBox.HeldKeyFirstTimer

            elif event.key == pygame.K_LEFT:
                self._PerformLeftArrow()
                self.keyHoldTimer = InputBox.HeldKeyFirstTimer

            else:
                if event.unicode in InputBox.ValidCharacters:
                    self.text = self.text[:self.cursorIndex] + event.unicode + self.text[self.cursorIndex:]
                    self.cursorIndex += 1
                    self.surfaceNeedsUpdate = True
            
        if self.surfaceNeedsUpdate:
            self.UpdateSurface()

    def Update(self, elapsed):
        if any([self.backspacing, self.rightArrow, self.leftArrow]):
            self.keyHoldTimer -= elapsed
            if self.keyHoldTimer < 0:
                self.keyHoldTimer += InputBox.HeldKeyRepeatedCharacterDelay
                if self.backspacing:
                    self._PerformBackspace()
                elif self.rightArrow:
                    self._PerformRightArrow()
                elif self.leftArrow:
                    self._PerformLeftArrow()

    def Draw(self, surface):
        if self.surfaceNeedsUpdate:
            self.UpdateSurface()
        surface.blit(
            self.inputSurface,
            (
                self.rect.x,
                self.rect.y
            )
        )

        # Draw the blinking cursor
        # Done here to limit redrawing of rest of surface
        if (time.time() % .7)  > .3:
            x = self.rect.x + 5 + sum([InputBox.CharSurfWidthMapping[self.text[i]][1] for i in range(self.cursorIndex)])
            pygame.draw.line(
                surface,
                Black,
                (
                    x,
                    round(self.rect.y + self.rect.h * .1)
                ),
                (
                    x,
                    round(self.rect.y + self.rect.h * .9)
                ),
                2
            )

    def UpdateSurface(self):
        self.surfaceNeedsUpdate = False

        self.inputSurface.fill(self.backgroundColor)

        pygame.draw.lines(
            self.inputSurface,
            LightBorderColor,
            False,
            [
                (
                    0,
                    self.rect.h - 1
                ),
                (
                    self.rect.w - 1,
                    self.rect.h - 1
                ),
                (
                    self.rect.w - 1,
                    0
                )
            ],
            ShadowWidth
        )

        pygame.draw.lines(
            self.inputSurface,
            DarkBorderColor,
            False,
            [
                (
                    0,
                    self.rect.h
                ),
                (
                    0,
                    0
                ),
                (
                    self.rect.w,
                    0
                )
            ],
            ShadowWidth
        )

        currentX = 5
        for char in self.text:
            self.inputSurface.blit(
                InputBox.CharSurfWidthMapping[char][0],
                (
                    currentX,
                    0
                )
            )
            currentX += InputBox.CharSurfWidthMapping[char][1]

class ResultMemory:
    LineHeight = 25
    def __init__(self, rect, backgroundColor=(175, 175, 175)):
        self.rect = rect
        self.backgroundColor = backgroundColor

        self.memorySurface = pygame.Surface((self.rect.w, self.rect.h))

        self.charSurfSizeMapping = dict()
        
        self.entries = []

        self.UpdateSurface()

    def Clear(self):
        self.entries = []
        self.UpdateSurface()

    def GetCharData(self, char):
        if char not in self.charSurfSizeMapping:
            surf, rect = ResizeCenterText(
                char,
                None,
                ResultMemory.LineHeight,
                0, 0
            )
            self.charSurfSizeMapping[char] = (surf, rect.w)

        return self.charSurfSizeMapping[char]

    def AddEntry(self, expr, result):
        if len(self.entries) > 0 and self.entries[0] == (str(expr), str(result)):
            return

        if len(self.entries) > 0 and self.entries[0] == ("Error", ""):
            self.entries.pop(0)

        self.entries = [(str(expr), str(result))] + self.entries

        self.UpdateSurface()

    def UpdateSurface(self):
        self.memorySurface.fill(self.backgroundColor)

        pygame.draw.lines(
            self.memorySurface,
            LightBorderColor,
            False,
            [
                (
                    0,
                    self.rect.h - 1
                ),
                (
                    self.rect.w - 1,
                    self.rect.h - 1
                ),
                (
                    self.rect.w - 1,
                    0
                )
            ],
            ShadowWidth
        )

        pygame.draw.lines(
            self.memorySurface,
            DarkBorderColor,
            False,
            [
                (
                    0,
                    self.rect.h
                ),
                (
                    0,
                    0
                ),
                (
                    self.rect.w,
                    0
                )
            ],
            ShadowWidth
        )

        i = 0
        currentY = 0
        for expr, result in self.entries:
            currentX = 5
            for char in expr:
                surf, width = self.GetCharData(char)
                self.memorySurface.blit(surf, (currentX, currentY))
                currentX += width

            currentY += ResultMemory.LineHeight

            currentX = self.rect.w - 5
            for char in result[::-1]:
                surf, width = self.GetCharData(char)
                self.memorySurface.blit(surf, (currentX - width, currentY))
                currentX -= width

            currentY += ResultMemory.LineHeight

            i += 1

    def Draw(self, surface):
        surface.blit(
            self.memorySurface,
            (
                self.rect.x,
                self.rect.y
            )
        )

class CalculatorScene:
    def __init__(self):
        self.surface = pygame.display.set_mode((ScreenWidth, ScreenHeight))

        self.clock = pygame.time.Clock()

        self.inputField = InputBox(
            pygame.Rect(
                Border,
                Border,
                round((ScreenWidth - Border * 3) * .65),
                WindowHeight
            ),
            self
        )

        self.memory = ResultMemory(
            pygame.Rect(
                Border * 2 + self.inputField.rect.w,
                Border,
                round(ScreenWidth - Border * 3) * .35,
                ScreenHeight - Border * 2
            )
        )

        self.buttons = dict()

        buttonNames = [
            ["sin",  "cos",  "tan",  "CE",   "C",  "Del", "="], 
            ["csc",  "sec",  "cot",  "sqrt", "^2", "^",   "/"], 
            ["asin", "acos", "atan", "7",    "8",  "9",   "*"], 
            ["ln",   "log",  "log2", "4",    "5",  "6",   "-"], 
            ["1/x",  "e^x",  "abs",  "1",    "2",  "3",   "+"],
            ["pi",   "e",    "!",    "0",    "(",  ")",   "."]
        ]

        buttonHeight = round((ScreenHeight - Border * 8 - self.inputField.rect.h) / 6)
        buttonWidth = round((ScreenWidth - Border * 9 - self.memory.rect.w) / 7)

        currentY = Border * 2 + self.inputField.rect.h
        for row in buttonNames:
            currentX = Border
            for button in row:
                self.buttons[button] = Button(
                    button,
                    pygame.Rect(
                        currentX,
                        currentY,
                        buttonWidth,
                        buttonHeight
                    )
                )
                currentX += buttonWidth + Border
            currentY += buttonHeight + Border

    def DoSolve(self, expr):
        try:
            res = ExpressionTree(expr).Solve()
            if int(res) == res:
                res = int(res)
            self.memory.AddEntry(expr, res)
        except:
            self.memory.AddEntry("Error", "")

    def Draw(self):
        self.surface.fill(Grey(50))

        self.inputField.Draw(self.surface)
        self.memory.Draw(self.surface)

        for button in self.buttons.values():
            button.Draw(self.surface)

    def HandleEvent(self, event):
        self.inputField.HandleEvent(event)

        for name, button in self.buttons.items():
            button.HandleEvent(event)
            if button.clicked:
                button.clicked = False
                if name == "CE":
                    self.inputField.Clear()
                elif name == "C":
                    self.inputField.Clear()
                    self.memory.Clear()
                elif name == "Del":
                    self.inputField._PerformBackspace(True)
                elif name == "=":
                    self.DoSolve(self.inputField.text)
                elif name == "1/x":
                    self.inputField.SetText("1/(" + self.inputField.text + ")")
                elif name == "e^x":
                    self.inputField.SetText("e^(" + self.inputField.text + ")")
                else:
                    self.inputField.Write(name)

    def Update(self, elapsed):
        self.inputField.Update(elapsed)

    def Run(self):

        lastUpdateTime = time.time()

        while True:

            self.clock.tick(60)

            ##############
            # Updating
            ##############

            for event in pygame.event.get():
                if event.type == pygame.QUIT or \
                    (event.type == pygame.KEYDOWN and event.key == pygame.K_x):
                    quit()

                self.HandleEvent(event)

            currentTime = time.time()
            elapsed = currentTime - lastUpdateTime
            lastUpdateTime = currentTime
            self.Update(elapsed)

            #############
            # Drawing
            #############

            self.Draw()

            pygame.display.update()

if __name__ == "__main__":
    CalculatorScene().Run()

