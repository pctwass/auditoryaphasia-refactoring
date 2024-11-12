import sys
import os
from tkinter import Misc
import mne

import numpy as np
from pylsl import StreamInlet, resolve_stream
import src.acquisition.epoch_container as epoch_container
import src.acquisition.OnlineDataAcquire as OnlineDataAcquire
import src.config.system_config as system_config

ENABLE_STREAM_INLET_RECOVER = False
FILTER_ORDER = 2
FILTER_FREQ = [0.5, 8]
MARKERS_TO_EPOCH = [1, 5]

#EPOCH_RANGE = [-0.2, 1.2]
EPOCH_T_MIN = -0.2
EPOCH_T_MAX = 1.2
#EPOCH_BASELINE = (-0.05, 0)
EPOCH_BASELINE = None

#EOG_CHANNELS = ['EOGvu']
#MISC_CHANNELS = ['x_EMGl', 'x_GSR', 'x_Respi', 'x_Pulse', 'x_Optic']

EOG_CHANNELS = None
MISC_CHANNELS = None

markers = dict()
markers['target'] = [111,112,113,114,115,116]
markers['non-target'] = [101,102,103,104,105,106]
markers['new-trial'] = [200,201,202,203,204,205]

MARKERS_TO_EPOCH = markers['target'] + markers['non-target']

def main():

    idx_learn = [4,7,10,13,16]

    home_dir = os.path.expanduser('~')
    git_dir = os.path.join(home_dir, 'git')
    data_dir = os.path.join(home_dir, 'Documents', 'eeg','auditory_aphasia','lecture')
    sys.path.append(git_dir)

    f_name_suffix = 'auditoryAphasia_6D_Block1_Run'
    raws = list()
    for idx in idx_learn:
        f_dir = os.path.join(data_dir, f_name_suffix + str(idx) + ".vhdr")
        raw = mne.io.read_raw(f_dir, preload=True, eog=EOG_CHANNELS, misc=MISC_CHANNELS)
        raw.filter(l_freq = FILTER_FREQ[0], h_freq = FILTER_FREQ[1], method='iir')
        #raw.set_montage('standard_1020')
        raws.append(raw)
    raw = mne.concatenate_raws(raws)
    events, event_id = mne.events_from_annotations(raw)

    epochs = mne.Epochs(raw, events, event_id=MARKERS_TO_EPOCH, tmin=EPOCH_T_MIN, tmax=EPOCH_T_MAX, baseline=EPOCH_BASELINE)

    from sklearn.pipeline import make_pipeline
    from sklearn.model_selection import StratifiedKFold, permutation_test_score
    from sklearn.metrics import get_scorer, roc_auc_score, accuracy_score
    from toeplitzlda.classification import ShrinkageLinearDiscriminantAnalysis, ToeplitzLDA
    from pylibs.classification import EpochsVectorizer

    classifier = 'toe'

    if classifier == 'shrinkage':
        clf = make_pipeline(
            ShrinkageLinearDiscriminantAnalysis(n_channels=len(epochs.ch_names)),
        )
    elif classifier == 'toe':
        clf = make_pipeline(
            ToeplitzLDA(n_channels=len(epochs.ch_names)),
        )


    ivals = [[0.08, 0.15],
            [0.151, 0.21],
            [0.211, 0.28],
            [0.271, 0.35],
            [0.351, 0.44],
            [0.45, 0.56],
            [0.561, 0.7],
            [0.701, 0.85],
            [0.851, 1],
            [1.001, 1.2]]

    vectorizer = EpochsVectorizer(jumping_mean_ivals=ivals, sfreq = epochs.info['sfreq'], t_ref = epochs.times[0])
    X = vectorizer.transform(epochs)

    events = epochs.events
    events = mne.merge_events(events, markers['target'], 10)
    events = mne.merge_events(events, markers['non-target'], 1)

    Y = events[:, -1]

    clf.fit(X, Y)

    # ------------------------------------------------------------------------------------------------
    # find/connect eeg outlet

    print("looking for an EEG stream...")
    eeg_stream = resolve_stream('type', 'EEG')
    eeg_inlet = StreamInlet(eeg_stream[0], recover=ENABLE_STREAM_INLET_RECOVER)
    n_channels = eeg_stream[0].channel_count()
    n_channels = fmt_converter.n_ch_convert(n_channels)

    sample_freq = eeg_stream[0].nominal_srate()

    # ------------------------------------------------------------------------------------------------
    # find/connect marker outlet

    print("looking for a marker stream...")
    marker_stream = resolve_stream('type', 'Markers')
    marker_inlet = StreamInlet(marker_stream[0], recover=ENABLE_STREAM_INLET_RECOVER)

    epochs = epoch_container.EpochContainer(n_channels, sample_freq, MARKERS_TO_EPOCH, EPOCH_T_MIN, EPOCH_T_MAX, EPOCH_BASELINE)
    
    formatting_client = system_config.FormattingClient()
    acq = OnlineDataAcquire.OnlineDataAcquire(
                            epochs,
                            eeg_inlet,
                            marker_inlet,
                            n_channels,
                            sample_freq,
                            formatting_client.eeg_format_convert,
                            formatting_client.marker_format_convert,
                            filter_freq=FILTER_FREQ,
                            filter_order=FILTER_ORDER,
                            new_trial_markers=markers['new-trial'])
    acq.start()

    labels = np.array([], dtype=np.int64)
    preds = np.array([], dtype=np.int64)

    try:
        while True:

            new_trial = acq.is_new_trial()
            #print(new_trial)
            if new_trial:
                pass
                #print(new_trial)


            if epochs.has_new_data():
                epoch = epochs.get_new_data()
                vec = vectorizer.transform(epoch)
                labels = np.append(labels, epoch.events[:,-1]).astype(np.int64)
                preds = np.append(preds, clf.predict(vec)).astype(np.int64)
                acc = accuracy_score(labels, preds)
                print("Acc : %.3f"%acc)

    except KeyboardInterrupt:
        print(labels)
        print(preds)

if __name__ == '__main__':
    main()