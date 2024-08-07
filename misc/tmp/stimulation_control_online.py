import sys
import os
import datetime
import time
import numpy as np

import StimulationController_no_video as StimulationController
StimulationController.set_logger(file=True, stdout=True)

# parameters
subject_code = "VPsimon001"
play_oddball = False
language = "Dutch"

# create folder to save data
#date = datetime.date.today().strftime("%y_%m_%d")
date = "22_08_02"
f_save_base = "D:/home/bbci/data"
f_save = os.path.join(f_save_base, subject_code + "_" + date)
if not os.path.exists(f_save):
    os.makedirs(f_save)

# start brain vision recorder
import win32com.client as win32

Rec = win32.gencache.EnsureDispatch('VisionRecorder.Application')
Rec.Acquisition.StopRecording()
Rec.Acquisition.StopViewing()
Rec.CurrentWorkspace.Load(os.path.join('D:/',
                                       'Users',
                                       'auditoryAphasia_stereo',
                                       'auditoryAphasia_portable',
                                       'python_scripts',
                                       'workspaces',
                                       '9ch_selftest.rwksp'))
                                       #'32ch_eog_dcc.rwksp'))
Rec.Acquisition.ViewData()
#Rec.Acquisition.StartRecording(os.path.join(f_save,"test.eeg"))

# eyes open close
time_rec = 60 # sec
while True:
    eyes = input("Do you want to record eyes open closed? [y]/n : ")
    if eyes == "" or eyes.lower() == 'y':
        if not os.path.exists(os.path.join(f_save, "presession")):
            os.makedirs(os.path.join(f_save, "presession"))
        input("Press Any Key to Start Eyes Open Recording (%ds)" %time_rec)
        Rec.Acquisition.StartRecording(os.path.join(f_save, "presession", "eyes_open.eeg"))
        start = time.time()
        while time.time() - start < time_rec:
            time.sleep(0.1)
        #time.sleep(time_rec)
        Rec.Acquisition.StopRecording()
        input("Press Any Key to Start Eyes Close Recording (%ds)" %time_rec)
        Rec.Acquisition.StartRecording(os.path.join(f_save, "presession", "eyes_close.eeg"))
        start = time.time()
        while time.time() - start < time_rec:
            time.sleep(0.1)
        #time.sleep(time_rec)
        Rec.Acquisition.StopRecording()
        break
    elif eyes.lower() == 'n':
        break

# oddball
if play_oddball:
    Rec.Acquisition.StartRecording(os.path.join(f_save, "standard_Oddball.eeg"))
    StimulationController.play("oddball")
    time.sleep(3)
    Rec.Acquisition.StopRecording()
    Rec.Acquisition.StartRecording(os.path.join(f_save, "standard_Oddball2.eeg"))
    StimulationController.play("oddball")
    time.sleep(3)
    Rec.Acquisition.StopRecording()

# --condition_plan--
# row : block
# column : run
#
# 1 : 6D
# 2 : Stereo Amuse
# 3 : Stereo Amuse Pitch
# 4 : MONO
#
conditions_matrix = [[1,1,1,1],
                     [1,1,1,1],
                     [1,1,1,1],
                     [1,1,1,1]]
conditions_matrix = np.array(conditions_matrix)
condition_list = ["6D", "Stereo", "StereoPitch", "Mono"]

f_name_prefix = "auditoryAphasia_"

n_block = 4
n_run = 4

block_init = 1
run_init = 1

for block in np.arange(block_init, n_block+1):
    for run in np.arange(run_init, n_run+1):
        condition_num = conditions_matrix[block-1, run-1]
        condition = condition_list[condition_num-1]
        f_name = f_name_prefix + condition + "_short_250_Block" + str(block) + "_Run" + str(run) + ".eeg"
        print("Block : %d, Run : %d" %(block, run))
        print("The next run will be: %s" %condition)
        input("Pres Any Key to Start")
        Rec.Acquisition.StartRecording(os.path.join(f_save, f_name))
        StimulationController.play(condition)
        time.sleep(3)
        Rec.Acquisition.StopRecording()

while True:
    eyes = input("Do you want to record eyes open closed? [y]/n : ")
    if eyes == "" or eyes.lower() == 'y':
        if not os.path.exists(os.path.join(f_save, "postsession")):
            os.makedirs(os.path.join(f_save, "postsession"))
        input("Press Any Key to Start Eyes Open Recording (%ds)" %time_rec)
        Rec.Acquisition.StartRecording(os.path.join(f_save, "postsession", "eyes_open.eeg"))
        time.sleep(time_rec)
        Rec.Acquisition.StopRecording()
        input("Press Any Key to Start Eyes Close Recording (%ds)" %time_rec)
        Rec.Acquisition.StartRecording(os.path.join(f_save, "postsession", "eyes_close.eeg"))
        time.sleep(time_rec)
        Rec.Acquisition.StopRecording()
        break
    elif eyes.lower() == 'n':
        break