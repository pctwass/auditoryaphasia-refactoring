from socket import timeout
import sys
import os
import time
import datetime
import logging
import json

from multiprocessing import Process, Array

import config.conf_selector
# exec('import %s as conf' %(conf_selector.conf_file_name))
# exec('import %s as conf_system' %(conf_selector.conf_system_file_name))

import config.conf_system as conf_system

import pyscab
import src.utils as utils

logger = logging.getLogger(__name__)

from src.process_management.state_dictionaries import *
from src.process_management.process_communication_enums import *

def marker_none(val):
    pass

class StimulationController(object):

    def __init__(self, state_dict):
        self.state_dict = state_dict
        self.mrk = None
        self.ahc = None
        self.stc = None

    def open(self):
        self.ahc = pyscab.AudioInterface(device_name = conf_system.device_name,
                                        n_ch = conf_system.n_ch,
                                        format=conf_system.format,
                                        frames_per_buffer = conf_system.frames_per_buffer)
                            
        self.mrk = conf_system.Marker()
        #self.mrk.open()     
        self.stc = pyscab.StimulationController(self.ahc, 
                                                marker_send=self.mrk.sendMarker,
                                                correct_latency = conf_system.correct_sw_latency,
                                                correct_hardware_buffer = conf_system.correct_hw_latency,
                                                state_dict=self.state_dict)
        self.stc.open()
        logger.info("Audio Device was opened")

    def close(self):
        self.stc.close()
        self.ahc.terminate()
        #logger.info("Audio Hardware Controller terminated.")
        #if params['marker']:
        self.mrk.close() # close marker device

    def play(self, params):
        #self.p = Process(target=self.play_parallel, args=(params,self.state_dict, log_file, log_stdout))
        #self.p.start()

        #conf.set_logger(file=log_file, stdout=log_stdout)

        audio_infos = params['audio_info']
        play_plan = params['play_plan']

        audio_files = pyscab.DataHandler()
        for audio_info in audio_infos:
            audio_files.load(audio_info[0], audio_info[1], volume=audio_info[2])

        #logger.info("Stimulation Controller Opened and Start playing.")
        self.stc.play(play_plan, audio_files, time_termination = 'auto', pause=0)
        #play(self, plans, data, time_termination = 'auto', pause=0.5):

        #time.sleep(1) # for closing marker device properly, just in case.
        #logger.info("Marker Device closed") 
        #logger.info("------------------------ Run ended ------------------------")
        self.state_dict["audio_status"] = AudioStatus.TERMINATED

    #def stop(self, pause=1):
    #    self.state_dict["audio_status"] = AudioStatus.TERMINATED
    #    time.sleep(pause)
    #    #self.p.terminate()

def interface(name, name_main_outlet='main', log_file=True, log_stdout=True, state_dict=None):
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
    #          0 : initial
    #          1 : start playing
    #         99 : end

    sys.path.append(conf_system.repository_dir_base)

    if state_dict == None:
        state_dict = init_audio_state_dict()
    params = dict() # variable for receive parameters
    

    stim_controller = StimulationController(state_dict)

    inlet = utils.getIntermoduleCommunicationInlet(name_main_outlet)
    state_dict["LSL_inlet_connected"] = True # LSL connected
    logger.info(f"Audio Controller was connected via LSL. (state dict value: {state_dict['LSL_inlet_connected']})")

    while True:
        #print("pyscab : %.2f" %(share_pyscab[0]))

        #state_dict["trial_marker"] = share_pyscab[1] # share marker from pyscab
        #share_pyscab[0] = state_dict[3] 

        data, _ = inlet.pull_sample(timeout=0.01)
        if data is not None:
            if data[0].lower() == name:
                if data[1].lower() == 'cmd':
                    logger.info("cmd '%s' was recieved with param : %s" %(data[2], str(json.loads(data[3]))))
                    # ------------------------------------
                    # command
                    if data[2].lower() == 'play':
                        state_dict["audio_status"] = AudioStatus.INITIAL
                        #share_pyscab[0] = 0
                        params['play_plan'] = json.loads(data[3])
                        if params['play_plan'] is None:
                            raise ValueError("command 'play' requires play plan.")
                        state_dict["audio_status"] = AudioStatus.PLAYING
                        stim_controller.play(params)
                    elif data[2].lower() == 'open':
                        stim_controller.open()
                        state_dict["LSL_inlet_connected"] = True
                    elif data[2].lower() == 'close':
                        stim_controller.close()
                    #elif data[2].lower() == 'stop':
                    #    stim_controller.stop(0.1)
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
        #if int(state_dict["audio_status"]) == AudioStatus.PLAYING and int(share_pyscab[0]) == 99:
            # pass
            # state_dict["audio_status"] != AudioStatus.TERMINATED -> is not already ended
            # state_dict["audio_status"] != AudioStatus.INITIAL  -> is not initial state
            # share_pyscab[0] == 0 -> pyscab is already terminated.

            #state_dict["audio_status"] = AudioStatus.TERMINATED