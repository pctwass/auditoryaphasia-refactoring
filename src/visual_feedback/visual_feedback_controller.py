import os
import sys
import numpy as np

from psychopy import visual, core

import src.config.system_config as system_config
from src.visual_feedback.visual_objects.crosshair import Crosshair
from src.visual_feedback.visual_objects.speaker import Speakers


class VisualFeedbackController(object):

    def __init__(self, number_of_speakers:int=2, fullscreen_mode:bool=False, display_size:tuple[int,int]=[640, 480],
                 window_position:tuple[int,int]=[100, 100], window_units:str='height', images_dir_base:str='', screen:int=0):
        self.number_of_speakers = number_of_speakers
        self.fullscreen_mode = fullscreen_mode
        self.display_size = display_size
        self.window_position = window_position
        self.window_units = window_units
        self.images_dir_base = images_dir_base
        self.screen = screen


    def show_screen(self):
        self.window = visual.Window(self.display_size, color=system_config.background_color, fullscr=self.fullscreen_mode,
                                 pos=self.window_position, units=self.window_units, screen=self.screen)
        self.smiley = visual.ImageStim(win=self.window, size=system_config.size_smiley)
        self.barplot = visual.ImageStim(win=self.window)
        self.eyes_open = visual.ImageStim(win=self.window, image=os.path.join(self.images_dir_base, 'eyesOpen.jpg'),
                                          size=system_config.size_eye_open_close)
        self.eyes_close = visual.ImageStim(win=self.window, image=os.path.join(self.images_dir_base, 'eyesClosed.jpg'),
                                           size=system_config.size_eye_open_close)
        self.dancing_gif = visual.ImageStim(win=self.window, size=system_config.size_dancing_gif)
        self.crosshair = Crosshair(self.window)
        self.speakers = Speakers(self.window, highlight_color=system_config.highlight_color)

    def hide_screen(self):
        self.window.close()

    def show_barplot_with_smiley(self):
        self.fb_smiley, self.fb_bar = self._show_pics_vert(win=self.window,
                                            img_1_dir=os.path.join(self.images_dir_base, 'smiley_transparent.png'),
                                            img_2_dir=os.path.join(system_config.repository_dir_base, 'media', 'tmp', 'fb_barplot.png'),
                                            img_1_vert_coff=0.15)
        self.window.flip()
    
    def hide_barplot_with_smiley(self):
        self.fb_smiley.clearTextures()
        self.fb_bar.clearTextures()
        self.window.flip()

    def show_barplot(self):
        self.barplot = self._show_pic_by_height(self.window, os.path.join(system_config.repository_dir_base, 'media', 'tmp', 'fb_barplot.png'))
        self.window.flip()

    def hide_barplot(self):
        self.barplot.clearTextures()
        self.window.flip()

    def show_smiley(self):
        self.smiley.setImage(os.path.join(self.images_dir_base, 'smiley_transparent.png'))
        self.smiley.draw()
        self.window.flip()

    def hide_smiley(self):
        self.smiley.clearTextures()
        self.window.flip()

    def show_eyes_open_close(self, show_eyes:str):
        if show_eyes.lower() == "open":
            self.eyes_open.draw()
        elif show_eyes.lower() == "close":
            self.eyes_close.draw()
        else:
            print("Error : Argument of show_eyes_open_close() has to be 'open' or 'close'.")
            sys.exit()
        self.window.flip()

    def hide_eyes_open_close(self, show_eyes:str):
        if show_eyes.lower() == "open":
            self.eyes_open.clearTextures()
        elif show_eyes.lower() == "close":
            self.eyes_close.clearTextures()
        else:
            print("Error : Argument of hide_eyes_open_close() has to be 'open' or 'close'.")
            sys.exit()
        self.window.flip()

    def show_gif(self, n_times:int=1, n_frames:int=77, sleep_time:float=0.1):
        for i in range(0, n_times):
            for file in range(0, n_frames):
                #print(os.path.join(self.images_dir_base, 'dancing_gif', str(file) + '.gif'))
                self.dancing_gif.setImage(os.path.join(self.images_dir_base, 'dancing_gif', str(file) + '.gif'))
                self.dancing_gif.draw()
                self.window.flip()
                core.wait(sleep_time)
        self.dancing_gif.clearTextures()

    def show_crosshair(self):
        self.crosshair.show()

    def hide_crosshair(self):
        self.crosshair.hide()

    def show_speakers(self):
        self.speakers.show()

    def highlight_speaker(self, speaker_number):
        self.speakers.highlight(speaker_number)

    def unhighlight_speaker(self):
        self.speakers.unhighlight()

    def hide_speaker(self):
        self.speakers.hide()


    def _show_pics_vert(window:visual.Window, img_1_dir:str, img_2_dir:str, vertical_ratio_images:float) -> tuple[visual.ImageStim, visual.ImageStim]:
        """
        Parameters
        ----------
        window : instance of psychopy.visual.Window()
        img_1_dir : path-like
            image shown above
        img_2_dir : path-like
            image shown below
        vertical_ratio_images : float
            should be in range between 0 and 1
            It determines ratio between img_1 and img_2.
            if img_1_ver_coff = 0.2, img_1 will be filling 20% of vertical pixels on display, and img_2 will be 80%.
        """
        size_window = window.size

        img_1 = visual.ImageStim(win=window, image=img_1_dir, units='pix')
        img_2 = visual.ImageStim(win=window, image=img_2_dir, units='pix')
        
        size_img = img_1.size
        ratio_img_1 = size_img[0]/size_img[1]
        size_img = img_2.size 
        ratio_img_2 = size_img[0]/size_img[1]
        
        y_1 = size_window[1]*vertical_ratio_images
        x_1 = y_1*ratio_img_1
        
        y_2 = size_window[1]*(1-vertical_ratio_images)
        x_2 = y_2*ratio_img_2
        
        img_1.size = (x_1, y_1)
        img_2.size = (x_2, y_2)
        
        img_1.pos += (0, size_window[1]*(1-vertical_ratio_images)/2)
        img_2.pos += (0, -size_window[1]/2*vertical_ratio_images)
        
        img_1.draw()
        img_2.draw()
            
        return img_1, img_2

    def _show_pic_by_height(window:visual.Window, img_dir:str) -> visual.ImageStim:
        """
        Parameters
        ----------
        window : instance of psychopy.visual.Window()
        img_dir : path-like
        """
        size_window = window.size

        img = visual.ImageStim(win=window, image=img_dir, units='pix')
        
        size_img = img.size
        ratio_img = size_img[0]/size_img[1]
        
        y = size_window[1]
        x = y*ratio_img
        
        img.size = (x, y)
        
        img.draw()
            
        return img
