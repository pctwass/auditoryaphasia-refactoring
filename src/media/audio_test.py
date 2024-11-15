from psychopy.core import MonotonicClock
import pyaudio
from libs import audio
import numpy
import time
import sys

t = numpy.array([])
mc = MonotonicClock()

audio.get_available_devices()

ac = audio.AudioCache('./words_database')
aif = audio.AudioInterface()

aif.open()

print('device opened')

t = numpy.append(t, mc.getTime())
aif.play_speaker(ac.data[2], 1)
t = numpy.append(t, mc.getTime())

#time.sleep(1)

t = numpy.append(t, mc.getTime())
aif.play_speaker(ac.data[2], 2)
t = numpy.append(t, mc.getTime())

aif.close()

#print(t[1]-t[0])
#print(t[3]-t[2])
