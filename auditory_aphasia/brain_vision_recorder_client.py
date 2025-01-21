import os
import subprocess

import auditory_aphasia.config.config as config
import auditory_aphasia.config.system_config as system_config


class BrainVisionRecorderClient():
    def __init__(self, logger, params : dict[str,any]):
        self.logger = logger
        self.initialize_recorder(params)


    def initialize_recorder(self, params):
        try:
            import win32com.client as win32
            self.logger.debug("win32com.client was imported")
        except:
            self.logger.debug("Error : loading package pywin32 was failed, try these commands 'python Scripts/pywin32_postinstall.py -install'")
            print("Error : loading package pywin32 was failed, try these commands 'python Scripts/pywin32_postinstall.py -install'")

        recorder = win32.gencache.EnsureDispatch('VisionRecorder.Application')
        recorder.Acquisition.StopRecording()
        recorder.Acquisition.StopViewing()

        if params['session_type'] == 'online':
            #recorder.CurrentWorkspace.Load(os.path.join(repository_dir_base,"workspace",'9ch_selftest.rwksp'))
            recorder.CurrentWorkspace.Load(os.path.join(system_config.repository_dir_base,"lsl", 'config', 'BrainVisionRecorder',config.recorder_config_offline))
            subprocess.Popen("%s -c %s" %(system_config.rda_lsl_dir, system_config.rda_lsl_config_dir))
        elif params['session_type'] == 'offline':
            #recorder.CurrentWorkspace.Load(os.path.join(repository_dir_base,"workspace",'9ch_selftest.rwksp'))
            recorder.CurrentWorkspace.Load(os.path.join(system_config.repository_dir_base, "lsl", 'config', 'BrainVisionRecorder', config.recorder_config_online))

        recorder.Acquisition.ViewData()

        self.recorder = recorder


    def start_recording(self, f_dir):
        if f_dir[-4:] != '.eeg':
            f_dir += '.eeg'
        self.recorder.Acquisition.ViewData()
        self.recorder.Acquisition.StartRecording(f_dir)


    def stop_recording(self):
        self.recorder.Acquisition.StopRecording()
        #self.recorder.Acquisition.StopViewing()