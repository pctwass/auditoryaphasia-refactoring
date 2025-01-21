# NOTE: this stuff should run with the general paradigm flow, not was a separate subprocess IMO
import json
import time

import auditory_aphasia.process_management.intermodule_communication as intermodule_comm
from auditory_aphasia.config_builder import (build_general_config,
                                             build_system_config)
from auditory_aphasia.logging.logger import get_logger
from auditory_aphasia.visual_feedback.visual_feedback_controller import \
    VisualFeedbackController

logger = get_logger()


def run_visual_interface(name: str='', name_main_outlet: str = "main", state_dict: dict = None):
    # ==============================================
    # This function is called from main module.
    # It opens LSL and communicate with main module.
    # ==============================================
    #
    # name : name of this module. main module will call this module with this name.
    #        This name will be given by main module.
    # name_main_outlet : name of main module's outlet. This module will find the main module with this name.
    #

    config = build_general_config()
    system_config = build_system_config()

    state_dict = state_dict or dict()
    state_dict["LSL_inlet_connected"] = False

    # status.value = 0
    params = dict()  # variable for receive parameters

    vfc = VisualFeedbackController(
        images_dir_base=system_config.visual_images_dir_base,
        fullscreen_mode=system_config.enable_fullscreen,
        screen=config.screen_number,
    )
    vfc.show_screen()
    vfc.show_crosshair()
    # vfc.show_speakers()

    inlet = intermodule_comm.get_intermodule_communication_inlet(name_main_outlet)
    state_dict["LSL_inlet_connected"] = True
    # print('LSL connected, %s' %name)

    while True:
        # TODO: very nested programme flow -> refactor
        data, _ = inlet.pull_sample(timeout=0.01)
        if data is not None:
            if data[0].lower() == name:
                if data[1].lower() == "cmd":
                    logger.info(
                        f"cmd {data[2]} was recieved with param : {str(json.loads(data[3]))}"
                    )
                    # ------------------------------------
                    # command
                    if data[2].lower() == "show_speaker":
                        vfc.show_speakers()
                    elif data[2].lower() == "highlight_speaker":
                        param = json.loads(data[3])
                        # print()
                        vfc.highlight_speaker(int(param["spk_num"]))
                        time.sleep(param["duration"])
                        vfc.unhighlight_speaker()
                        vfc.hide_speaker()
                        vfc.show_crosshair()

                    elif data[2].lower() == "show_crosshair":
                        vfc.unhighlight_speaker()
                        vfc.hide_speaker()
                        vfc.show_crosshair()

                    elif data[2].lower() == "show_smiley":
                        vfc.hide_crosshair()
                        vfc.show_smiley()
                    elif data[2].lower() == "hide_smiley":
                        vfc.hide_smiley()
                        vfc.show_crosshair()

                    elif data[2].lower() == "show_neutral":
                        vfc.hide_crosshair()
                        vfc.show_barplot()
                    elif data[2].lower() == "hide_neutral":
                        vfc.hide_barplot()
                        vfc.show_crosshair()

                    elif data[2].lower() == "show_positive":
                        vfc.hide_crosshair()
                        vfc.show_barplot_with_smiley()
                    elif data[2].lower() == "hide_positive":
                        vfc.hide_barplot_with_smiley()
                        vfc.show_crosshair()

                    elif data[2].lower() == "show_gif":
                        vfc.hide_crosshair
                        vfc.show_gif()
                        vfc.show_crosshair()

                    # modify here to add new commands
                    # ------------------------------------

                elif data[1].lower() == "params":
                    # ------------------------------------
                    # parameters
                    params[data[2]] = json.loads(data[3])
                    logger.info(
                        f"Param Received : {str(data[2])}, {str(params[data[2]])}"
                    )
                    # ------------------------------------

                else:
                    raise ValueError("Unknown LSL data type received.")
