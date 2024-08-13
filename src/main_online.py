import sys
import os
import json
import time

from multiprocessing import Process, Value, Array, Manager
import numpy as np
#from pylsl import StreamInfo, StreamOutlet

import conf_selector
# exec("import %s as conf" % (conf_selector.conf_file_name))
# exec("import %s as conf_system" % (conf_selector.conf_system_file_name))
import conf as conf
import conf_system as conf_system

import matplotlib
matplotlib.use('tkagg')

import utils
import pyscab

import common
import condition_params

conf_system.set_logger(True, True, level_file = 'debug', level_stdout = 'info')

import logging
logger = logging.getLogger(__name__)

if __name__ == '__main__':

    # make directory to save files
    isExist = os.path.exists(os.path.join(conf_system.data_dir, conf_system.save_folder_name))
    if not isExist:
        os.makedirs(os.path.join(conf_system.data_dir, conf_system.save_folder_name))

    # generate meta file
    meta = dict()
    meta['session_type'] = 'online'
    meta['words'] = conf.words
    with open(os.path.join(conf_system.data_dir, conf_system.save_folder_name, 'meta.json'), 'w') as f:
        json.dump(meta, f, indent=4)

    sys.path.append(conf_system.repository_dir_base)

    #----------------------------------------------------------------------
    # start stimulation

    # open LSL sender for sending commands to stimulation controller
    outlet = utils.createIntermoduleCommunicationOutlet('main', channel_count=4, id='auditory_aphasia_main')

    # open StimulationController as a new Process
    share_audio = Array('i', [0 for m in range(conf_system.len_shared_memory)])
    import audio.AudioController as AudioController
    audio_process = Process(target=AudioController.interface, args=('audio', 'main', False, False, share_audio))
    audio_process.start()
    while share_audio[2] == 0:
        time.sleep(0.1) # wait until module is connected

    # open VisualFeedbackController as a new Process
    share_visual = Array('d', [0 for m in range(conf_system.len_shared_memory)])
    import VisualFeedbackInterface
    visual_process = Process(target=VisualFeedbackInterface.interface, args=('visual', 'main', False, False, share_visual))
    visual_process.start()
    while share_visual[0] == 0:
        time.sleep(0.1) # wait until module is connected

    # open AcquisitionSystemController as a new Process
    share_acq = Array('d', [0 for m in range(conf_system.len_shared_memory)])
    import acquisition.AcquisitionSystemController as AcquisitionSystemController
    acq_process = Process(target=AcquisitionSystemController.interface, args=('acq', 'main', False, False, share_acq))
    acq_process.start()
    while share_acq[0] == 0:
        time.sleep(0.1) # wait until module is connected

    #while True:
    #for idx, trial_num in enumerate(range(1, number_of_words+1)):

    logger.info("open audio device")
    share_audio[2] = 0
    utils.send_cmd_LSL(outlet, 'audio', 'open')
    #time.sleep(3)
    while share_audio[2] == 0:
        time.sleep(0.1)
    logger.info("start recorder")
    utils.send_cmd_LSL(outlet, 'acq', 'init_recorder', {'session_type':'online'})
    time.sleep(1)

    #----------------------------------------------------------------------
    # load some parameters from conf file

    audio_files_dir_base = conf_system.audio_files_dir_base
    number_of_words = conf_system.number_of_words
    master_volume = conf.master_volume
    words = conf.words
    condition = conf.condition_online
    soa = conf.soa_online

    # eyes open close
    common.eyes_open_close(outlet, 'pre')

    # oddball
    common.play_oddball(outlet, share_audio, number_of_repetitions = conf.oddball_n_reps)

    utils.send_cmd_LSL(outlet, 'acq', 'init')
    utils.send_cmd_LSL(outlet, 'acq', 'connect_LSL')
    utils.send_cmd_LSL(outlet, 'acq', 'set')

    utils.send_params_LSL(outlet, 'acq', 'condition', condition)
    utils.send_params_LSL(outlet, 'acq', 'soa', soa)
    utils.send_cmd_LSL(outlet, 'acq', 'start_calibration')
    while share_acq[1] == 0:
        time.sleep(0.1)

    for m in range(conf.number_of_runs_online):

        plan_run = utils.generate_plan_run(audio_files_dir_base,
                                        words,
                                        condition,
                                        condition_params.conditions[condition],
                                        master_volume)

        audio_info = plan_run['audio_info']
        audio_files = plan_run['audio_files']
        word2spk = plan_run['word2spk']
        targetplan = plan_run['targetplan']

        n_runs = 1
        while True:
            #f_name = utils.gen_eeg_fname(os.path.join(conf.data_dir, conf.save_folder_name), conf.f_name_prefix, condition, soa, idx_run)
            f_name = os.path.join(conf_system.data_dir,
                                  conf_system.save_folder_name,
                                  "%s_%s_%s_%s.%s" %(conf.f_name_prefix, condition, str(int(soa*1000)), str(n_runs).zfill(4), 'eeg'))
            print(f_name)
            if os.path.exists(f_name):
                n_runs += 1
            else:
                break

        time.sleep(1)
        val = input("Press Any Key to Start A New Run (No.%d) or type 'n' to terminate : " %n_runs)
        if val.lower() == 'n':
            break

        logger.info('plan_run : %s' %str(plan_run))
        utils.send_cmd_LSL(outlet, 'acq','start_recording', f_name)
        utils.send_cmd_LSL(outlet, 'acq', 'start')

        for idx, trial_num in enumerate(range(1, number_of_words+1)):
        #for idx, trial_num in enumerate(range(1,2)):
            target = targetplan[idx]
            #time.sleep(2)
            
            plan_trial = utils.generate_plan_trial(audio_files,
                                                 word2spk,
                                                 target,
                                                 condition,
                                                 soa,
                                                 conf.number_of_repetitions,
                                                 number_of_words,
                                                 conf_system.ch_speaker,
                                                 conf_system.ch_headphone,
                                                 condition_params.conditions[condition],
                                                 online = True)

            word = conf.words[target-1]
            logger.debug("word : %s" %word)
            sentence_data = pyscab.DataHandler()
            sentence_data.load(0, os.path.join(conf_system.repository_dir_base,
                                             'media',
                                             'audio',
                                             conf.language,
                                             'sentences',
                                             condition,
                                             word,
                                             '1.wav'))
            sentence_duration = sentence_data.get_length_by_id(0)

            logger.info("plan_trial : %s" %str(plan_trial))
            play_plan = plan_trial['play_plan']
            word_plan = plan_trial['word_plan']
            utils.send_params_LSL(outlet, 'audio', 'audio_info', audio_info)
            utils.send_params_LSL(outlet, 'audio', 'marker', True)

            #utils.send_cmd_LSL(outlet, 'acq','start_recording', os.path.join('D:/','data','test_2209'))
            utils.send_cmd_LSL(outlet, 'audio', 'play', play_plan)
            share_acq[1] = 0
            share_audio[3] = 1

            marker = int(share_audio[1])
            spk_shown = False
            show_speaker_diagram = condition_params.conditions[condition]["show_speaker_diagram"]
            while share_acq[1] == 0:
                if int(share_audio[1]) != marker and show_speaker_diagram:
                    marker = int(share_audio[1])
                    if marker in conf_system.markers['new-trial']:  
                        utils.send_cmd_LSL(outlet, 'visual', 'highlight_speaker', {'spk_num':word2spk[marker-200], 'duration':sentence_duration})
                    elif marker == 210:
                        utils.send_cmd_LSL(outlet, 'visual', 'show_speaker')
                time.sleep(0.01)

            if share_audio[0] == 1:
                share_audio[0] = 2
            #utils.send_cmd_LSL(outlet, 'audio', 'stop')
            while True: # wait until audio module stop
                if share_audio[0] == 99:
                    logger.info("status value is 99, terminate")
                    break
                else:
                    time.sleep(0.1)
                    logger.info("wait for audio module is terminated")

            fb_type = share_acq[2]
            if fb_type == 2 and share_acq[4] == conf_system.dynamic_stopping_params['min_n_stims']:
                if np.random.randint(5) == 0: # np.random.randint(5) = ints between 0 - 4.
                    fb_type = 3
            #logger.info("feedback type : %d" %fb_type)

            if fb_type == 0:
                visual_fb = 'neutral'
            elif fb_type == 1:
                visual_fb = 'positive'
            elif fb_type == 2:
                visual_fb = 'smiley'
            elif fb_type == 3:
                visual_fb = 'show_gif'
            logger.info("feedback type ; %s" %visual_fb)

            fb_plan = utils.generate_plan_feedback(audio_files_dir_base,
                                            words,
                                            share_acq[3],
                                            fb_type,
                                            condition,
                                            conf_system.ch_speaker,
                                            conf_system.ch_headphone,
                                            condition_params.conditions[condition],
                                            master_volume)    
            utils.send_params_LSL(outlet, 'audio', 'audio_info', fb_plan['audio_info'])
            #utils.send_params_LSL(outlet, 'audio', 'marker', False)

            time.sleep(conf_system.pause_before_feedback)

            if visual_fb == 'show_gif':
                    utils.send_cmd_LSL(outlet, 'visual', 'show_gif')
            else:
                utils.send_cmd_LSL(outlet, 'visual', "show_" + visual_fb)

            utils.send_cmd_LSL(outlet, 'audio', 'play', fb_plan['play_plan'])
            share_audio[0] = 0

            while share_audio[0] != 99:
                time.sleep(0.1)
            #time.sleep(3)
            if visual_fb != 'show_gif':
                utils.send_cmd_LSL(outlet, 'visual', "hide_" + visual_fb)

            logger.info("Trial ended, observed by main module")
            #utils.send_cmd_LSL(outlet, 'acq', 'stop_recording')
            share_audio[0] = 0 # reinitialize status

            if conf_system.enable_pause_between_trial:
                input("Press Any Key to Start A New Trial")
            else:
                time.sleep(conf_system.pause_between_trial)                
        share_acq[5] = 0
        utils.send_cmd_LSL(outlet, 'acq', 'stop_recording')

    # eyes open close
    common.eyes_open_close(outlet, 'post')

    utils.send_cmd_LSL(outlet, 'audio', 'close')
    time.sleep(3)

    audio_process.terminate()
    visual_process.terminate()
    acq_process.terminate()
    print("all trial ended, terminate process by main module")
    #sys.exit()