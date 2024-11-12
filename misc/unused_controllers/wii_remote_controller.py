import hid
import json

from multiprocessing import Process, Value

import src.process_management.intermodule_communication as intermodule_comm

class WiiController(object):
    # Get information of pressed button from wii controller
    # There are two version of Wii controller.
    # developed/tested on newer version (Wii Motion Plus Controller).
    # I believe it also works with previous version since only difference between
    # previous and newer version is about motion controller. newer version has nice motion sensor.
    # However in this script, only button feature is used.
    def __init__(self):
        self.device_name = 'RVL-CNT-01'

        self.vendor_id = None
        self.product_id = None

        self.event = 0

        self.p = None

        # Lab Streaming Layer
        self.LSL = False
        self.outlet = None


        self.button_previous = Value('i', 0)
        self.button = Value('i', 0)
        # mapping between each bit and button (from LSB)
        #
        #  0 : Arrow Left
        #  1 : Arrow Right
        #  2 : Arrow Down
        #  3 : Arrow Up
        #  4 : Plus
        #  5 : 2
        #  6 : 1
        #  7 : Trigger
        #  8 : A
        #  9 : Minus
        # 10 : N/A
        # 11 : N/A
        # 12 : Home

        self.difference = "0000000000"
        # format of difference
        # Each bit is corresponding to the mapping described above.
        # when nth bit is 1, corresponding button was pressed.
        # when nth bit is -1, corresponding button was released.
    
    def set_LSL(self, outlet, press = True, release = False):
        self.LSL = True
        self.outlet = True
        self.press = press
        self.release = release

    def start(self):
        self.p = Process(target=self.main)
        self.p.start()
    
    def stop(self):
        self.p.terminate()

    def get_difference(self):
        previous = self.dec2binstr(self.button_previous.value)
        current = self.dec2binstr(self.button.value)
        difference = ""
        for idx, c in enumerate(previous):
            difference += str(int(current[idx]) - int(c))
        self.difference = difference
        return difference

    def dec2binstr(self, dec):
        return '{:013b}'.format(dec)

    def show_available_devices(self):
        for device in hid.enumerate():
            print(device['product_string'])

    def sendLSL(self, val):
        
        print(str(val))

    def main(self):
        
        for device in hid.enumerate():
            if self.device_name in device['product_string']:
                self.vendor_id = device['vendor_id']
                self.product_id = device['product_id']
        HID = hid.device()
        HID.open(self.vendor_id, self.product_id)
        HID.set_nonblocking(True)
        print("Device was connected.")
        while True:
            report = HID.read(64)
            if report:
                button_bin_str = '{:08b}'.format(report[2]) + '{:05b}'.format(report[1])
                self.button.value = int(button_bin_str, 2)
                val = self.get_difference()
                if self.LSL:
                    self.sendLSL(val)
                self.button_previous.value = self.button.value

def start(params, outlet=None):
    print(params)
    if params['device'] == 'wii':
        wii = WiiController()
        if params['lsl'] == True:
            wii.set_LSL(outlet, press = params['lsl_press'], release = params['lsl_release'])
        wii.start()

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

    print(name)
    print(name_main_outlet)

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
                    if data[2].lower() == 'start':
                        print('start command received')
                        #logger.debug('Command Received : %s' %data[2].lower())
                        start(params)
                    elif data[2].lower() == 'set_lsl':
                        params['lsl'] = json.loads(data[3])
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