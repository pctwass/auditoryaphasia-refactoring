import json

import auditory_aphasia.process_management.intermodule_communication as intermodule_comm


def interface(name:str, state_dict:dict[str,any], name_main_outlet:str='main'):
    # ==============================================
    # This function is called from main module.
    # It opens LSL and communicate with main module.
    # ==============================================
    #
    # name : name of this module. main module will call this module with this name.
    #        This name will be given by main module.
    # name_main_outlet : name of main module's outlet. This module will find the main module with this name.
    #
    # state_dict : instance of multiprocessing.Manager.dict, shared with parent module.

    inlet = intermodule_comm.get_intermodule_communication_inlet(name_main_outlet)
    print('LSL connected, %s' %name)

    params = dict() # variable for receive parameters
    while True:
        data, _ = inlet.pull_sample(timeout=0.01)
        if data is not None:
            if data[0].lower() == name:
                if data[1].lower() == 'cmd':
                    # ------------------------------------
                    # command
                    # format of command
                    # data[1] -> 'cmd'
                    # data[2] -> 'name_of_command'
                    # data[3] -> 'parameter'
                    if data[2].lower() == 'name_of_command':
                        #logger.debug('Command Received : %s' %data[2].lower())
                        params['name_of_params'] = json.loads(data[3])
                    elif data[2].lower() == 'stop':
                        print("receive stop command")
                    # modify here to add new commands
                    # ------------------------------------                        

                elif data[1].lower() == 'params':
                    # ------------------------------------
                    # parameters
                    params[data[2]] = json.loads(data[3])
                    #logger.debug('Param Received : %s' %str(params[data[2]]))
                    # ------------------------------------
                else:
                    raise ValueError("Unknown LSL data type received.")