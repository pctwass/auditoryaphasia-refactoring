import json
import logging

import config.conf_system as conf_system
import src.process_management.intermodule_communication as intermodule_comm

from classifier import ClassifierFactory
from acquisition.AcquisitionSystemController import AcquisitionSystemController
from src.process_management.state_dictionaries import *

logger = logging.getLogger(__name__)


def interface(
    name:str, state_dict:dict[str,any], live_barplot_state_dict:dict[str,any], name_main_outlet:str='main'
):
    # ==============================================
    # This function is called from main module.
    # It opens LSL and communicate with main module.
    # ==============================================
    #
    # name : name of this module. main module will call this module with this name.
    #        This name will be given by main module.
    # name_main_outlet : name of main module's outlet. This module will find the main module with this name.
    #

    if state_dict == None:
        state_dict = init_acquisition_state_dict()

    # set_logger(file=log_file, stdout=log_stdout)
    params = dict()  # variable for receive parameters

    inlet = intermodule_comm.get_intermodule_communication_inlet(name_main_outlet)
    # print('LSL connected, Acquisition Controller Module')
    state_dict["LSL_inlet_connected"] = True

    asc = None

    while True:
        data, _ = inlet.pull_sample(timeout=0.01)
        if data is not None:
            if data[0].lower() == name:
                if data[1].lower() == "cmd":
                    logger.info(
                        "cmd '%s' was recieved with param : %s"
                        % (data[2], str(json.loads(data[3])))
                    )
                    # ------------------------------------
                    # command
                    if data[2].lower() == "start_recording":
                        f_dir = json.loads(data[3])
                        conf_system.start_recording(f_dir)
                    elif data[2].lower() == "init_recorder":
                        params["init_recorder"] = json.loads(data[3])
                        conf_system.initialize_recorder(
                            params["init_recorder"]
                        )
                    elif data[2].lower() == "stop_recording":
                        conf_system.stop_recording()
                    elif data[2].lower() == "start_calibration":
                        asc.calibration(params)
                        state_dict["trial_completed"] = True
                    elif data[2].lower() == "init":
                        asc = init_acquisition(state_dict, live_barplot_state_dict)
                    elif data[2].lower() == "start":
                        asc.main()
                    else:
                        raise ValueError("Unknown command was received.")
                    # modify here to add new commands
                    # ------------------------------------

                elif data[1].lower() == "params":
                    # ------------------------------------
                    # parameters
                    params[data[2]] = json.loads(data[3])
                    logger.info(
                        "Param Received : %s, %s"
                        % (str(data[2]), str(params[data[2]]))
                    )
                    # ------------------------------------
                else:
                    raise ValueError("Unknown LSL data type received.")
                

def init_acquisition(state_dict:dict[str,any], live_barplot_state_dict : dict[str,any]):
    classifier_factory = ClassifierFactory(n_channels=conf_system.n_ch)
    classifier = classifier_factory.getmodel()

    asc = AcquisitionSystemController(
        state_dict=state_dict,
        live_barplot_state_dict=live_barplot_state_dict,
        clf=classifier,
        markers=conf_system.markers,
        tmin=conf_system.tmin,
        tmax=conf_system.tmax,
        baseline=conf_system.baseline,
        filter_freq=conf_system.filter_freq,
        filter_order=conf_system.filter_order,
        ivals=conf_system.ivals,
        n_class=conf_system.n_class,
        adaptation=conf_system.adaptation,
        dynamic_stopping=conf_system.dynamic_stopping,
        dynamic_stopping_params=conf_system.dynamic_stopping_params,
        max_n_stims=conf_system.n_stimulus,
    )

    return asc