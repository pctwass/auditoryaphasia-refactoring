import numpy as np
#import mne
#mne.set_log_level(verbose=False)

from common.LSL_data_chunk import LSLDataStruct

import logging
logger = logging.getLogger(__name__)

class EpochContainer():
    def __init__(
            self, 
            n_channels : int, 
            sample_freq : float, 
            markers_to_epoch : list[int], 
            tmin : float, 
            tmax : float, 
            baseline : float = None
        ):
        """
        Parameters
        ----------
        n_ch : number of EEG channels
        markers_to_epoch : markers to epoch e.g. [1,3,5]
        range_epoch : epoching range relative to marker onset e.g. [-0.1, 1.0]
        baseline : NOT IMPLEMENTED!!!! range of baseline correction. if pass None, baseline correction will not be applied
        """
        self.n_channels = n_channels
        self.sample_freq = sample_freq
        self.markers_to_epoch = markers_to_epoch
        self.tmin = tmin
        self.tmax = tmax
        self.epoch_range = [tmin, tmax]
        self.baseline = baseline
        
        self.data = None
        self.events = None
        self.new_data_start_index = 0
        self.new_data_available = False
        self.length_epoch_in_samples = np.floor(sample_freq*(self.epoch_range[1]-self.epoch_range[0])).astype(np.int64)+1
    

    def has_new_data(self) -> bool:
        return self.new_data_available
    

    def get_new_data(self) -> tuple[np.ndarray[float], np.ndarray[int]]:
        idx = np.where(self.new_data == 1)
        idx = idx[0]

        if self.new_data_available:
            #epochs_new = self.data.__getitem__(idx)
            logger.debug("get new data, data : %s" %(str(self.data.shape)))
            logger.debug("get new data, idx : %s" %str(idx))
            logger.debug("get new data, events : %s" %(str(self.events.shape)))

            epochs_new = self.data[self.new_data_start_index,:,:]
            events = self.events[self.new_data_start_index,2]

            self.new_data_start_index += len(epochs_new)
            self.new_data_available = False

            return epochs_new, events
        return None, None


    def set(self, eeg : LSLDataStruct, marker : LSLDataStruct):
        self.__eeg = eeg
        self.__marker = marker
        self.epoched_marker = np.zeros((len(marker.data)), dtype=np.int64)
        
        # skip markers that do not need to be epoched
        for idx, marker in enumerate(marker.data):
            if marker not in self.markers_to_epoch:
                self.epoched_marker[idx] = 1
        

    def update(self):
        if len(self.__marker.data) > len(self.epoched_marker):
            n_new_markers = len(self.__marker.data)-len(self.epoched_marker)
            new_markers_data = self.__marker.data[-1*n_new_markers:]
            markers_to_epoch = np.zeros(n_new_markers).astype(np.int64)

            # skip markers that do not need to be epoched
            for idx, unepoched_marker_idx in enumerate(new_markers_data):
                if unepoched_marker_idx not in self.markers_to_epoch:
                    markers_to_epoch[idx] = 1
            
            self.epoched_marker = np.append(self.epoched_marker, markers_to_epoch).astype(np.int64)

        # np.where returns a tuple of lists with one (list) element, [0] gets the list of indices
        unepoched_markers_indices = np.where(self.epoched_marker == 0)[0]

        if unepoched_markers_indices.size != 0:
            indices_matched_epoch_start_times = np.array([],dtype=np.int64)
            for unepoched_marker_idx in unepoched_markers_indices:
                if self.__marker.data[unepoched_marker_idx] == 1:
                    pass

                unepoched_marker_timestamp = self.__marker.time[unepoched_marker_idx]
                unepoched_marker_timestamp_eeg_onset_adjusted = unepoched_marker_timestamp + self.epoch_range[0] # (i.e. + self.tmin)
                
                # get indices of all eeg entries that are timestamped after the unepoched marker
                # NOTE '>' may need to be replaced with '>=', however, this likely doesn't matter in practice
                indices_eeg_time_range_after_marker = np.where((self.__eeg.time - unepoched_marker_timestamp_eeg_onset_adjusted) > 0)[0]

                if len(indices_eeg_time_range_after_marker) != 0:
                    idx_epoch_start_time = indices_eeg_time_range_after_marker[0]
                    idx_epoch_start_time = idx_epoch_start_time + self.length_epoch_in_samples # shift by one epoch?
                    
                    # check if the epoch completion time is a entry in the eeg timestamps
                    if len(self.__eeg.time)-1 > idx_epoch_start_time: 
                        indices_matched_epoch_start_times = np.append(indices_matched_epoch_start_times, idx_epoch_start_time)
            
            if indices_matched_epoch_start_times.size != 0:
                data = np.empty((0, self.n_channels, self.length_epoch_in_samples))
                events = np.empty((0,3), dtype=np.int64)
                new_data_tmp = np.array([], dtype=np.int64)
                
                for idx_epoch_start_time in indices_matched_epoch_start_times:
                    idx_range_epoch_markers = self.epoch_range + self.__marker.time[idx_epoch_start_time]
                    
                    indices_eeg_times_during_epoch = np.where(self.__eeg.time - idx_range_epoch_markers[0] > 0)[0]
                    idx_eeg_time_epoch_start = indices_eeg_times_during_epoch[0]
                    idx_eeg_time_epoch_end = idx_eeg_time_epoch_start + self.length_epoch_in_samples
                    idx_range_epoch = [idx_eeg_time_epoch_start, idx_eeg_time_epoch_end + self.length_epoch_in_samples]

                    marker_timestamp_epoch_start = self.__marker.time[idx_epoch_start_time]
                    indices_eeg_after_epoch_start_marker = np.where(self.__eeg.time - marker_timestamp_epoch_start > 0)[0]
                    idx_first_eeg_timestamp_after_marker = indices_eeg_after_epoch_start_marker[0]

                    data_tmp = self.__eeg.data[:, idx_range_epoch[0]:idx_range_epoch[1]]

                    data_tmp = np.reshape(data_tmp, (1, self.n_channels, self.length_epoch_in_samples))
                    data = np.append(data, data_tmp, axis=0)
                    events = np.append(events, np.reshape([idx_first_eeg_timestamp_after_marker, 0, self.__marker.data[idx_epoch_start_time]], (1, 3)), axis=0)
                    self.epoched_marker[idx_epoch_start_time] = 1
                    new_data_tmp= np.append(new_data_tmp, 1)

                #data_tmp = mne.EpochsArray(data, self.info, events=events, tmin=self.range_epoch[0])
                #if self.baseline != None:
                #    data_tmp.apply_baseline(baseline = (self.baseline[0], self.baseline[1]))

                if self.data is None:
                    self.data = data
                    self.events = events
                else:
                    #self.data = mne.concatenate_epochs([self.data, data_tmp], add_offset=False)
                    self.data = np.append(self.data, data, axis=0)
                    self.events = np.append(self.events, events, axis=0)

                self.new_data = np.append(self.new_data, new_data_tmp)
                self.new_data_available = True
    