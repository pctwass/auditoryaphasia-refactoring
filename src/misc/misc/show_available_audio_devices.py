import pyaudio
import pyscab

import sys

pya = pyaudio.PyAudio()
hi = pyscab.HardwareInformation(pya)
devices = hi.devices
for device in devices:
    print(devices[device])
    #print("name : '" + str(devices[device]['name']) + "', maxOutputChannels : " + str(devices[device]['maxOutputChannels']))