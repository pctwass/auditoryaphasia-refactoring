from libs import video
import time
import sys

time_sleep = 1

vi = video.VideoInterface(fullscreen_mode=False)
vi.show_screen()

# test speakers

vi.show_speakers()
time.sleep(time_sleep)
vi.highlight_speaker(4)
time.sleep(time_sleep)
vi.unhighlight_speaker()
time.sleep(time_sleep)
vi.hide_speaker()
time.sleep(time_sleep)

# test cross hair

vi.show_crosshair()
time.sleep(time_sleep)
vi.hide_crosshair()
time.sleep(time_sleep)

# test smiley
vi.show_smiley()
time.sleep(time_sleep)
vi.hide_smiley()
time.sleep(time_sleep)

# test eyes open close
vi.show_eyes_open_close("open")
time.sleep(time_sleep)
vi.hide_eyes_open_close("open")
time.sleep(time_sleep)

vi.show_eyes_open_close("close")
time.sleep(time_sleep)
vi.hide_eyes_open_close("close")
time.sleep(time_sleep)

# test dancing gif
vi.show_gif()

time.sleep(time_sleep)

vi.hide_screen()

