import json
import time

# Because the interface is spawned as the target of a new process, we need to load the config into memory again
from src.config.config_builder import build_configs
build_configs()

import src.config.config as config
import src.config.system_config as system_config
import src.process_management.intermodule_communication as intermodule_comm

import logging
logger = logging.getLogger(__name__)

from src.visual_feedback.VisualFeedbackController import VisualFeedbackController


def interface(name:str, name_main_outlet:str='main', state_dict:str=None):
    # ==============================================
    # This function is called from main module.
    # It opens LSL and communicate with main module.
    # ==============================================
    #
    # name : name of this module. main module will call this module with this name.
    #        This name will be given by main module.
    # name_main_outlet : name of main module's outlet. This module will find the main module with this name.
    #

    state_dict["LSL_inlet_connected"] = False

    #status.value = 0
    params = dict() # variable for receive parameters

    vfc = VisualFeedbackController(images_dir_base=system_config.visual_images_dir_base, fullscreen_mode = system_config.enable_fullscreen, screen=config.screen_number)
    vfc.show_screen()
    vfc.show_crosshair()
    #vfc.show_speakers()

    inlet = intermodule_comm.get_intermodule_communication_inlet(name_main_outlet)
    state_dict["LSL_inlet_connected"] = True
    #print('LSL connected, %s' %name)

    while True:
        data, _ = inlet.pull_sample(timeout=0.01)
        if data is not None:
            if data[0].lower() == name:
                if data[1].lower() == 'cmd':
                    logger.info(f"cmd {data[2]} was recieved with param : {str(json.loads(data[3]))}")
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
                    logger.info(f"Param Received : {str(data[2])}, {str(params[data[2]])}")
                    # ------------------------------------

                else:
                    raise ValueError("Unknown LSL data type received.")
