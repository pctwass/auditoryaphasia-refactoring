import numpy as np

from psychopy import visual
from psychopy.visual import circle
from auditory_aphasia.visual_feedback.visual_objects.crosshair import Crosshair


class Speakers(object):
    def __init__(self, window:visual.Window, number_of_speakers:int=6, offset:float=None, radius_inner:float=0.1, 
                 radius_outer:float=0.4, line_width:float=3, edges:int|str=32, highlight_color:str=None):
        self.window = window
        self.number_of_speakers = number_of_speakers
        self.offset = 180/number_of_speakers
        self.radius_inner = radius_inner
        self.radius_outer = radius_outer
        self.line_width = line_width
        self.edges = edges
        self.highlighted_speaker = None
        self.highlight_color = highlight_color

        self.circle_objs = list()
        for m in range(0, self.number_of_speakers):
            degree = 360 / self.number_of_speakers * m + self.offset
            radian = np.radians(degree)
            pos = [radius_outer*np.sin(radian), radius_outer*np.cos(radian)]
            self.circle_objs.append(circle.Circle(window, radius=radius_inner, edges=edges, lineWidth=line_width, pos=pos))
        self.cross_hair = Crosshair(self.window)


    def highlight(self, speaker_number:int):
        self.highlighted_speaker = speaker_number
        self.circle_objs[speaker_number-1].color = self.highlight_color
        for m in range(0, self.number_of_speakers):
            self.circle_objs[m].draw()
            self.cross_hair.draw()
        self.window.flip()

    def unhighlight(self):
        if self.highlighted_speaker is not None:
            self.circle_objs[self.highlighted_speaker-1].color = [1.0, 1.0, 1.0]
            for m in range(0, self.number_of_speakers):
                self.circle_objs[m].draw()
                self.cross_hair.draw()
            self.window.flip()

    def show(self):
        self.draw()
        self.window.flip()

    def hide(self):
        self.window.flip()

    def draw(self):
        for m in range(0, self.number_of_speakers):
            self.circle_objs[m].draw()
        self.cross_hair.draw()