import numpy
import mne
mne.set_log_level(verbose=False)

class Epoch():
    def __init__(self, n_ch, fs, markers_to_epoch, range_epoch, baseline=None, ch_names=None, ch_types='eeg'):

        """
        n_ch : number of EEG channels
        markers_to_epoch : markers to epoch e.g. [1,3,5]
        range : epoching range relative to marker onset e.g. [-0.1 1.0]
        baseline : range of baseline correction. if pass None, baseline correction will not be applied
        """
        self.n_ch = n_ch
        self.fs = fs
        self.markers_to_epoch = markers_to_epoch
        self.range_epoch = range_epoch
        self.baseline = baseline
        self.data = None
        self.ch_types = ch_types
        if ch_names == None:
            self.ch_names = list()
            for m in range(n_ch):
                self.ch_names.append("ch" + str(m+1))
        else:
            self.ch_names = ch_names
        self.info = mne.create_info(self.ch_names, self.fs, ch_types=self.ch_types)

        self.__length_epoch = numpy.floor(fs*(range_epoch[1]-range_epoch[0])).astype(numpy.int64)+1
        self.__new_data = numpy.array([], dtype=numpy.int64)

    def set(self, eeg, marker):
        self.__eeg = eeg
        self.__marker = marker
        self.epoched_marker = numpy.zeros((len(marker.data)), dtype=numpy.int64)

    def update(self):
        if len(self.__marker.data) > len(self.epoched_marker):
            self.epoched_marker = numpy.append(self.epoched_marker, numpy.zeros(len(self.__marker.data)-len(self.epoched_marker))).astype(numpy.int64)

        unepoched_markers = numpy.where(self.epoched_marker == 0)
        unepoched_markers = unepoched_markers[0]

        if unepoched_markers.size != 0:
            satisfied_markers = numpy.array([],dtype=numpy.int64)
            for m in unepoched_markers:
                required_idx = numpy.where((self.__eeg.time - (self.__marker.time[m]+self.range_epoch[0])) > 0)
                required_idx = required_idx[0][0]
                required_idx = required_idx + self.__length_epoch
                if len(self.__eeg.time)-1 > required_idx:
                    satisfied_markers = numpy.append(satisfied_markers, m)
            
            if satisfied_markers.size != 0:
                data = numpy.empty((0, self.n_ch, self.__length_epoch))
                events = numpy.empty((0,3), dtype=numpy.int64)
                for idx_marker in satisfied_markers:
                    time_range = self.range_epoch + self.__marker.time[idx_marker]
                    idx_range = numpy.where(self.__eeg.time-time_range[0] > 0)
                    idx_range = idx_range[0][0]
                    idx_range = numpy.append(idx_range, idx_range+self.__length_epoch)

                    idx_onset = numpy.where(self.__eeg.time-self.__marker.time[idx_marker] > 0)
                    idx_onset = idx_onset[0][0]

                    data_tmp = self.__eeg.data[:, idx_range[0]:idx_range[1]]

                    data_tmp = numpy.reshape(data_tmp, (1, self.n_ch, self.__length_epoch))
                    data = numpy.append(data, data_tmp, axis=0)
                    events = numpy.append(events, numpy.reshape([idx_onset, 0, self.__marker.data[idx_marker]], (1, 3)), axis=0)
                    self.epoched_marker[idx_marker] = 1
                    self.__new_data = numpy.append(self.__new_data, 1)

                data_tmp = mne.EpochsArray(data, self.info, events=events, tmin=self.range_epoch[0])
                if self.baseline != None:
                    data_tmp.apply_baseline(baseline = (self.baseline[0], self.baseline[1]))

                if self.data == None:
                    self.data = data_tmp
                else:
                    self.data = mne.concatenate_epochs([self.data, data_tmp], add_offset=False)

    def get_data(self):
        if self.data == None:
            return None
        else:
            self.__new_data = numpy.zeros((len(self.__new_data)), dtype=numpy.int64)
            return self.data
    
    def get_new_data(self):
        idx = numpy.where(self.__new_data == 1)
        idx = idx[0]

        if idx.size == 0:
            return None
        else:
            epochs_new = self.data.__getitem__(idx)
            self.__new_data[idx] = 0
            return epochs_new