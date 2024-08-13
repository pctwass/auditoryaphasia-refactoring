import os
import sys
import utils
import datetime
import json
import time

import conf_selector
# exec("import %s as conf" % (conf_selector.conf_file_name))
# exec("import %s as conf_system" % (conf_selector.conf_system_file_name))
import conf as conf
import conf_system as conf_system

import logging
logger = logging.getLogger(__name__)

def interface(name, name_main_outlet='main', log_file=True, log_stdout=True, share=None):
    # ==============================================
    # This function is called from main module.
    # It opens LSL and communicate with main module.
    # ==============================================
    #
    # name : name of this module. main module will call this module with this name.
    #        This name will be given by main module.
    # name_main_outlet : name of main module's outlet. This module will find the main module with this name.
    #

    for m in range(1):
        share[0] = 0

    #status.value = 0
    #set_logger(file=log_file, stdout=log_stdout)
    params = dict() # variable for receive parameters

    import VisualFeedbackController
    vfc = VisualFeedbackController.VisualFeedbackController(images_dir_base=conf_system.visual_images_dir_base, fullscreen_mode = conf_system.enable_fullscreen, screen=conf.screen_number)
    vfc.show_screen()
    vfc.show_crosshair()
    #vfc.show_speakers()

    inlet = utils.getIntermoduleCommunicationInlet(name_main_outlet)
    share[0] = 1
    #print('LSL connected, %s' %name)

    while True:
        data, _ = inlet.pull_sample(timeout=0.01)
        if data is not None:
            if data[0].lower() == name:
                if data[1].lower() == 'cmd':
                    logger.info("cmd '%s' was recieved with param : %s" %(data[2], str(json.loads(data[3]))))
                    # ------------------------------------
                    # command
                    if data[2].lower() == 'show_speaker':
                        vfc.show_speakers()
                    elif data[2].lower() == 'highlight_speaker':
                        param = json.loads(data[3])
                        #print()
                        vfc.highlight_speaker(int(param['spk_num']))
                        time.sleep(param['duration'])
                        vfc.unhighlight_speaker()
                        vfc.hide_speaker()
                        vfc.show_crosshair()
                    elif data[2].lower() == 'show_crosshair':
                        vfc.unhighlight_speaker()
                        vfc.hide_speaker()
                        vfc.show_crosshair()

                    elif data[2].lower() == 'show_smiley':
                        vfc.hide_crosshair()
                        vfc.show_smiley()
                    elif data[2].lower() == 'hide_smiley':
                        vfc.hide_smiley()
                        vfc.show_crosshair()

                    elif data[2].lower() == 'show_neutral':
                        vfc.hide_crosshair()
                        vfc.show_barplot()
                    elif data[2].lower() == 'hide_neutral':
                        vfc.hide_barplot()
                        vfc.show_crosshair()

                    elif data[2].lower() == 'show_positive':
                        vfc.hide_crosshair()
                        vfc.show_barplot_with_smiley()
                    elif data[2].lower() == 'hide_positive':
                        vfc.hide_barplot_with_smiley()
                        vfc.show_crosshair()

                    elif data[2].lower() == 'show_gif':
                        vfc.hide_crosshair
                        vfc.show_gif()
                        vfc.show_crosshair()
                    # modify here to add new commands
                    # ------------------------------------                        

                elif data[1].lower() == 'params':
                    # ------------------------------------
                    # parameters
                    params[data[2]] = json.loads(data[3])
                    logger.info('Param Received : %s, %s' %(str(data[2]), str(params[data[2]])))
                    # ------------------------------------
                else:
                    raise ValueError("Unknown LSL data type received.")