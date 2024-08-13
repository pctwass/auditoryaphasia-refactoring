import traceback
import numpy as np
#import mne
#mne.set_log_level(verbose=False)

import logging
logger = logging.getLogger(__name__)

class Epochs():
    def __init__(self, n_ch, fs, markers_to_epoch, tmin, tmax, baseline=None, ch_names=None, ch_types='eeg'):
        """
        Parameters
        ----------
        n_ch : number of EEG channels
        markers_to_epoch : markers to epoch e.g. [1,3,5]
        range : epoching range relative to marker onset e.g. [-0.1 1.0]
        baseline : NOT IMPLEMENTED!!!! range of baseline correction. if pass None, baseline correction will not be applied
        """
        self.n_ch = n_ch
        self.fs = fs
        self.markers_to_epoch = markers_to_epoch
        self.tmin = tmin
        self.tmax = tmax
        range_epoch = [tmin, tmax]
        self.range_epoch = range_epoch
        self.baseline = baseline
        self.data = None
        self.events = None
        self.ch_types = ch_types
        if ch_names == None:
            self.ch_names = list()
            for m in range(n_ch):
                self.ch_names.append("ch" + str(m+1))
        else:
            self.ch_names = ch_names
        #self.info = mne.create_info(self.ch_names, self.fs, ch_types=self.ch_types)

        self.length_epoch = np.floor(fs*(range_epoch[1]-range_epoch[0])).astype(np.int64)+1
        self.new_data = np.array([], dtype=np.int64)

    def set(self, eeg, marker):
        self.__eeg = eeg
        self.__marker = marker
        self.epoched_marker = np.zeros((len(marker.data)), dtype=np.int64)
        for idx, m in enumerate(marker.data):
            if m in self.markers_to_epoch is False:
                self.epoched_marker[idx] = 1
        
    def update(self):
        if len(self.__marker.data) > len(self.epoched_marker):
            n_ele = len(self.__marker.data)-len(self.epoched_marker)
            mrk_part = self.__marker.data[-1*n_ele:]
            epoched_mrk_part = np.zeros(n_ele).astype(np.int64)
            for idx, m in enumerate(mrk_part):
                if (m in self.markers_to_epoch) is False:
                    epoched_mrk_part[idx] = 1
            self.epoched_marker = np.append(self.epoched_marker, epoched_mrk_part).astype(np.int64)

        unepoched_markers = np.where(self.epoched_marker == 0)
        unepoched_markers = unepoched_markers[0]

        if unepoched_markers.size != 0:
            satisfied_markers = np.array([],dtype=np.int64)
            for m in unepoched_markers:
                if self.__marker.data[m] == 1:
                    pass
                required_idx = np.where((self.__eeg.time - (self.__marker.time[m]+self.range_epoch[0])) > 0)
                if len(required_idx[0]) != 0:
                    required_idx = required_idx[0][0]
                    required_idx = required_idx + self.length_epoch
                    if len(self.__eeg.time)-1 > required_idx:
                        satisfied_markers = np.append(satisfied_markers, m)
            
            if satisfied_markers.size != 0:
                data = np.empty((0, self.n_ch, self.length_epoch))
                events = np.empty((0,3), dtype=np.int64)
                new_data_tmp = np.array([], dtype=np.int64)
                for idx_marker in satisfied_markers:
                    time_range = self.range_epoch + self.__marker.time[idx_marker]
                    idx_range = np.where(self.__eeg.time-time_range[0] > 0)
                    idx_range = idx_range[0][0]
                    idx_range = np.append(idx_range, idx_range+self.length_epoch)

                    idx_onset = np.where(self.__eeg.time-self.__marker.time[idx_marker] > 0)
                    idx_onset = idx_onset[0][0]

                    data_tmp = self.__eeg.data[:, idx_range[0]:idx_range[1]]

                    data_tmp = np.reshape(data_tmp, (1, self.n_ch, self.length_epoch))
                    data = np.append(data, data_tmp, axis=0)
                    events = np.append(events, np.reshape([idx_onset, 0, self.__marker.data[idx_marker]], (1, 3)), axis=0)
                    self.epoched_marker[idx_marker] = 1
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

    def get_data(self):
        if self.data == None:
            return None
        else:
            self.new_data = np.zeros((len(self.new_data)), dtype=np.int64)
            return self.data
    
    def has_new_data(self):
        idx = np.where(self.new_data == 1)
        idx = idx[0]

        if idx.size == 0:
            return False
        else:
            return True
    
    def get_new_data(self):
        idx = np.where(self.new_data == 1)
        idx = idx[0]

        if idx.size == 0:
            return None
        else:
            #epochs_new = self.data.__getitem__(idx)
            logger.debug("get new data, data : %s" %(str(self.data.shape)))
            logger.debug("get new data, idx : %s" %str(idx))
            logger.debug("get new data, events : %s" %(str(self.events.shape)))
            epochs_new = self.data[idx,:,:]
            events = self.events[idx,2]
            #epochs_new = self.data[idx]
            self.new_data[idx] = 0
            return epochs_new, events