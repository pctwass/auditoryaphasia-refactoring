import json

import auditory_aphasia.process_management.intermodule_communication as intermodule_comm
from auditory_aphasia.acquisition.acquisition_system_controller import \
    AcquisitionSystemController
from auditory_aphasia.clients.recorder.brain_vision_recorder_client import \
    BrainVisionRecorderClient as RecorderClient
from auditory_aphasia.config_builder import (GeneralConfig, SystemConfig,
                                             build_classifier_config,
                                             build_general_config,
                                             build_system_config)
from auditory_aphasia.factories import classification_pipeline_factory
from auditory_aphasia.logging.logger import get_logger
from auditory_aphasia.process_management.state_dictionaries import \
    init_acquisition_state_dict

logger = get_logger()


def interface(
    name: str,
    state_dict: dict[str, any],
    live_barplot_state_dict: dict[str, any],
    name_main_outlet: str = "main",
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

    # Because the interface is spawned as the target of a new process, we need to load the config into memory again
    system_config = build_system_config()
    general_config = build_general_config()

    if state_dict is None:
        state_dict = init_acquisition_state_dict()

    # set_logger(file=log_file, stdout=log_stdout)
    params = dict()  # variable for receive parameters

    inlet = intermodule_comm.get_intermodule_communication_inlet(name_main_outlet)
    # print('LSL connected, Acquisition Controller Module')
    state_dict["LSL_inlet_connected"] = True

    acquisition_local_client = None
    acquisition_sys_controller = None

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
                    if data[2].lower() == "init_recorder":
                        params["init_recorder"] = json.loads(data[3])
                        acquisition_local_client = RecorderClient(
                            logger=logger,
                            params=params["init_recorder"],
                            system_config=system_config,
                            general_config=general_config,
                        )

                    elif data[2].lower() == "start_recording":
                        f_dir = json.loads(data[3])
                        acquisition_local_client.start_recording(f_dir)

                    elif data[2].lower() == "stop_recording":
                        acquisition_local_client.stop_recording()

                    elif data[2].lower() == "init":
                        acquisition_sys_controller = init_acquisition(
                            state_dict,
                            live_barplot_state_dict,
                            system_config=system_config,
                            general_config=general_config,
                        )

                    elif data[2].lower() == "start_calibration":
                        acquisition_sys_controller.calibration(params)
                        state_dict["trial_completed"] = True

                    elif data[2].lower() == "start":
                        acquisition_sys_controller.main()

                    else:
                        raise ValueError("Unknown command was received.")
                    # modify here to add new commands
                    # ------------------------------------

                elif data[1].lower() == "params":
                    # ------------------------------------
                    # parameters
                    params[data[2]] = json.loads(data[3])
                    logger.info(
                        "Param Received : %s, %s" % (str(data[2]), str(params[data[2]]))
                    )
                    # ------------------------------------
                else:
                    raise ValueError("Unknown LSL data type received.")


def init_acquisition(
    state_dict: dict[str, any],
    live_barplot_state_dict: dict[str, any],
    system_config: SystemConfig,
    general_config: GeneralConfig,
):

    classifier_config = build_classifier_config()

    classifier = classification_pipeline_factory(
        classifier_config.classification_pipeline_name
    )

    acquisition_sys_controller = AcquisitionSystemController(
        state_dict=state_dict,
        live_barplot_state_dict=live_barplot_state_dict,
        clf=classifier,
        markers=system_config.markers,
        tmin=classifier_config.tmin,
        tmax=classifier_config.tmax,
        baseline=classifier_config.baseline,
        filter_freq=classifier_config.filter_freq,
        filter_order=classifier_config.filter_order,
        ivals=classifier_config.ivals,
        n_class=classifier_config.n_class,
        adaptation=classifier_config.adaptation,
        dynamic_stopping=classifier_config.dynamic_stopping,
        dynamic_stopping_params=classifier_config.dynamic_stopping_params,
        max_n_stims=classifier_config.n_stimulus,
    )

    return acquisition_sys_controller
