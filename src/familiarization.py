import utils
import pyscab
import os
import sys
import argparse
import condition_params

import conf_selector
# exec("import %s as conf" % (conf_selector.conf_file_name))
# exec("import %s as conf_system" % (conf_selector.conf_system_file_name))
import conf as conf
import conf_system as conf_systems

parser = argparse.ArgumentParser()

parser.add_argument('-n', '--n_reps', type=int, default=3)
parser.add_argument('-v', '--visual', action='store_true')

args = parser.parse_args()

NUMBER_OF_REPETITIONS = args.n_reps
    
def gen_plan_play_each_word(word_idx_to_be_played, base_dir, soa=1.5, ch = [1], marker = None, volume = 1):

    word_dir = os.path.join(base_dir,
                            'media',
                            'audio',
                            conf.language,
                            'words',
                            '6d',
                            conf.words[word_idx_to_be_played-1],
                            '1.wav')

    plan = list()
    for m in range(NUMBER_OF_REPETITIONS):
        plan.append([m*soa, 1, ch, marker])

    data = pyscab.DataHandler()
    data.load(1, word_dir, volume = volume)
        
    return plan, data

def gen_plan_sentence_and_word(ahc, word_idx_to_be_played, base_dir, pause_between_sentence_and_subtrial=1.5, ch = [1], marker = None, volume = 1):
    import time
    word_dir = os.path.join(base_dir,
                            'media',
                            'audio',
                            conf.language,
                            'words',
                            '6d',
                            conf.words[word_idx_to_be_played-1],
                            '1.wav')

    sentence_dir = os.path.join(base_dir,
                            'media',
                            'audio',
                            conf.language,
                            'sentences',
                            '6d',
                            conf.words[word_idx_to_be_played-1],
                            '1.wav')

    data = pyscab.DataHandler()
    data.load(1, sentence_dir, volume = volume)
    data.load(2, word_dir, volume = volume)

    sentence_data = data.get_data_by_id(1)
    word_data = data.get_data_by_id(2)
    
    ahc.open()
    ahc.play(sentence_data, ch)
    time.sleep(data.get_length_by_id(1))
    input("Press Any Key to Play Word : %s" %(conf.words[word_idx_to_be_played-1]))
    ahc.play(word_data, ch)
    time.sleep(data.get_length_by_id(2)*1.05)
    ahc.close()

def gen_plan_spk_fam(base_dir, condition, soa=1, volume = 1):

    data = pyscab.DataHandler()

    sudoku = utils.Sudoku()
    #word2spk = [1, 2, 3, 4, 5, 6]
    targetplan = sudoku.generate_matrix(1, 6)[0]
    word2spk = sudoku.generate_matrix(1, 6)[0]

    for idx, word in enumerate(conf.words):
        if condition_params.conditions[condition]['single_file']:
            f_name = '1.wav'
        else:
            f_name = '%d.wav' %(word2spk[idx])

        word_dir = os.path.join(base_dir,
                                'media',
                                'audio',
                                conf.language,
                                'words',
                                condition,
                                word,
                                f_name)

        sentence_dir = os.path.join(base_dir,
                                'media',
                                'audio',
                                conf.language,
                                'sentences',
                                condition,
                                word,
                                f_name)

        data.load(idx+1, word_dir, volume = volume)
        data.load(idx+1+10, sentence_dir, volume = volume)

    restart_dir = os.path.join(base_dir,
                            'media',
                            'audio',
                            conf.language,
                            'misc',
                            'restart.wav')
    data.load(100, restart_dir, volume = volume)

    relax_dir = os.path.join(base_dir,
                            'media',
                            'audio',
                            conf.language,
                            'misc',
                            'relax.wav')
    data.load(101, relax_dir, volume = volume)

    pause_between_trial = 5
    pause_after_start_sound = 2
    pause_between_sentence_and_subtrial = 3.5
    pause_before_trial_completion = 2
    number_of_repetitions = NUMBER_OF_REPETITIONS

    offset_start = 1
    audio_plan = list()

    time_plan = 0
    time_plan += offset_start
    for trial_idx in range(6):
        target = targetplan[trial_idx]
        wordplan = utils.generate_stimulation_plan(6, number_of_repetitions)

        audio_plan.append([time_plan, 100, [1], 210])
        time_plan += data.get_length_by_id(100)
        time_plan += pause_after_start_sound
        audio_plan.append([time_plan, target+10, [word2spk[target-1]], 200 + target])
        time_plan += data.get_length_by_id(target+10)
        time_plan += pause_between_sentence_and_subtrial
        for m in range(0, len(wordplan)):
            if wordplan[m] == target:
                time_plan += soa
                audio_plan.append([time_plan, wordplan[m], [word2spk[wordplan[m]-1]], 110 + target])
            else:
                time_plan += soa
                audio_plan.append([time_plan, wordplan[m], [word2spk[wordplan[m]-1]], 100 + wordplan[m]])
        time_plan += data.get_length_by_id(wordplan[m])
        time_plan += pause_before_trial_completion
        audio_plan.append([time_plan, 101, [1], 0])
        time_plan += data.get_length_by_id(101)
        time_plan += pause_between_trial

    return audio_plan, data

