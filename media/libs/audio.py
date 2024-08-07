import pyaudio
import wave
import os.path
import numpy

DEFAULT_AUDIO_DEVICES = dict(name='default', number_of_channels=32)
#DEFAULT_AUDIO_DEVICES = dict(name=b'\x83X\x83s\x81[\x83J\x81[ (Dell USB Audio)', number_of_channels=2)
#DEFAULT_AUDIO_DEVICES = dict(name=b'Headphones (Simon\x81fs AirPods Pr', number_of_channels=2)
#FIREFACE_ASIO_DEVICE = dict(name='ASIO Fireface USB', number_of_channels=8)

DEFAULT_FRAME_RATE = 44100
DEFAULT_FRAMES_PER_BUFFER = 512
DEFAULT_VOLUME = 1.0

PATH_TO_AUDIO_FILES = os.path.join(os.getcwd(), "words_database")
print("Path to Audio Files : " + PATH_TO_AUDIO_FILES)


def get_available_devices():
    pya = pyaudio.PyAudio()
    hi = HardwareInformation(pya)
    devices = hi.devices
    for device in devices:
        print("name : " + str(devices[device]['name']) + ", maxOutputChannels : " + str(devices[device]['maxOutputChannels']))


class HardwareInformation(object):

    def __init__(self, pya):
        self.devices = dict()
        n_devs = pya.get_device_count()
        for idx in range(n_devs):
            device = pya.get_device_info_by_index(idx)
            name = device['name']
            if device['maxOutputChannels'] > 0 and name not in self.devices:
                self.devices[name] = device

    def get_output_device_with_name(self, device_name):
        return self.devices[device_name]


class AudioInterface(object):
    def __init__(self,
                 device_name=DEFAULT_AUDIO_DEVICES['name'],
                 volume=DEFAULT_VOLUME,
                 frame_rate=DEFAULT_FRAME_RATE,
                 frames_per_buffer=DEFAULT_FRAMES_PER_BUFFER,
                 use_headphones=False):
        self.device_name = device_name
        self.volume = volume
        self.frame_rate = frame_rate
        self.frames_per_buffer = frames_per_buffer
        self.use_headphones = use_headphones

        self.pya = pya = pyaudio.PyAudio()
        hardware_information = HardwareInformation(pya)

        available_devices = hardware_information.devices
        device = available_devices[device_name]
        self.device_idx = device['index']
        self.num_channels = device['maxOutputChannels']
        #self.num_channels = 3

        self.aligner = AlignMultiChAudioData(self.num_channels)


    def open(self):
        # self.stream = stream = self.pya.open(format=self.pya.get_format_from_width(self.sample_width),
        self.stream = stream = self.pya.open(format=pyaudio.paInt16,
                                             channels=self.num_channels,
                                             rate=self.frame_rate,
                                             output_device_index=self.device_idx,
                                             frames_per_buffer=self.frames_per_buffer,
                                             output=True)

    """
    def play_wav_speaker(self, filename):
        wf = wave.open(filename, 'rb')
        data = wf.readframes(self.frames_per_buffer)
        while len(data) > 0:
            self.stream.write(data)
            data = wf.readframes(self.frames_per_buffer)
    """

    def play_speaker(self, data, speaker_number):
        aligned_data = self.aligner.align(speaker_number, data)
        self.stream.write(aligned_data.tobytes())

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.pya.terminate()


class AlignMultiChAudioData(object):
    def __init__(self, n_ch):
        self.n_ch = n_ch

    def align(self, ch, data):
        aligned_data = numpy.zeros((data.size, self.n_ch))
        aligned_data[:, ch - 1] = data
        aligned_data = numpy.ravel(aligned_data, order='C').astype(numpy.int16)
        return aligned_data


class AudioCache(object):
    def __init__(self, path, volume=DEFAULT_VOLUME):

        self.volume = volume
        self.data = list()
        self.data.append(0)

        file_num = 1
        file_name = str(file_num) + '.wav'

        while os.path.isfile(os.path.join(path, file_name)):
            wf = wave.open(os.path.join(path, file_name), 'rb')

            print("loading : " + file_name)
            cnt = 0
            cnt_ = 0
            #data_int16 = numpy.array([])
            data_int16 = list()
            data = wf.readframes(1)
            while len(data) > 0:
                #data_int16 = numpy.append(data_int16, int.from_bytes(data, 'little', signed=True))
                data_int16.append(int.from_bytes(data, 'little', signed=True))
                data = wf.readframes(1)
                cnt += 1
                cnt_ += 1
                #print("#", end='')
                if cnt > 10000:
                    print("loading..." + str(cnt_))
                    cnt = 0
            data_int16 = numpy.array(data_int16)
            self.data.append(data_int16.astype(numpy.int16))
            print("finish loading : " + file_name)
            file_num += 1
            file_name = str(file_num) + '.wav'
