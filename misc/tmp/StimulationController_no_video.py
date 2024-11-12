from src.logging.logger import get_logger
import argparse
import pyscab
import pyencoder
import sys
import time
import datetime
import os
from markerbci import buttonbox
from threading import Thread
#from psychopy.visual import Window

import src.process_management.intermodule_communication as intermodule_comm
from src.plans.stimulation_plan import generate_stimulation_plan


logger = logging.getLogger("StimulationController." + __name__)

class Marker(object):
    def __init__(self, port=None, marker_duration = 0.05):
        self.port = port
        self.marker_duration = marker_duration

    def open(self):
        self._button_box = buttonbox.ButtonBoxBci(port=self.port)

    def close(self):
        self._button_box.close()

    def sendMarker_6D(self, val):
        if val != 0:
            self._button_box.sendMarker(val=val)
            logger.debug("sent marker:%s", str(val))
            if val == 210:
                pass
            elif int(val/100) == 2:
                word = int(str(val)[-1])
                speaker = word_to_speak[word-1]
                logger.debug("speaker No.%s was highlighted.", str(speaker))
            else:
                pass

        else:
            logger.debug("sent no marker (relax sentence played)")
            logger.debug("------------------------ trial ended ------------------------")

    def sendMarker(self, val):
        if val != 0:
            self._button_box.sendMarker(val=val)
            logger.debug("sent marker:%s", str(val))
        else:
            logger.debug("sent no marker (relax sentence played)")
            logger.debug("------------------------ trial ended ------------------------")

    def _send_buttonbox(self, val):
        marker_thread = Thread(target=self._send_buttonbox_thread, args=(val))
        marker_thread.start()

    def _send_buttonbox_thread(self, marker):
        self._button_box.sendMarker(val=marker)
        time.sleep(self.marker_duration)
        self._button_box.sendMarker(val=0)

