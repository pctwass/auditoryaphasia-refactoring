from psychopy import visual
from psychopy.visual import line as visual_line


class Crosshair(object):
    def __init__(self, window:visual.Window, length:float=0.125, line_width:float=4):
        self.window = window
        self.length = length
        self.line_width = line_width

        self.line_hor = visual_line.Line(window, start=[-length/2, 0], end=[length/2, 0], lineWidth=line_width)
        self.line_ver = visual_line.Line(window, start=[0, -length/2], end=[0, length/2], lineWidth=line_width)


    def show(self):
        self.draw()
        self.window.flip()

    def hide(self):
        self.window.flip()

    def draw(self):
        self.line_hor.draw()
        self.line_ver.draw()