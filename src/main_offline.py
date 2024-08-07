import sys
import os
import json
import time

from multiprocessing import Process, Value, Array, Manager

import conf_selector
# exec("import %s as conf" % (conf_selector.conf_file_name))
# exec("import %s as conf_system" % (conf_selector.conf_system_file_name))
import conf as conf
import conf_system as conf_system

import utils
import pyscab
import condition_params
import common

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
    meta['session_type'] = 'offline'
    meta['words'] = conf.words
    with open(os.path.join(conf_system.data_dir, conf_system.save_folder_name, 'meta.json'), 'w') as f:
        json.dump(meta, f, indent=4)

    sys.path.append(conf_system.repository_dir_base)
    number_of_words = conf_system.number_of_words

    logger.debug("computer : %s" %conf_system.computer_name)
    logger.debug("subject code : %s" %conf.subject_code)

    #----------------------------------------------------------------------
    # start stimulation

    # open LSL sender for sending commands to stimulation controller
    outlet = utils.createIntermoduleCommunicationOutlet('main', channel_count=4, id='auditory_aphasia_main')

    # open StimulationController as a new Process
    share_audio = Array('i', [0 for m in range(conf_system.len_shared_memory)])
    import AudioController
    audio_process = Process(target=AudioController.interface, args=('audio', 'main', True, True, share_audio))
    audio_process.start()
    while share_audio[2] == 0:
        time.sleep(0.1) # wait until module is connected
    #utils.send_cmd_LSL(outlet, 'audio','open')

    # open VisualFeedbackController as a new Process
    share_visual = Array('d', [0 for m in range(conf_system.len_shared_memory)])
    import VisualFeedbackInterface
    visual_process = Process(target=VisualFeedbackInterface.interface, args=('visual', 'main', True, True, share_visual))
    visual_process.start()
    while share_visual[0] == 0:
        time.sleep(0.1) # wait until module is connected

    # open AcquisitionSystemController as a new Process
    share_acq = Array('d', [0 for m in range(conf_system.len_shared_memory)])
    import AcquisitionSystemController
    acq_process = Process(target=AcquisitionSystemController.interface, args=('acq', 'main', True, True, share_acq))
    acq_process.start()
    while share_acq[0] == 0:
        time.sleep(0.1) # wait until module is connected

    logger.info("open audio device")
    share_audio[2] = 0
    utils.send_cmd_LSL(outlet, 'audio', 'open')
    #time.sleep(3)
    while share_audio[2] == 0:
        time.sleep(0.1)
    logger.info("start recorder")
    utils.send_cmd_LSL(outlet, 'acq', 'init_recorder', {'session_type':'offline'})
    time.sleep(1)

    # eyes open close
    common.eyes_open_close(outlet, 'pre')

    # oddball
    common.play_oddball(outlet, share_audio, number_of_repetitions = conf.oddball_n_reps)

    idx_run_offset = 0
    if conf.initial_run_offline != 1:
        condition_plan = conf.condition_offline[conf.initial_run_offline-1:]
        idx_run_offset += conf.initial_run_offline-1
    else:
        condition_plan = conf.condition_offline

    for idx_run, condition in enumerate(condition_plan):
        
        idx_run += idx_run_offset
        soa = conf.soa_offline[idx_run]

        time.sleep(1)
        input("Press Any Key to Start a New Run, %s, SOA %sms" %(condition, soa))
        logger.debug("new run started, %d out of %d" %(idx_run+1, len(conf.condition_offline)))
        logger.debug("condition of run : %s" %condition)
        #plan_run = generate_plan_run(condition)
        plan_run = utils.generate_plan_run(conf_system.audio_files_dir_base,
                                           conf.words,
                                           condition,
                                           condition_params.conditions[condition],
                                           conf.master_volume)

        audio_info = plan_run['audio_info']
        audio_files = plan_run['audio_files']
        word2spk = plan_run['word2spk']
        targetplan = plan_run['targetplan']

        utils.send_params_LSL(outlet, 'audio', 'audio_info', audio_info)
        utils.send_params_LSL(outlet, 'audio', 'marker', True)
        
        f_name = utils.gen_eeg_fname(os.path.join(conf_system.data_dir, conf_system.save_folder_name), conf.f_name_prefix, condition, soa, idx_run, 'eeg', session_type = conf.offline_session_type)
        utils.send_cmd_LSL(outlet, 'acq','start_recording', f_name)

        for word_idx in range(conf_system.number_of_words):
            share_audio[0] = 0
            target = targetplan[word_idx]
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
                                                   online=False)
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
            utils.send_cmd_LSL(outlet, 'audio', 'play', play_plan)
            marker = int(share_audio[1])
            marker = 0
            cnt = 0
            spk_shown = False
            show_speaker_diagram = condition_params.conditions[condition]["show_speaker_diagram"]
            while True:
                if int(share_audio[1]) != marker and show_speaker_diagram:
                    marker = int(share_audio[1])
                    if marker in conf_system.markers['new-trial']:  
                        utils.send_cmd_LSL(outlet, 'visual', 'highlight_speaker', {'spk_num':word2spk[marker-200], 'duration':sentence_duration})
                    elif marker == 210:
                        utils.send_cmd_LSL(outlet, 'visual', 'show_speaker')
                if share_audio[0] == 99:
                    share_audio[0] = 0
                    break
                time.sleep(0.01)
            time.sleep(conf_system.pause_between_trial)
        utils.send_cmd_LSL(outlet, 'acq', 'stop_recording')
    
    # eyes open close
    common.eyes_open_close(outlet, 'post')

    #utils.send_cmd_LSL(outlet, 'audio', 'close')
    #time.sleep(3)
    
    #time.sleep(1)
    utils.send_cmd_LSL(outlet, 'audio','close')
    time.sleep(3)
    audio_process.terminate()
    visual_process.terminate()
    acq_process.terminate()
    logger.info("All procceses were terminated. Exit program.")