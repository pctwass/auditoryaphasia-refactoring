"""
This class has been adopted from the pyscab package to work with auditory aphasia dataset.
Pyscab origional author: Simon Kojima
See the pyscab package for more detail at: https://pypi.org/project/pyscab/
"""

import time
import threading

from auditory_aphasia.process_management.state_dictionaries import init_audio_state_dict
from auditory_aphasia.process_management.process_communication_enums import AudioStatus
from auditory_aphasia.logging.logger import get_logger

logger = get_logger()


def get_required_time(plans, data):
    end_times = list()
    for plan in plans:
        end_time = data.get_length_by_id(plan[1])
        end_time += plan[0]
        end_times.append(end_time)
    return max(end_times)

class PyscabStimulationController(object):

    def __init__(self,
                 AudioHardwareController,
                 marker_send,
                 correct_latency = True,
                 correct_hardware_buffer = False,
                 time_tick = 0.0001,
                 state_dict=None):
        """
        class for playing stimulating plan.

        Attributes
        ----------
        AudioHardwareController : An instance of pyscab.AudioHardwareController class
        marker_send : reference to a function
            A reference to function for send a marker
        mode : str {'serial', 'pararell'} default = 'serial'
            If it's set to 'pararell', it can be controll from parent process.
        time_tick : float, default=0.0001
            pause between each loop in play() function. In terms of real time, it should be reduced.
            However, it also caused intence compulational load.
        state_dict : dictionary used to communicate between processes. Primarily used to track the audio device status

        """
        self.ahc = AudioHardwareController
        self.time_tick = time_tick
        self.correct_latency = correct_latency

        if self.correct_latency:
            self.offset = self.ahc.frames_per_buffer/self.ahc.frame_rate
            if correct_hardware_buffer is not False:
                if correct_hardware_buffer is True:
                    self.offset += self.ahc.device['defaultLowOutputLatency']
                else:
                    self.offset += correct_hardware_buffer/self.ahc.frame_rate
            self.marker_send_hw = marker_send
            self.marker_send = self.marker_send_offset
        else:
            self.marker_send = marker_send

        if state_dict is None:
            self.state_dict = init_audio_state_dict()
        else:
            self.state_dict = state_dict

        logger.debug("time_tick for Stimulation Controller was set to %s", str(self.time_tick))

    def open(self):
        self.ahc.open()
        logger.debug("Audio Hardware Controller Opened.")
        
    def close(self):
        self.ahc.close()
        logger.debug("Audio Hardware Controller Closed.")

    def marker_send_offset(self, val):
        t = threading.Thread(target=self.marker_send_offset_thread, kwargs=dict(val=val))
        t.start()

    def marker_send_offset_thread(self, val):
        time.sleep(self.offset)
        self.marker_send_hw(val=val)

    def play(self, plans, data, time_termination = 'auto', pause=0.5):

        # initialize
        self.state_dict["audio_status"] = AudioStatus.INITIAL

        del_idxs = list()
        if time_termination is None:
            # TODO : prep two functions for main_loop with and w/o termination with time
            #        to avoid verbosed conditional branch in loop
            time_termination = float('inf')
        elif time_termination.lower() == 'auto':
            time_termination = get_required_time(plans, data)
        
        logger.debug("session time was set to %s." ,str(time_termination))

        # requires time to be opened. with out this line, time_info won't be get
        # TO DO : get the state of instance from pyaudio and wait until it's opened instead of waiting with sleep
        #time.sleep(1)
        while self.ahc.get_time_info() is None:
            time.sleep(0.01)

        self.state_dict["audio_status"] = AudioStatus.PLAYING

        start = self.ahc.get_time_info()['current_time']
        while self.state_dict["audio_status"] == AudioStatus.PLAYING:
            now = self.ahc.get_time_info()['current_time'] - start
            for idx, plan in enumerate(plans):
                if now > plan[0]:
                    self.ahc.play(data.get_data_by_id(plan[1]),plan[2])
                    self.marker_send(val=plan[3])
                    self.state_dict["trial_marker" ] = plan[3]
                    del_idxs.append(int(idx))
                    logger.debug(f"Playing, id:{str(plan[1])}, ch:{str(plan[2])}, marker:{str(plan[3])}, path:f{data.get_path_by_id(plan[1])}")
                for del_idx in del_idxs:
                    del plans[del_idx]
                del_idxs=list()
            time.sleep(self.time_tick)
            if now > time_termination:
                self.state_dict["audio_status"] = AudioStatus.FINISHED_PLAYING
        time.sleep(pause)
