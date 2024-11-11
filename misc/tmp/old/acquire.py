from pylsl import StreamInlet, resolve_stream
import numpy
from scipy import signal
import data_structure
import src.config.system_config as system_config

ENABLE_STREAM_INLET_RECOVER = False
FILTER_ORDER = 2
FILTER_FREQ = [1, 40]
MARKERS_TO_EPOCH = [1, 3, 5]

EPOCH_RANGE = [-0.1, 0.5]
EPOCH_BASELINE = [-0.05, 0]

class StreamingSource:
    stream = None
    inlet = None

class Data:
    data = numpy.array([])
    time = numpy.array([])
    data_chunk = list()
    time_chunk = list()
    time_correction = list()

def main():
    formatting_client = system_config.FormattingClient()

    # ------------------------------------------------------------------------------------------------
    # find/connect eeg outlet

    eeg_stream = StreamingSource()
    print("looking for an EEG stream...")
    eeg_stream.stream = resolve_stream('type', 'EEG')
    eeg_stream.inlet = StreamInlet(eeg_stream.stream[0], recover=ENABLE_STREAM_INLET_RECOVER)
    n_ch = eeg_stream.stream[0].channel_count()
    n_ch = formatting_client.n_channels_convert(n_ch)

    fs_eeg = eeg_stream.stream[0].nominal_srate()


    # ------------------------------------------------------------------------------------------------
    # online filter
    sos = signal.butter(FILTER_ORDER, numpy.array(FILTER_FREQ)/(fs_eeg/2), 'bandpass', output='sos')
    z = numpy.zeros((FILTER_ORDER,n_ch, 2))
    # Shape of initial Z should be (filter_order, number_of_eeg_channel, 2)
    # or
    # z = signal.sosfilt_zi(sos) # shape of the return will be (filter_order, 2)

    # ------------------------------------------------------------------------------------------------
    # find/connect marker outlet

    marker_stream = StreamingSource()
    print("looking for a marker stream...")
    marker_stream.stream = resolve_stream('type', 'Markers')
    marker_stream.inlet = StreamInlet(marker_stream.stream[0], recover=ENABLE_STREAM_INLET_RECOVER)

    eeg = Data()
    eeg.data = numpy.empty((n_ch, 0))

    marker = Data()
    marker.data = numpy.empty((0), dtype=numpy.int64)

    Epoch = data_structure.Epoch(n_ch, fs_eeg, MARKERS_TO_EPOCH, EPOCH_RANGE, EPOCH_BASELINE)
    Epoch.set(eeg, marker) # push by reference

    print("start receiving data.")
    while True:
        try:
            eeg.data_chunk, eeg.time_chunk = eeg_stream.inlet.pull_chunk()
            marker.data_chunk, marker.time_chunk = marker_stream.inlet.pull_chunk()
            eeg.time_correction = eeg_stream.inlet.time_correction()
            marker.time_correction = marker_stream.inlet.time_correction()

        except Exception as e:
            print(e)
            break

        if eeg.time_chunk:                
            for idx in range(len(eeg.time_chunk)):
                eeg.time_chunk[idx] += eeg.time_correction
            eeg.data_chunk = formatting_client.eeg_format_convert(eeg.data_chunk)
            eeg.data_chunk, z = signal.sosfilt(sos, eeg.data_chunk, axis=1, zi=z)
            eeg.data = numpy.concatenate((eeg.data, eeg.data_chunk), axis=1)
            eeg.time = numpy.append(eeg.time, eeg.time_chunk)
            eeg.time_chunk = list()

            Epoch.update()

            test = Epoch.get_new_data()
            if test != None:
                print(test)

        if marker.time_chunk:
            for idx in range(len(marker.time_chunk)):
                marker.time_chunk[idx] += marker.time_correction     
            marker.data_chunk = formatting_client.marker_format_convert(marker.data_chunk)
            marker.data = numpy.append(marker.data, marker.data_chunk)
            marker.time = numpy.append(marker.time, marker.time_chunk)
            marker.time_chunk = list()
            Epoch.update()

    print(eeg.data.shape)
    print(eeg.time.shape)

    print(marker.data.shape)
    print(marker.time.shape)

    #numpy.save("eeg_data", eeg)
    #numpy.save("marker_data", marker)

if __name__ == '__main__':
    main()