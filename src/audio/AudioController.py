from socket import timeout
import sys
import os
import time
import datetime
import logging
import json

from multiprocessing import Process, Array

import conf_selector
exec('import %s as conf' %(conf_selector.conf_file_name))
exec('import %s as conf_system' %(conf_selector.conf_system_file_name))

import pyscab
import utils

logger = logging.getLogger(__name__)

def marker_none(val):
    pass

class StimulationController(object):

    def __init__(self, share):
        self.share = share
        self.mrk = None
        self.ahc = None
        self.stc = None

    def open(self):
        self.ahc = pyscab.AudioInterface(device_name = conf_system.device_name,
                                        n_ch = conf_system.n_ch,
                                        format=conf_system.format,
                                        frames_per_buffer = conf_system.frames_per_buffer)
                            
        self.mrk = conf_system.Marker()
        self.mrk.open()     
        self.stc = pyscab.StimulationController(self.ahc, 
                                                marker_send=self.mrk.sendMarker,
                                                correct_latency = conf_system.correct_sw_latency,
                                                correct_hardware_buffer = conf_system.correct_hw_latency,
                                                share=self.share)
        self.stc.open()
        logger.info("Audio Device was opened")

    def close(self):
        self.stc.close()
        self.ahc.terminate()
        #logger.info("Audio Hardware Controller terminated.")
        #if params['marker']:
        self.mrk.close() # close marker device

    def play(self, params):
        #self.p = Process(target=self.play_parallel, args=(params,self.share, log_file, log_stdout))
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
        self.share[0] = 99

    #def stop(self, pause=1):
    #    self.share[0] = 99
    #    time.sleep(pause)
    #    #self.p.terminate()

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
    # share : value which is shared with main module.
    #          0 : initial
    #          1 : start playing
    #         99 : end

    sys.path.append(conf_system.repository_dir_base)

    for m in range(5): # set value of used 3 digits to zero.
        share[m] = 0
    params = dict() # variable for receive parameters
    

    stim_controller = StimulationController(share)

    inlet = utils.getIntermoduleCommunicationInlet(name_main_outlet)
    share[2] = 1 # LSL connected
    logger.info("Audio Controller was connected via LSL.")

    while True:
        #print("pyscab : %.2f" %(share_pyscab[0]))

        #share[1] = share_pyscab[1] # share marker from pyscab
        #share_pyscab[0] = share[3]

        data, _ = inlet.pull_sample(timeout=0.01)
        if data is not None:
            if data[0].lower() == name:
                if data[1].lower() == 'cmd':
                    logger.info("cmd '%s' was recieved with param : %s" %(data[2], str(json.loads(data[3]))))
                    # ------------------------------------
                    # command
                    if data[2].lower() == 'play':
                        share[0] = 0
                        #share_pyscab[0] = 0
                        params['play_plan'] = json.loads(data[3])
                        if params['play_plan'] is None:
                            raise ValueError("command 'play' requires play plan.")
                        share[0] = 1
                        stim_controller.play(params)
                    elif data[2].lower() == 'open':
                        stim_controller.open()
                        share[2] = 1
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
        #if share[0] != 99 and share[0] != 0 and share_pyscab[0] == 0:
        #if int(share[0]) == 1 and int(share_pyscab[0]) == 99:
            # pass
            # share[0] != 99 -> is not already ended
            # share[0] != 0  -> is not initial state
            # share_pyscab[0] == 0 -> pyscab is already terminated.

            #share[0] = 99