from psychopy import visual


class Crosshair(object):
    def __init__(self, win, length=0.125, line_width=4):
        self.length = length
        self.line_width = line_width
        self.win = win

        self.line_hor = visual.line.Line(win, start=[-length/2, 0], end=[length/2, 0], lineWidth=line_width)
        self.line_ver = visual.line.Line(win, start=[0, -length/2], end=[0, length/2], lineWidth=line_width)


    def show(self):
        self.draw()
        self.win.flip()

    def hide(self):
        self.win.flip()

    def draw(self):
        self.line_hor.draw()
        self.line_ver.draw()