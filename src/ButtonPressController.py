import json

import utils
import HIDController

def interface(name, name_main_outlet='main', log_file=True, log_stdout=True):
    # ==============================================
    # This function is called from main module.
    # It opens LSL and communicate with main module.
    # ==============================================
    #
    # name : name of this module. main module will call this module with this name.
    #        This name will be given by main module.
    # name_main_outlet : name of main module's outlet. This module will find the main module with this name.
    #

    #status.value = 0
    #set_logger(file=log_file, stdout=log_stdout)
    params = dict() # variable for receive parameters
    hid_ctrl = HIDController.WiiController()

    inlet = utils.getIntermoduleCommunicationInlet(name_main_outlet)
    print('LSL connected, %s' %name)
    while True:
        data, _ = inlet.pull_sample(timeout=0.01)
        if data is not None:
            if data[0].lower() == name:
                if data[1].lower() == 'cmd':

                    # ------------------------------------
                    # command
                    if data[2].lower() == 'show_speaker':
                        pass
                    # modify here to add new commands
                    # ------------------------------------                        

                elif data[1].lower() == 'params':
                    # ------------------------------------
                    # parameters
                    params[data[2]] = json.loads(data[3])
                    logger.debug('Param Received : %s' %str(params[data[2]]))
                    # ------------------------------------
                else:
                    raise ValueError("Unknown LSL data type received.")
