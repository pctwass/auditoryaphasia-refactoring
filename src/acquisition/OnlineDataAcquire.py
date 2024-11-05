import sys
import traceback
import threading
from logging import getLogger
import numpy as np
from scipy import signal

logger = getLogger(__name__)

class DataStruct:
    data = np.array([])
    time = np.array([])
    data_chunk = list()
    time_chunk = list()
    time_correction = list()

class OnlineDataAcquire(object):

    def __init__(
            self,
            epochs,
            eeg_inlet,
            channels_to_acquire,
            nch_eeg=None,
            fs_eeg=None,
            marker_inlet=None,
            filter_freq=None,
            filter_order=None,
            format_convert_eeg_func=None,
            format_convert_marker_func=None,
            new_trial_markers=None,
            end_markers=None):

        self.epochs = epochs
        self.eeg_inlet = eeg_inlet
        self.nch_eeg = nch_eeg
        self.fs_eeg = fs_eeg
        self.marker_inlet = marker_inlet
        self.filter_freq = filter_freq
        self.filter_order = filter_order
        self.format_convert_eeg_func = format_convert_eeg_func
        self.format_convert_marker_func = format_convert_marker_func

        self.channels_to_acquire = channels_to_acquire
        if type(channels_to_acquire) == list:
            self.channels_to_acquire = np.array(self.channels_to_acquire)

        self.new_trial_markers = new_trial_markers
        if type(new_trial_markers) == int:
            self.new_trial_markers = list(self.new_trial_markers)

        self.end_markers = end_markers
        if type(self.end_markers) == int:
            self.end_markers = list(self.end_markers)

        self.is_running = False

        self.new_trial_marker = None
        self.got_end_marker = False

        logger.info("Online Data Aquire module was initialized.")

    def start(self):
        logger.info("Online Data Acquire module was started.")
        self.thread = threading.Thread(target=self.main_thread)
        self.is_running = True
        self.thread.start()

    def stop(self):
        logger.info("Online Data Acquire module was stopped.")
        self.is_running = False

    def main_thread(self):

        # ------------------------------------------------------------------------------------------------
        # online filter
        if self.filter_freq is not None:
            sos = signal.butter(self.filter_order, np.array(self.filter_freq)/(self.fs_eeg/2), 'bandpass', output='sos')
            z = np.zeros((self.filter_order, self.nch_eeg, 2))
            # Shape of initial Z should be (filter_order, number_of_eeg_channel, 2)
            # or
            # z = signal.sosfilt_zi(sos) # shape of the returned object will be (filter_order, 2)

        # ------------------------------------------------------------------------------------------------

        eeg = DataStruct()
        eeg.data = np.empty((self.nch_eeg, 0))

        marker = DataStruct()
        marker.data = np.empty((0), dtype=np.int64)

        #Epoch = data_structure.Epoch(n_ch, fs_eeg, MARKERS_TO_EPOCH, EPOCH_RANGE, EPOCH_BASELINE)
        # 'epochs' is passed from parent
        self.epochs.set(eeg, marker) # push by reference

        logger.info("start receiving data.")
        try:
            while self.is_running:
                try:
                    eeg.data_chunk, eeg.time_chunk = self.eeg_inlet.pull_chunk()
                    marker.data_chunk, marker.time_chunk = self.marker_inlet.pull_chunk()
                    eeg.time_correction = self.eeg_inlet.time_correction()
                    marker.time_correction = self.marker_inlet.time_correction()
                except Exception as e:
                    from pylsl.pylsl import LostError
                    if type(e) == LostError:
                        logger.error("Error : \n%s" %(traceback.format_exc()))
                        break

                if eeg.time_chunk:                
                    for idx in range(len(eeg.time_chunk)):
                        eeg.time_chunk[idx] += eeg.time_correction
                    eeg.data_chunk = np.array(eeg.data_chunk) # has shape of (n_samples, n_ch)
                    #eeg.data_chunk = np.transpose(eeg.data_chunk) # now it's shape of (n_ch, n_samples)
                    eeg.data_chunk = self.format_convert_eeg_func(eeg.data_chunk)
                    eeg.data_chunk = eeg.data_chunk[self.channels_to_acquire, :]
                    eeg.data_chunk, z = signal.sosfilt(sos, eeg.data_chunk, axis=1, zi=z)
                    eeg.data = np.concatenate((eeg.data, eeg.data_chunk), axis=1)
                    eeg.time = np.append(eeg.time, eeg.time_chunk)
                    eeg.time_chunk = list()
                    self.epochs.update()

                    if self.got_end_marker:
                        if len(self.epochs.epoched_marker) == sum(self.epochs.epoched_marker):
                            self.is_running = False

                if marker.time_chunk:
                    for idx in range(len(marker.time_chunk)):
                        marker.time_chunk[idx] += marker.time_correction
                    marker.data_chunk = self.format_convert_marker_func(marker.data_chunk)
                    logger.info(np.unique(marker.data_chunk))
                    marker.data = np.append(marker.data, marker.data_chunk)
                    marker.time = np.append(marker.time, marker.time_chunk)
                    marker.time_chunk = list()
                    self.epochs.update()
                    if self.new_trial_markers is not None:
                        for new_trial_marker in  self.new_trial_markers:
                            if new_trial_marker in marker.data_chunk:
                                self.new_trial_marker = new_trial_marker
                    if self.end_markers is not None:
                        for end_marker in self.end_markers:
                            if end_marker in marker.data_chunk:
                                self.got_end_marker = True
        except:
            logger.error("Error : \n%s" %(traceback.format_exc()))

        logger.info("stop receiving data.")

    def get_marker_data(self):
        return self.marker


    def get_new_trial_marker(self) -> int | None:
        return self.new_trial_marker
    
    def clear_new_trial_marker(self):
        self.new_trial_marker = None
        