def play(transformation):

    sudoku = common.Sudoku()
    global word_to_speak
    word_to_speak = sudoku.generate_matrix(1, 6)[0]
    targetplan = sudoku.generate_matrix(1, 6)[0]

    mrk = Marker(port="COM4")
    mrk.open()

    words = ['Spiegel', 'Blender', 'Groente', 'Stropdas', 'Tractor', 'Knuffel']

    logger.debug("words:%s", pyencoder.list2str(words))

    home_dir = os.path.expanduser('~')
    base_dir = "D:/Users/auditoryAphasia_stereo/auditoryAphasia_portable/auditoryAphasia/Feedbacks/media/online_paradigm/"
    logger.debug("base_dir:%s", base_dir)

    #------------------------------------------------
    # load audio files
    #

    logger.debug("word_to_speaker_mapping:%s", pyencoder.list2str(word_to_speak))
    logger.debug("targetplan:%s", pyencoder.list2str(targetplan))
    logger.debug("transformation:%s", transformation)
    
    volume = 0.25

    logger.debug("Master Volume:%s", volume)

    afh = pyscab.DataHandler()

    if 'Stereo' in transformation:
        ch_condition = [7,8]
        for m in range(0,6):
            idx = word_to_speak[m]
            word_dir = base_dir + "words_database_stereo/" + transformation + "/" + words[m] + "/" + str(idx) + ".wav"
            afh.load(m+1, word_dir, volume = volume)
            logger.debug("word loaded, id:%s, dir:%s, volume:%s", m+1, word_dir, volume)

        for m in range(0,6):
            idx = word_to_speak[m]    
            sentence_dir =  base_dir + "sentences_database_stereo/" + transformation + "/" + words[m] + "/" + str(idx) + ".wav"
            afh.load(m+1+10, sentence_dir, volume = volume)
            logger.debug("sentence loaded, id:%s, dir:%s, volume:%s", m+1, sentence_dir, volume)
    elif 'Mono' in transformation or '6D' == transformation:
        ch_condition = [7,8] 
        for m in range(0,6):
            word_dir = base_dir + "words_database" + "/Dutch_6D/" + str(m+1) + ".wav"
            afh.load(m+1, word_dir, volume = volume)
            logger.debug("word loaded, id:%s, dir:%s, volume:%s", m+1, word_dir, volume)

        for m in range(0,6):
            sentence_dir =  base_dir + "sentences_database" + "/Dutch_6D/" + str(m+1) + ".wav"
            afh.load(m+1+10, sentence_dir, volume = volume)
            logger.debug("sentence loaded, id:%s, dir:%s, volume:%s", m+1, sentence_dir, volume)
    elif '6D_Pitch' == transformation:
        for m in range(0,6):
            idx = word_to_speak[m]
            #word_dir = base_dir + "words_database" + "/Dutch_6D_Pitch/" + str(m+1) + ".wav"
            word_dir = base_dir + "words_database" + "/Dutch_6D_Pitch/" + words[m] + "/" + str(idx) + ".wav"
            afh.load(m+1, word_dir, volume = volume)
            logger.debug("word loaded, id:%s, dir:%s, volume:%s", m+1, word_dir, volume)

        for m in range(0,6):
            idx = word_to_speak[m]
            sentence_dir =  base_dir + "sentences_database" + "/Dutch_6D_Pitch/" + words[m] + "/" + str(idx) + ".wav"
            afh.load(m+1+10, sentence_dir, volume = volume)
            logger.debug("sentence loaded, id:%s, dir:%s, volume:%s", m+1, sentence_dir, volume)
    elif 'oddball' in transformation:
        ch_condition = [1]
        oddball_base = "D:/Users/auditoryAphasia_stereo/auditoryAphasia_portable/auditoryAphasia/Feedbacks/media/oddball"
        std_id = 1
        dev_id = 21
        afh.load(std_id, os.path.join(oddball_base, "500.wav"), volume=volume)
        logger.debug("sentence loaded, id:%s, dir:%s, volume:%s", std_id, os.path.join(oddball_base, "500.wav"), volume)
        afh.load(dev_id, os.path.join(oddball_base, "1000.wav"), volume=volume)
        logger.debug("sentence loaded, id:%s, dir:%s, volume:%s", dev_id, os.path.join(oddball_base, "1000.wav"), volume)

    restart_dir = "D:/Users/auditoryAphasia_stereo/auditoryAphasia_portable/auditoryAphasia/Feedbacks/media/speech_restart.wav"
    afh.load(100, restart_dir, volume = volume)
    logger.debug("restart loaded, id:%s, dir:%s, volume:%s", 100, restart_dir, volume)

    relax_dir = "D:/Users/auditoryAphasia_stereo/auditoryAphasia_portable/auditoryAphasia/Feedbacks/media/speech_relax.wav"
    afh.load(101, relax_dir, volume = volume)
    logger.debug("restart loaded, id:%s, dir:%s, volume:%s", 101, relax_dir, volume)
    #------------------------------------------------
    # audio play plan
    #

    # plan format
    # [time, file_id, ch, marker]

    number_of_repetitions = 15
    soa = 0.25

    if 'oddball' in transformation:
        soa = 1.0
        number_of_repetitions = 50 # 50->1min
    logger.debug("soa : %s", str(soa))
    logger.debug("number of repetitions : %s", str(number_of_repetitions))

    pause_between_trial = 5
    pause_after_start_sound = 2
    pause_between_sentence_and_subtrial = 3.5
    pause_before_trial_completion = 2

    offset_start = 1
    audio_plan = list()
    time_plan = 0
    time_plan += offset_start

    if '6D' in transformation:
        for trial_idx in range(6):
            target = targetplan[trial_idx]
            wordplan = generate_stimulation_plan(6, number_of_repetitions)

            audio_plan.append([time_plan, 100, [1], 210])
            time_plan += afh.get_length_by_id(100)
            time_plan += pause_after_start_sound
            audio_plan.append([time_plan, target+10, [word_to_speak[target-1]], 200 + target])
            time_plan += afh.get_length_by_id(target+10)
            time_plan += pause_between_sentence_and_subtrial
            for m in range(0, len(wordplan)):
                if wordplan[m] == target:
                    time_plan += soa
                    audio_plan.append([time_plan, wordplan[m], [word_to_speak[wordplan[m]-1]], 110 + target])
                else:
                    time_plan += soa
                    audio_plan.append([time_plan, wordplan[m], [word_to_speak[wordplan[m]-1]], 100 + wordplan[m]])
            time_plan += afh.get_length_by_id(wordplan[m])
            time_plan += pause_before_trial_completion
            audio_plan.append([time_plan, 101, [1], 0])
            time_plan += afh.get_length_by_id(101)
            time_plan += pause_between_trial
    elif 'oddball' in transformation:
        stimplan = generate_stimulation_plan(6, number_of_repetitions)
        for stim in stimplan:
            if stim == 1:
                audio_plan.append([time_plan, dev_id, ch_condition, 21])
            else:
                audio_plan.append([time_plan, std_id, ch_condition, 1])
            time_plan += soa
    else:
        for trial_idx in range(6):
            target = targetplan[trial_idx]
            wordplan = generate_stimulation_plan(6, number_of_repetitions)

            logger.debug("wordplan No.%s:%s", str(trial_idx+1), pyencoder.list2str(wordplan))

            audio_plan.append([time_plan, 100, ch_condition, 210])
            time_plan += afh.get_length_by_id(100)
            time_plan += pause_after_start_sound
            audio_plan.append([time_plan, target+10, ch_condition, 200 + target])
            time_plan += afh.get_length_by_id(target+10)
            time_plan += pause_between_sentence_and_subtrial
            for m in range(0, len(wordplan)):
                if wordplan[m] == target:
                    time_plan += soa
                    audio_plan.append([time_plan, wordplan[m], ch_condition, 110 + target])
                else:
                    time_plan += soa
                    audio_plan.append([time_plan, wordplan[m], ch_condition, 100 + wordplan[m]])
            time_plan += afh.get_length_by_id(wordplan[m])
            time_plan += pause_before_trial_completion
            audio_plan.append([time_plan, 101, ch_condition, 0])
            time_plan += afh.get_length_by_id(101)
            time_plan += pause_between_trial

    #------------------------------------------------
    # open and initialize Audio I/F
    #

    DEVICE_NAME = 'X-AIR ASIO Driver'
    #DEVICE_NAME = 'ASIO4ALL v2'
    #DEVICE_NAME = 'default'
    ahc = pyscab.AudioInterface(device_name = DEVICE_NAME, n_ch = 8, format="INT16", frames_per_buffer = 512)
   
    if '6D' in transformation or 'Stereo' in transformation:
        marker_func = mrk.sendMarker_6D
    else:
        marker_func = mrk.sendMarker
        
    stc = pyscab.StimulationController(ahc, marker_send=marker_func)
    logger.debug("Stimulation Controller Opened and Start playing.")
    stc.play(audio_plan, afh, time_termination = 'auto')
    ahc.terminate()
    logger.debug("Audio Hardware Controller terminated.")
    mrk.sendMarker_6D(val=255)
    logger.debug("Termination code for bbci toolbox (255) was sent.")
    logger.debug("Audio Device closed")
    time.sleep(1) # for sending marker 255 properly, just in case.
    mrk.close() # close marker device
    time.sleep(1) # for closing marker device properly, just in case.
    logger.debug("Marker Device closed")
    logger.debug("------------------------ Run ended ------------------------")

