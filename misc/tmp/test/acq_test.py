import sys
import os
import mne

#import numpy as np
from pylsl import StreamInlet, resolve_stream
import acquisition.container as container
import acquisition.OnlineDataAcquire as OnlineDataAcquire
import fmt_converter

home_dir = os.path.expanduser('~')

# append path which contain pylibs to python path
git_dir = os.path.join(home_dir, 'git')
sys.path.append(git_dir)

from pylibs.utils import input_binary

ENABLE_STREAM_INLET_RECOVER = False
FILTER_ORDER = 2
FILTER_FREQ = [0.5, 8]
#MARKERS_TO_EPOCH = [1, 21]

#EPOCH_RANGE = [-0.2, 1.2]
EPOCH_T_MIN = -0.2
EPOCH_T_MAX = 1.2
#EPOCH_BASELINE = (-0.05, 0)
EPOCH_BASELINE = None

#EOG_CHANNELS = ['EOGvu']
#MISC_CHANNELS = ['x_EMGl', 'x_GSR', 'x_Respi', 'x_Pulse', 'x_Optic']

markers = dict()
markers['target'] = [111,112,113,114,115,116]
markers['non-target'] = [101,102,103,104,105,106]
markers['new-trial'] = [200,201,202,203,204,205]

MARKERS_TO_EPOCH = markers['target'] + markers['non-target']

def main():

    # ------------------------------------------------------------------------------------------------
    # find/connect eeg outlet

    try:
        print("looking for an EEG stream...")
        eeg_stream = resolve_stream('type', 'EEG')
        eeg_inlet = StreamInlet(eeg_stream[0], recover=ENABLE_STREAM_INLET_RECOVER)
        n_ch = eeg_stream[0].channel_count()
        n_ch = fmt_converter.n_ch_convert(n_ch)

        fs = eeg_stream[0].nominal_srate()
        info = eeg_inlet.info()
        ch_names = list()
        for m in range(n_ch):
            ch_names.append(info.desc().child("channels").child("channel").child_value("label"))
            
        #print(info.desc().child("channels").child("channel").child_value("label"))
        print(ch_names)
        sys.exit()
    except KeyboardInterrupt:
        raise ValueError("EEG stream could not found.")

    # ------------------------------------------------------------------------------------------------
    # find/connect marker outlet
    print("looking for a marker stream...")
    try:
        marker_stream = resolve_stream('type', 'Markers')
        if len(marker_stream) != 0:
            marker_inlet = StreamInlet(marker_stream[0], recover=ENABLE_STREAM_INLET_RECOVER)
    except KeyboardInterrupt:
        ans = input_binary("Marker Stream was not found, do you want to continue?")
        if ans == False:
            raise ValueError("EEG stream could not found.")

    epochs = container.Epochs(
                            n_ch,
                            fs,
                            MARKERS_TO_EPOCH,
                            EPOCH_T_MIN,
                            EPOCH_T_MAX,
                            EPOCH_BASELINE,
                            channel_names=None,
                            channel_types='eeg')

    acq = OnlineDataAcquire.OnlineDataAcquire(
                            epochs,
                            eeg_inlet,
                            n_ch,
                            fs,
                            marker_inlet,
                            FILTER_FREQ,
                            FILTER_ORDER,
                            fmt_converter.eeg_format_convert,
                            fmt_converter.marker_format_convert,
                            new_trial_markers=None,
                            end_markers=[255])
    acq.start()
    print("Acquisition Started")

    epochs_list = list()

    while True:
        try:
            new_trial_marker = self.acq.get_new_trial_marker()
            if new_trial_marker is not None:
                acq.clear_new_trial_marker()

            if epochs.has_new_data():
                epoch = epochs.get_new_data()
                #print(epoch)
                epochs_list.append(epoch)
        
            if acq.is_running is False:
                print("terminated")
                break
    
        except:
            acq.stop()
            print("Finished")
            break
    
    epochs_list = mne.concatenate_epochs(epochs_list)
    epochs_list.save(os.path.join(home_dir, "test-epo.fif"))

if __name__ == '__main__':
    main()