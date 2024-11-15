import sys
from auditory_aphasia.logging.logger import get_logger
import json

import auditory_aphasia.config.system_config as system_config
import auditory_aphasia.process_management.intermodule_communication as intermodule_comm

from auditory_aphasia.config.config_builder import build_configs
from audio_stimulation.audio_stimulation_controller import AudioStimulationController
from auditory_aphasia.process_management.state_dictionaries import *
from auditory_aphasia.process_management.process_communication_enums import *

logger = get_logger()


def interface(name:str, name_main_outlet:str='main', state_dict:dict[str,any]=None):
    # ==============================================
    # This function is called from main module.
    # It opens LSL and communicate with main module.
    # ==============================================
    #
    # name : name of this module. main module will call this module with this name.
    #        This name will be given by main module.
    # name_main_outlet : name of main module's outlet. This module will find the main module with this name.
    #
    # state_dict : value which is state_dictd with main module.

    # Because the interface is spawned as the target of a new process, we need to load the config into memory again
    build_configs()
    sys.path.append(system_config.repository_dir_base)

    if state_dict == None:
        state_dict = init_audio_state_dict()
    params = dict() # variable for receive parameters

    audio_stim_controller = AudioStimulationController(state_dict)

    inlet = intermodule_comm.get_intermodule_communication_inlet(name_main_outlet)
    state_dict["LSL_inlet_connected"] = True # LSL connected
    logger.info(f"Audio Controller was connected via LSL.")

    while True:
        #print("pyscab : %.2f" %(share_pyscab[0]))

        #state_dict["trial_marker"] = share_pyscab[1] # share marker from pyscab
        #share_pyscab[0] = state_dict[3] 

        data, _ = inlet.pull_sample(timeout=0.01)
        if data is not None:
            if data[0].lower() == name:
                if data[1].lower() == 'cmd':
                    logger.info(f"cmd {data[2]} was recieved with param : {str(json.loads(data[3]))}")
                    # ------------------------------------
                    # command
                    if data[2].lower() == 'play':
                        state_dict["audio_status"] = AudioStatus.INITIAL
                        #share_pyscab[0] = 0
                        params['play_plan'] = json.loads(data[3])

                        if params['play_plan'] is None:
                            raise ValueError("command 'play' requires play plan.")
                        
                        state_dict["audio_status"] = AudioStatus.PLAYING
                        logger.debug(f"changed audio status to PLAYING")
                        audio_stim_controller.play(params)

                    elif data[2].lower() == 'open':
                        audio_stim_controller.open()
                        state_dict["LSL_inlet_connected"] = True

                    elif data[2].lower() == 'close':
                        audio_stim_controller.close()

                    #elif data[2].lower() == 'stop':
                    #    audio_stim_controller.stop(0.1)
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
                    
        #if state_dict["audio_status"] != AudioStatus.TERMINATED and state_dict["audio_status"] != AudioStatus.INITIAL and share_pyscab[0] == 0:
        #if state_dict["audio_status"].value == AudioStatus.PLAYING.value and int(share_pyscab[0]) == 99:
            # pass
            # state_dict["audio_status"] != AudioStatus.TERMINATED -> is not already ended
            # state_dict["audio_status"] != AudioStatus.INITIAL  -> is not initial state
            # share_pyscab[0] == 0 -> pyscab is already terminated.

            #state_dict["audio_status"] = AudioStatus.TERMINATED