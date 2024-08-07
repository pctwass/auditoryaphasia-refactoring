import numpy

class Epoch():
    def __init__(self, n_ch, fs, markers_to_epoch, range_epoch, baseline=None):

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
        if baseline != None:
            self.length_baseline = numpy.floor(fs*(baseline[1]-baseline[0])).astype(numpy.int64)
        self.length_epoch = numpy.floor(fs*(range_epoch[1]-range_epoch[0])).astype(numpy.int64)
        self.data = numpy.empty((n_ch,self.length_epoch,0))
        self.new_data_idx = numpy.array([], dtype=numpy.int64)
        self.time = numpy.arange(range_epoch[0], range_epoch[1], 1/fs)

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
                required_idx = required_idx + self.length_epoch
                if len(self.__eeg.time)-1 > required_idx:
                    satisfied_markers = numpy.append(satisfied_markers, m)
            
            if satisfied_markers.size != 0:
                for idx_marker in satisfied_markers:
                    time_range = self.range_epoch + self.__marker.time[idx_marker]
                    idx_range = numpy.where(self.__eeg.time-time_range[0] > 0)
                    idx_range = idx_range[0][0]
                    idx_range = numpy.append(idx_range, idx_range+self.length_epoch)

                    data_tmp = self.__eeg.data[:, idx_range[0]:idx_range[1]]
                    
                    if self.baseline != None:
                        offset = (self.baseline[0] - self.range_epoch[0])*self.fs
                        idx_range_baseline = idx_range[0] + offset
                        idx_range_baseline = numpy.append(idx_range_baseline, idx_range_baseline+self.length_baseline)
                        idx_range_baseline = idx_range_baseline.astype(numpy.int64)
                        baseline = self.__eeg.data[:, idx_range_baseline[0]:idx_range_baseline[1]]
                        baseline = numpy.reshape(numpy.mean(baseline, axis=1), (self.n_ch, 1))
                        baseline = numpy.tile(baseline, data_tmp.shape[1])
                        data_tmp = data_tmp - baseline

                    data_tmp = numpy.reshape(data_tmp, (self.n_ch, self.length_epoch, 1))
                    self.data = numpy.append(self.data, data_tmp, axis=2)
                    self.epoched_marker[idx_marker] = 1
                    self.new_data_idx = numpy.append(self.new_data_idx, 1)

    def get_data(self, marker):
        idx = numpy.where(self.__marker.data[numpy.where(self.epoched_marker == 1)] == marker)
        idx = idx[0]

        data = self.data[:,:,idx]
        self.new_data_idx[idx] = 0

        return data
    
    def get_new_data(self, marker):
        idx_all = numpy.where(self.__marker.data[numpy.where(self.epoched_marker == 1)] == marker)
        idx_all = idx_all[0]

        idx = numpy.where(self.new_data_idx[idx_all] == 1)
        idx = idx_all[idx[0]]

        data = self.data[:,:,idx]
        self.new_data_idx[idx] = 0
        
        return data

    def get_time(self):
        return self.time