def set_logger(file=True, stdout=True):

    log_format = '%(asctime)s [%(levelname)s] [%(module)s.%(funcName)s] %(message)s'

    if stdout:
        stdout_handler = logging.StreamHandler(stream=sys.stdout)
        stdout_handler.setFormatter(logging.Formatter(log_format))
        stdout_handler.setLevel(logging.DEBUG)

    if file:
        logfile_prefix = "auditory_aphasia_"
        fname = "D:/Users/auditoryAphasia_stereo/logs/" + logfile_prefix + datetime.datetime.now().strftime("%d%b%y_%H%M%S") + ".log"
        file_handler = logging.FileHandler(fname)
        file_handler.setFormatter(logging.Formatter(log_format))
        file_handler.setLevel(logging.DEBUG)

    root_logger = logging.getLogger(None)
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(stdout_handler)
    root_logger.addHandler(file_handler)

    #logging.basicConfig(filename=fname, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%d/%m/%Y_%I:%M:%S', level=logging.DEBUG, force=True)
    
    
def main_debug():
    set_logger(file=True, stdout=True)
    logger.debug("process started.")
    while True:
        try:
            print("input transformation")
            transformation = input()
            logger.debug("start playing")
            play(transformation)
        except KeyboardInterrupt:
            break

def main_LSL():
    set_logger(file=True, stdout=True)
    logger.debug("process started.")
    intermodule_inlet = intermodule_comm.get_intermodule_communication_inlet('matlab', timeout=None)
    logger.debug("Lab Streaming Layer Connected.")
    while True:
        try:
            sample, timestamp = intermodule_inlet.pull_sample(timeout=0.5)
            if sample is not None:
                if sample[0] == 'word_to_speak':
                    word_to_speak = pyencoder.decode_list(sample[1])
                    logger.debug("parameter word_to_speak received via LSL.")
                    #is_received_word_to_speak = True
                elif sample[0] == 'transformation':
                    transformation = sample[1]
                    logger.debug("parameter 'transformation' received via LSL.")
                    #is_received_transformation = True
                elif sample[0] == 'targetplan':
                    targetplan = pyencoder.decode_list(sample[1])
                    logger.debug("parameter targetplan received via LSL.")
                    #is_received_targetplan = True
                elif sample[0] == 'command':
                    if sample[1] == 'play':
                        logger.debug("start playing")
                        play(transformation)
                        word_to_speak = None
                        transformation = None
                        targetplan = None
        except KeyboardInterrupt:
            break

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', help='debug mode', action='store_true')
    args = parser.parse_args()

    if args.debug:
        main_debug()
    else:
        main_LSL()
