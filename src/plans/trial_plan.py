import src.config.system_config as system_config

from src.plans.stimulation_plan import generate_stimulation_plan


def generate_trial_plan(audio_files,
                        word_to_speak,
                        target,
                        condition,
                        soa,
                        number_of_repetitions,
                        number_of_words,
                        ch_speaker,
                        ch_headphone,
                        condition_params,
                        online = False):

    play_plan = list()
    word_plan = generate_stimulation_plan(number_of_words, number_of_repetitions)
    time_plan = 0 # you can add pause before trial.
    if condition_params['output'] == 'speaker':
        play_plan.append([time_plan, 100, [ch_speaker[0]], 210])
    elif condition_params['output'] == 'headphone':
        play_plan.append([time_plan, 100, ch_headphone, 210]) # play restart sound
    time_plan += audio_files.get_length_by_id(100)
    time_plan += system_config.pause_after_start_sound

    # === About the marker of sentence ===
    # Sending 201 for word 1 is straight forward,
    # however, in original script, index for sentence is starting from 0.
    # i.e. word 1 : marker for word -> 101 or 111, marker for sentence -> 200
    #
    # for compatibility, python implementation is also follow this marker configuration.
    if condition_params['output'] == 'speaker':
        play_plan.append([time_plan, target+10, [ch_speaker[word_to_speak[target-1]-1]], 200+target-1])
    elif condition_params['output'] == 'headphone':
        play_plan.append([time_plan, target+10, ch_headphone, 200+target-1]) # play sentence

    # ====================================

    time_plan += system_config.pause_between_sentence_and_subtrial
    time_plan += audio_files.get_length_by_id(target+10)
    for word_num in word_plan:
        time_plan += soa
        if condition_params['output'] == 'speaker':
            spk = [ch_speaker[word_to_speak[word_num-1]-1]]
        elif condition_params['output'] == 'headphone':
            spk = ch_headphone
        
        if word_num == target:
            marker = 110 + target
        else:
            marker = 100 + word_num

        play_plan.append([time_plan, word_num, spk, marker])
    
    if online is False:
        time_plan += system_config.pause_after_trial
        if condition_params['output'] == 'speaker':
            play_plan.append([time_plan, 101, [ch_speaker[0]], 0])
        elif condition_params['output'] == 'heaphone':
            play_plan.append([time_plan, 101, ch_headphone, 0])

    plan = dict()
    plan['play_plan'] = play_plan
    plan['word_plan'] = word_plan

    return plan