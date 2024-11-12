import traceback
import threading
import pylsl
import numpy as np

from scipy import signal
from pylsl.pylsl import LostError

from src.common.LSL_data_chunk import LSLDataStruct
from src.acquisition.epoch_container import EpochContainer
from logging import getLogger

logger = getLogger(__name__)


class OnlineDataAcquire(object):
    def __init__(
            self,
            epoch_container : EpochContainer,
            eeg_inlet : pylsl.StreamInlet,
            marker_inlet : pylsl.StreamInlet,
            channels_to_acquire : list[list[int]], # np.array[list[int]]
            n_eeg_channels : int,
            sample_freq_eeg : float,
            format_convert_eeg_func,
            format_convert_marker_func,
            filter_freq : float|None = None,
            filter_order : int|float|None = None,
            new_trial_markers : int|list[int]|None = None,
            end_markers : int|list[int]|None = None):

        self.epochs_container = epoch_container
        self.eeg_inlet = eeg_inlet
        self.n_eeg_channels = n_eeg_channels
        self.sample_freq_eeg = sample_freq_eeg
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
        if self.filter_freq is not None and self.filter_order is not None:
            sos = signal.butter(self.filter_order, np.array(self.filter_freq)/(self.sample_freq_eeg/2), 'bandpass', output='sos')
            z = np.zeros((self.filter_order, self.n_eeg_channels, 2))
            # Shape of initial Z should be (filter_order, number_of_eeg_channel, 2)
            # or
            # z = signal.sosfilt_zi(sos) # shape of the returned object will be (filter_order, 2)

        # ------------------------------------------------------------------------------------------------

        eeg = LSLDataStruct()
        eeg.data = np.empty((self.n_eeg_channels, 0))

        marker = LSLDataStruct()
        marker.data = np.empty((0), dtype=np.int64)

        #Epoch = data_structure.Epoch(n_ch, fs_eeg, MARKERS_TO_EPOCH, EPOCH_RANGE, EPOCH_BASELINE)
        # 'epochs' is passed from parent
        self.epochs_container.set(eeg, marker) # push by reference

        logger.info("start receiving data.")
        try:
            while self.is_running:
                try:
                    eeg.data_chunk, eeg.time_chunk = self.eeg_inlet.pull_chunk()
                    marker.data_chunk, marker.time_chunk = self.marker_inlet.pull_chunk()
                    eeg.time_correction = self.eeg_inlet.time_correction()
                    marker.time_correction = self.marker_inlet.time_correction()
                except Exception as e:
                    if type(e) == LostError:
                        logger.error("Error : \n%s" %(traceback.format_exc()))
                        break

                # if any eeg data was pulled from the outlet
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

                    self.epochs_container.update()

                    if self.got_end_marker:
                        if len(self.epochs_container.epoched_marker) == sum(self.epochs_container.epoched_marker):
                            self.is_running = False

                # if any markers were pulled from the outlet
                if marker.time_chunk:
                    for idx in range(len(marker.time_chunk)):
                        marker.time_chunk[idx] += marker.time_correction
                        
                    marker.data_chunk = self.format_convert_marker_func(marker.data_chunk)
                    marker.data = np.append(marker.data, marker.data_chunk)
                    marker.time = np.append(marker.time, marker.time_chunk)
                    logger.info(np.unique(marker.data_chunk))
                    
                    marker.time_chunk = list()
                    self.epochs_container.update()

                    self._check_for_and_set_new_trial_marker(marker)
                    self._check_for_and_flag_end_marker(marker)
        except:
            logger.error("Error : \n%s" %(traceback.format_exc()))

        logger.info("stop receiving data.")


    def get_marker_data(self):
        return self.marker

    def get_new_trial_marker(self) -> int | None:
        return self.new_trial_marker
    
    def clear_new_trial_marker(self):
        self.new_trial_marker = None


    # set the current new trial marker if there is a new trial marker in the marker data
    def _check_for_and_set_new_trial_marker(self, marker:LSLDataStruct):
        if self.new_trial_markers is not None:
                for new_trial_marker in  self.new_trial_markers:
                    if new_trial_marker in marker.data_chunk:
                        self.new_trial_marker = new_trial_marker

                        
    # flag if there is an end marker in the marker data
    def _check_for_and_flag_end_marker(self, marker:LSLDataStruct):
        if self.end_markers is not None:
            for end_marker in self.end_markers:
                if end_marker in marker.data_chunk:
                    self.got_end_marker = True
        