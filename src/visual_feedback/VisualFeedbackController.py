import os
import sys

import numpy as np

from psychopy import visual, core
from psychopy.visual import line, circle

import config.conf_selector
# exec("import %s as conf" % (conf_selector.conf_file_name))
# exec("import %s as conf_system" % (conf_selector.conf_system_file_name))
import config.conf as conf
import config.conf_system as conf_system

def show_pics_vert(win, img_1_dir, img_2_dir, img_1_vert_coff):
    """
    Parameters
    ----------
    win : instance of psychopy.visual.Window()
    img_1_dir : path-like
        image shown above
    img_2_dir : path-like
        image shown below
    img_1_vert_coff : float
        should be in range between 0 and 1
        It determines ratio between img_1 and img_2.
        if img_1_ver_coff = 0.2, img_1 will be filling 20% of vertical pixels on display, and img_2 will be 80%.
    """
    size_win = win.size

    img_1 = visual.ImageStim(win=win, image=img_1_dir, units='pix')
    img_2 = visual.ImageStim(win=win, image=img_2_dir, units='pix')
    
    size_img = img_1.size
    ratio_img_1 = size_img[0]/size_img[1]
    size_img = img_2.size 
    ratio_img_2 = size_img[0]/size_img[1]
    
    y_1 = size_win[1]*img_1_vert_coff
    x_1 = y_1*ratio_img_1
    
    y_2 = size_win[1]*(1-img_1_vert_coff)
    x_2 = y_2*ratio_img_2
    
    img_1.size = (x_1, y_1)
    img_2.size = (x_2, y_2)
    
    img_1.pos += (0, size_win[1]*(1-img_1_vert_coff)/2)
    img_2.pos += (0, -size_win[1]/2*img_1_vert_coff)
    
    img_1.draw()
    img_2.draw()
        
    return img_1, img_2

def show_pic_by_height(win, img_dir):
    """
    Parameters
    ----------
    win : instance of psychopy.visual.Window()
    img_dir : path-like
    """
    size_win = win.size

    img = visual.ImageStim(win=win, image=img_dir, units='pix')
    
    size_img = img.size
    ratio_img = size_img[0]/size_img[1]
    
    y = size_win[1]
    x = y*ratio_img
    
    img.size = (x, y)
    
    img.draw()
        
    return img

class VisualFeedbackController(object):

    def __init__(self, number_of_speakers=2, fullscreen_mode=False, display_size=[640, 480],
                 window_position=[100, 100], units='height', images_dir_base='', screen = 0):
        self.number_of_speakers = number_of_speakers
        self.fullscreen_mode = fullscreen_mode
        self.display_size = display_size
        self.window_position = window_position
        self.units = units
        self.images_dir_base = images_dir_base
        self.screen = screen

    def show_screen(self):
        self.win = visual.Window(self.display_size, color=conf_system.background_color, fullscr=self.fullscreen_mode,
                                 pos=self.window_position, units=self.units, screen=self.screen)
        self.smiley = visual.ImageStim(win=self.win, size=conf_system.size_smiley)
        self.barplot = visual.ImageStim(win=self.win)
        self.eyes_open = visual.ImageStim(win=self.win, image=os.path.join(self.images_dir_base, 'eyesOpen.jpg'),
                                          size=conf_system.size_eye_open_close)
        self.eyes_close = visual.ImageStim(win=self.win, image=os.path.join(self.images_dir_base, 'eyesClosed.jpg'),
                                           size=conf_system.size_eye_open_close)
        self.dancing_gif = visual.ImageStim(win=self.win, size=conf_system.size_dancing_gif)
        self.cross_hair = CrossHair(self.win)
        self.speakers = Speakers(self.win)


    def hide_screen(self):
        self.win.close()

    def show_barplot_with_smiley(self):
        self.fb_smiley, self.fb_bar = show_pics_vert(win=self.win,
                                            img_1_dir=os.path.join(self.images_dir_base, 'smiley_transparent.png'),
                                            img_2_dir=os.path.join(conf_system.repository_dir_base, 'media', 'tmp', 'fb_barplot.png'),
                                            img_1_vert_coff=0.15)
        self.win.flip()
    
    def hide_barplot_with_smiley(self):
        self.fb_smiley.clearTextures()
        self.fb_bar.clearTextures()
        self.win.flip()

    def show_barplot(self):
        self.barplot = show_pic_by_height(self.win, os.path.join(conf_system.repository_dir_base, 'media', 'tmp', 'fb_barplot.png'))
        self.win.flip()

    def hide_barplot(self):
        self.barplot.clearTextures()
        self.win.flip()

    def show_smiley(self):
        self.smiley.setImage(os.path.join(self.images_dir_base, 'smiley_transparent.png'))
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

    def show_gif(self, n_times=1, n_frames=77, sleep_time=0.1):
        for m in range(0, n_times):
            for file in range(0, n_frames):
                #print(os.path.join(self.images_dir_base, 'dancing_gif', str(file) + '.gif'))
                self.dancing_gif.setImage(os.path.join(self.images_dir_base, 'dancing_gif', str(file) + '.gif'))
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
            radian = np.radians(degree)
            pos = [radius_outer*np.sin(radian), radius_outer*np.cos(radian)]
            self.circle_objs.append(circle.Circle(win, radius=radius_inner, edges=edges, lineWidth=line_width, pos=pos))
        self.cross_hair = CrossHair(self.win)

    def highlight(self, speaker_number):
        self.highlighted_speaker = speaker_number
        self.circle_objs[speaker_number-1].color = conf_system.highlight_color
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
