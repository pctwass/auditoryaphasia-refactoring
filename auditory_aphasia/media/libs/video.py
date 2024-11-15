from psychopy import visual, core
from psychopy.visual import line, circle
import numpy
import os
import sys

BACKGROUND_COLOR = [-1, -1, -1]  # 0, 0, 0
FOREGROUND_COLOR = [1, 1, 1]  # 255, 255, 255
HIGHLIGHT_COLOR = [0.59375, -1, -1]  # 204, 0, 0

SIZE_SMILEY = [0.5]
SIZE_EYE_OPEN_CLOSE = [1.0]
SIZE_DANCING_GIF = [0.7]

PATH_TO_IMAGES = os.path.join(os.getcwd(), "images")
print("Path to Image Files : " + PATH_TO_IMAGES)

class VideoInterface(object):
    def __init__(self, number_of_speakers=2, fullscreen_mode=False, display_size=[640, 480],
                 window_position=[100, 100], units='height'):
        self.number_of_speakers = number_of_speakers
        self.fullscreen_mode = fullscreen_mode
        self.display_size = display_size
        self.window_position = window_position
        self.units = units

    def show_screen(self):
        self.win = visual.Window(self.display_size, color=BACKGROUND_COLOR, fullscr=self.fullscreen_mode,
                                 pos=self.window_position, units=self.units)
        self.smiley = visual.ImageStim(win=self.win, image=os.path.join(PATH_TO_IMAGES, 'smiley_transparent.png'),
                                       size=SIZE_SMILEY)
        self.eyes_open = visual.ImageStim(win=self.win, image=os.path.join(PATH_TO_IMAGES, 'eyesOpen.jpg'),
                                          size=SIZE_EYE_OPEN_CLOSE)
        self.eyes_close = visual.ImageStim(win=self.win, image=os.path.join(PATH_TO_IMAGES, 'eyesClosed.jpg'),
                                           size=SIZE_EYE_OPEN_CLOSE)
        self.dancing_gif = visual.ImageStim(win=self.win, size=SIZE_DANCING_GIF)
        self.cross_hair = CrossHair(self.win)
        self.speakers = Speakers(self.win)


    def hide_screen(self):
        self.win.close()

    def show_smiley(self):
        self.smiley.draw()
        self.win.flip()

    def hide_smiley(self):
        self.smiley.clearTextures()
        self.win.flip()

    def show_eyes_open_close(self, show_eyes):
        if show_eyes.lower() == "open":
            self.eyes_open.draw()
        elif show_eyes.lower() == "close":
            self.eyes_close.draw()
        else:
            print("Error : Argument of show_eyes_open_close() has to be 'open' or 'close'.")
            sys.exit()
        self.win.flip()

    def hide_eyes_open_close(self, show_eyes):
        if show_eyes.lower() == "open":
            self.eyes_open.clearTextures()
        elif show_eyes.lower() == "close":
            self.eyes_close.clearTextures()
        else:
            print("Error : Argument of hide_eyes_open_close() has to be 'open' or 'close'.")
            sys.exit()
        self.win.flip()

    def show_gif(self, n_times=1, n_frames=77, sleep_time=0.08):
        for m in range(0, n_times):
            for file in range(0, n_frames):
                #print(os.path.join(PATH_TO_IMAGES, 'dancing_gif', str(file) + '.gif'))
                self.dancing_gif.setImage(os.path.join(PATH_TO_IMAGES, 'dancing_gif', str(file) + '.gif'))
                self.dancing_gif.draw()
                self.win.flip()
                core.wait(sleep_time)
        self.dancing_gif.clearTextures()

    def show_crosshair(self):
        self.cross_hair.show()

    def hide_crosshair(self):
        self.cross_hair.hide()

    def show_speakers(self):
        self.speakers.show()

    def highlight_speaker(self, speaker_number):
        self.speakers.highlight(speaker_number)

    def unhighlight_speaker(self):
        self.speakers.unhighlight()

    def hide_speaker(self):
        self.speakers.hide()


class CrossHair(object):
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


class Speakers(object):
    def __init__(self, win,  number_of_speakers=6, offset=None, radius_inner=0.1, radius_outer=0.4, line_width=3, edges=32):
        """
        discriptions of offset
        ...
        ...
        ...
        """
        self.win = win
        self.number_of_speakers = number_of_speakers
        self.offset = 180/number_of_speakers
        self.radius_inner = radius_inner
        self.radius_outer = radius_outer
        self.line_width = line_width
        self.edges = edges
        self.highlighted_speaker = None

        self.circle_objs = list()
        for m in range(0, self.number_of_speakers):
            degree = 360 / self.number_of_speakers * m + self.offset
            radian = numpy.radians(degree)
            pos = [radius_outer*numpy.sin(radian), radius_outer*numpy.cos(radian)]
            self.circle_objs.append(circle.Circle(win, radius=radius_inner, edges=edges, lineWidth=line_width, pos=pos))
        self.cross_hair = CrossHair(self.win)

    def highlight(self, speaker_number):
        self.highlighted_speaker = speaker_number
        self.circle_objs[speaker_number-1].color = HIGHLIGHT_COLOR
        for m in range(0, self.number_of_speakers):
            self.circle_objs[m].draw()
            self.cross_hair.draw()
        self.win.flip()

    def unhighlight(self):
        if self.highlighted_speaker is not None:
            self.circle_objs[self.highlighted_speaker-1].color = [1.0, 1.0, 1.0]
            for m in range(0, self.number_of_speakers):
                self.circle_objs[m].draw()
                self.cross_hair.draw()
            self.win.flip()

    def show(self):
        self.draw()
        self.win.flip()

    def hide(self):
        self.win.flip()

    def draw(self):
        for m in range(0, self.number_of_speakers):
            self.circle_objs[m].draw()
        self.cross_hair.draw()