def gen_plan_hp_fam(base_dir, condition, soa=1, volume = 1, ch = [7,8]):

    data = pyscab.DataHandler()

    for idx, word in enumerate(conf.words):

        if condition_params.conditions[condition]['single_file']:
            f_name = '1.wav'
        else:
            f_name = '%d.wav' %(idx+1)

        word_dir = os.path.join(base_dir,
                                'media',
                                'audio',
                                conf.language,
                                'words',
                                condition,
                                word,
                                f_name)

        sentence_dir = os.path.join(base_dir,
                                'media',
                                'audio',
                                conf.language,
                                'sentences',
                                condition,
                                word,
                                f_name)

        data.load(idx+1, word_dir, volume = volume)
        data.load(idx+1+10, sentence_dir, volume = volume)

    restart_dir = os.path.join(base_dir,
                            'media',
                            'audio',
                            conf.language,
                            'misc',
                            'restart.wav')
    data.load(100, restart_dir, volume = volume)

    relax_dir = os.path.join(base_dir,
                            'media',
                            'audio',
                            conf.language,
                            'misc',
                            'relax.wav')
    data.load(101, relax_dir, volume = volume)

    pause_between_trial = 5
    pause_after_start_sound = 2
    pause_between_sentence_and_subtrial = 3.5
    pause_before_trial_completion = 2
    number_of_repetitions = NUMBER_OF_REPETITIONS

    sudoku = utils.Sudoku()
    word2spk = sudoku.generate_matrix(1, 6)[0]
    #word2spk = [1, 2, 3, 4, 5, 6]
    targetplan = sudoku.generate_matrix(1, 6)[0]

    offset_start = 1
    audio_plan = list()

    time_plan = 0
    time_plan += offset_start
    for trial_idx in range(6):
        target = targetplan[trial_idx]
        wordplan = utils.generate_stimulation_plan(6, number_of_repetitions)

        audio_plan.append([time_plan, 100, ch, 210])
        time_plan += data.get_length_by_id(100)
        time_plan += pause_after_start_sound
        audio_plan.append([time_plan, target+10, ch, 200 + target])
        time_plan += data.get_length_by_id(target+10)
        time_plan += pause_between_sentence_and_subtrial
        for m in range(0, len(wordplan)):
            if wordplan[m] == target:
                time_plan += soa
                audio_plan.append([time_plan, wordplan[m], ch, 110 + target])
            else:
                time_plan += soa
                audio_plan.append([time_plan, wordplan[m], ch, 100 + wordplan[m]])
        time_plan += data.get_length_by_id(wordplan[m])
        time_plan += pause_before_trial_completion
        audio_plan.append([time_plan, 101, ch, 0])
        time_plan += data.get_length_by_id(101)
        time_plan += pause_between_trial

    return audio_plan, data

def gen_plan_play_oddball(soa=1, num_reps=10, volume = 1, ch = [7,8]):
    oddball_base = os.path.join(conf_system.repository_dir_base, 'media', 'audio', 'oddball')
    nT_id = 1
    T_id = 21
    audio_files = pyscab.DataHandler()
    audio_files.load(nT_id, os.path.join(oddball_base, conf_system.oddball_non_target), volume=conf.master_volume)
    audio_files.load(T_id, os.path.join(oddball_base, conf_system.oddball_target), volume=conf.master_volume)
    
    #soa_oddball = 1.0
    #number_of_repetitions_oddball = 1 # 50->5min

    play_plan = list()
    stimplan = utils.generate_stimulation_plan(6, num_reps)
    time_plan = 0
    for stim in stimplan:
        if stim == 1:
            play_plan.append([time_plan, T_id, [1], 21])
        else:
            play_plan.append([time_plan, nT_id, [1], 1])
        time_plan += soa

    return play_plan, audio_files


def sendMarker(val):
    pass

if args.visual:
    outlet = utils.createIntermoduleCommunicationOutlet('main', channel_count=4, id='main')
spk_showed = False
def sendMarker_visual(val):
    if args.visual:
        global spk_showed
        global outlet
        if val == 210:
            utils.send_cmd_LSL(outlet, 'visual', 'show_speaker')
            spk_showed = True
        
        if val >= 200 and val <= 205:
            spk_showed = True
            spk_num = str(val)
            spk_num = int(spk_num[-1])+1
            utils.send_cmd_LSL(outlet, 'visual', 'highlight_speaker', spk_num)

        if val >= 101 and val <= 116:
            if spk_showed:
                utils.send_cmd_LSL(outlet, 'visual', 'show_crosshair')
                spk_showed = False

