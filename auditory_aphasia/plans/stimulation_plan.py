import numpy as np


def generate_stimulation_plan(n_stim_types = 5, itrs = 10, min_stim_distance = 3):
    stim_list = np.arange(1, n_stim_types + 1)
    
    plan = stim_list.copy()

    np.random.seed()
    np.random.shuffle(plan)
    
    for itr in range(itrs-1):
        while True:
            cand = stim_list.copy()
            np.random.shuffle(cand)
            tmp = np.append(plan, cand)
            tmp_min_stim_distance = _get_minmax_stim_distance(tmp)[0]
            if tmp_min_stim_distance >= min_stim_distance:
                plan = tmp
                break

    plan = plan.tolist()
    return plan


def _get_minmax_stim_distance(sequence):
    stim_list = np.unique(sequence)
    distances = list()
    for stim in stim_list:
        idx = np.where(sequence == stim)
        distances.append(np.diff(idx))
    distances = np.hstack(distances)
    return np.min(distances), np.max(distances)