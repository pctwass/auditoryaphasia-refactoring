import logging
logger = logging.getLogger(__name__)

import config.conf_system as conf_system
import pyscab

from process_management.process_communication_enums import AudioStatus


class AudioStimulationController(object):

    def __init__(self, state_dict):
        self.state_dict = state_dict
        self.marker = None
        self.audio_device_interface = None
        self.psycab_stim_controller = None


    def open(self):
        self.audio_device_interface = pyscab.AudioInterface(device_name = conf_system.device_name,
                                        n_ch = conf_system.n_ch,
                                        format=conf_system.format,
                                        frames_per_buffer = conf_system.frames_per_buffer)
                            
        self.marker = conf_system.Marker()
        self.marker.open()
             
        self.psycab_stim_controller = pyscab.StimulationController(self.audio_device_interface, 
                                                marker_send=self.marker.sendMarker,
                                                correct_latency = conf_system.correct_sw_latency,
                                                correct_hardware_buffer = conf_system.correct_hw_latency,
                                                state_dict=self.state_dict)
        self.psycab_stim_controller.open()

        logger.info("Audio Device was opened")


    def close(self):
        self.psycab_stim_controller.close()
        self.audio_device_interface.terminate()

        logger.info("Audio Hardware Controller terminated.")
        
        if self.marker is not None:
            self.marker.close() # close marker device


    def play(self, params:dict[str,any]):
        #self.p = Process(target=self.play_parallel, args=(params,self.state_dict, log_file, log_stdout))
        #self.p.start()

        #conf.set_logger(file=log_file, stdout=log_stdout)

        audio_infos = params['audio_info']
        play_plan = params['play_plan']

        audio_files = pyscab.DataHandler()
        for audio_info in audio_infos:
            audio_files.load(audio_info[0], audio_info[1], volume=audio_info[2])

        logger.debug("Stimulation Controller Opened and Start playing.")
        self.psycab_stim_controller.play(play_plan, audio_files, time_termination = 'auto', pause=0)

        #time.sleep(1) # for closing marker device properly, just in case.
        #logger.info("Marker Device closed") 
        #logger.info("------------------------ Run ended ------------------------")
        self.state_dict["audio_status"] = AudioStatus.TERMINATED