def main():

    if args.visual:
        from multiprocessing import Process, Array
        import time
        # open VisualFeedbackController as a new Process
        share_visual = Array('d', [0 for m in range(conf_system.len_shared_memory)])
        import VisualFeedbackInterface
        visual_process = Process(target=VisualFeedbackInterface.interface, args=('visual', 'main', False, False, share_visual, False, 0))
        visual_process.start()
        while share_visual[0] == 0:
            time.sleep(0.1) # wait until module is connected
        #utils.send_cmd_LSL(outlet, 'visual', 'show_crosshair')

    words = conf.words

    #home_dir = os.path.expanduser('~')
    #base_dir = "D:/Users/auditoryAphasia_stereo/auditoryAphasia_portable/auditoryAphasia/Feedbacks/media/online_paradigm/"

    base_dir = conf_system.repository_dir_base

    share = [0 for m in range(8)]

    ahc = pyscab.AudioInterface(device_name = conf_system.device_name,
                                n_ch = conf_system.n_ch,
                                format=conf_system.format,
                                frames_per_buffer = conf_system.frames_per_buffer)
    stc = pyscab.StimulationController(ahc, marker_send=sendMarker_visual, share=share)

    isfamiliarizing = True

    MasterVolume = conf.master_volume

    if os.environ['computername'].lower() == 'am4':
        hp_ch = [1,2]
    else:
        hp_ch = [7,8]


    while isfamiliarizing:
        print('--------------------------------------------------------')
        print('Familiarization begins. You have the following choices:')
        print('0: Quit familiarization')
        print('1: Oddball')
        print('2: Play Each word')
        print('3: Sentences and words from one speaker')
        print('4: 6D run with customizable SOA.')
        print('5: StereoPitch run with customizable SOA.')
        print('6: Mono run with customizable SOA.')
        print('------ Choose one now by inserting a number between [0-6] -------')
        try:
            selected_fam_stage = input()
            if int(selected_fam_stage) == 0:
                sys.exit()
            elif int(selected_fam_stage) == 1:
                audio_plan, audio_data = gen_plan_play_oddball()
            elif int(selected_fam_stage) == 2:
                # play each word
                print('Stage  2: Select words to play. (The index starts from 1)')
                print('Words : ' + str(words))
                selected_word = input()
                audio_plan, audio_data = gen_plan_play_each_word(int(selected_word), base_dir, volume=MasterVolume)
            elif int(selected_fam_stage) == 3:
                # sentence and word
                print('Stage 3: Select words to play. (The index starts from 1)')
                print('Words : ' + str(words))
                selected_word = input()
                gen_plan_sentence_and_word(ahc, int(selected_word), base_dir, volume=MasterVolume)
                continue
            elif int(selected_fam_stage) == 4:
                # 6d
                print('Stage 4: Specify SOA (in seconds) for the familiarization:')
                selected_soa = input()
                print('Do you want to play 6d-pitch? if so, type y')
                en_pitch_shift = input()
                if en_pitch_shift == 'y':
                    condition = '6d-pitch'
                else:
                    condition = '6d'

                audio_plan, audio_data = gen_plan_spk_fam(base_dir, condition, soa=float(selected_soa), volume=MasterVolume)
            elif int(selected_fam_stage) == 5:
                # stereo-pitch
                print('Stage 5: Specify SOA (in seconds) for the familiarization:')
                selected_soa = input()
                audio_plan, audio_data = gen_plan_hp_fam(base_dir, condition='stereo-pitch', soa=float(selected_soa), volume=MasterVolume, ch=hp_ch)
            elif int(selected_fam_stage) == 6:
                # mono
                print('Stage 6: Specify SOA (in seconds) for the familiarization:')
                selected_soa = input()
                audio_plan, audio_data = gen_plan_hp_fam(base_dir, condition='mono', soa=float(selected_soa), volume=MasterVolume, ch=hp_ch)
            elif int(selected_fam_stage) == 0:
                sys.exit()
            else:
                continue
            stc.open()
            stc.play(audio_plan, audio_data, time_termination = 'auto', pause=0)
            stc.close()
        except KeyboardInterrupt:
            share[0] = 2
            if args.visual:
                visual_process.terminate()
            sys.exit()
        except ValueError:
            print("ERROR : input value was invailed.")
            main()
        except FileNotFoundError:
            print("ERROR : File was not found")
            main()
    share[0] = 2
    if args.visual:
        visual_process.terminate()
    sys.exit()

if __name__ == '__main__':
    main()
