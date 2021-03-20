#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2021
Martin Guthrie

"""
import json
import threading
from simple_rpc import Interface

try:
    # run locally
    from stublogger import StubLogger
except:
    # run from prism
    from public.prism.drivers.iba01.stublogger import StubLogger


DRIVER_TYPE = "TEENSY4"


class Teensy4():
    """ teensy4 SimpleRPC based driver

    ... add notes as required...

    """

    GPIO_MODE_INPUT = "INPUT"
    GPIO_MODE_OUTPUT = "OUTPUT"
    GPIO_MODE_INPUT_PULLUP = "INPUT_PULLUP"
    GPIO_MODE_LIST = [GPIO_MODE_INPUT, GPIO_MODE_OUTPUT, GPIO_MODE_INPUT_PULLUP]

    def __init__(self, port, baudrate=9600, loggerIn=None):
        self.lock = threading.Lock()

        if loggerIn: self.logger = loggerIn
        else: self.logger = StubLogger()

        self.port = port
        self.rpc = None
        self.my_version = "0.1.0"


    def init(self):
        """ Init Teensy SimpleRPC connection
        :return: <True/False> whether Teensy SimpleRPC connection was created
        """
        self.logger.info("attempting to install Teensy on port {}".format(self.port))
        try:
            self.rpc = Interface(self.port)
        except Exception as e:
            self.logger.error(e)
            return False

        version_response = self.version()
        if not version_response["success"]:
            self.logger.error("Unable to get version")
            return False

        if self.my_version != version_response["result"]["version"]:
            self.logger.error("version does not match, {} {}".format(...))
            return False

        # finally, all is well
        self.logger.info("Installed Teensy on port {}".format(self.port))
        return True

    def close(self):
        """  Close connection
          
        :return:
        """
        self.logger.info("closing")
        self.rpc.close()
        return True

    # -------------------------------------------------------------------------------------------------
    # API (wrapper functions)
    # these are the important functions
    #
    # all functions return dict: { "success": <True/False>, "result": { key: value, ... }}

    def list(self):
        """ list
        :return: list of Teensy methods
        """
        return list(self.rpc.methods)

    def unique_id(self):
        """ unique id
        :return: success = True/False, method: unique_id, unique_id = MAC Address
        """
        answer = self.rpc.call_method('unique_id')
        return json.loads(answer)

    def slot(self):
        """ slot
        :return: success = True/False, method: slot, id = id
        """
        # TODO: implement arduino side
        answer = self.rpc.call_method('slot')
        return json.loads(answer)

    # def channel(self):
    #     c = {'method': 'slot', 'args': {}}
    #     # FIXME: put SimpleRPC call here, and return the result JSON
    #     return {"success": False, "result": {}}

    def version(self):
        """ Version
        :return: success = True/False, method = version, version = version#
        """
        answer = self.rpc.call_method('version')
        return json.loads(answer)

    def reset(self):
        """ reset
        :return: success = True/False, method = reset
        """
        answer = self.rpc.call_method('reset')
        return json.loads(answer)


    def led(self, set):
        """ LED on/off
        :param set: True/False
        :return: success = True/False, method = set_led, result = state = ON/OFF
        """
        answer = self.rpc.call_method('set_led', set)
        return json.loads(answer)

    # def led_toggle(self, led, on_ms=500, off_ms=500, once=False):
    #     """ toggle and LED ON and then OFF
    #     - this is a blocking command
    #
    #     :param led: # of LED, see self.LED_*
    #     :param on_ms: # of milliseconds to turn on LED
    #     :return:
    #     """
    #     c = {'method': 'led_toggle', 'args': {'led': led, 'on_ms': on_ms, 'off_ms': off_ms, 'once': once}}
    #     # FIXME: put SimpleRPC call here, and return the result JSON
    #     return {"success": False, "result": {}}

    # def jig_closed_detect(self):
    #     """ Read Jig Closed feature on teensy
    #
    #     :return: success, result
    #     """
    #     c = {'method': 'jig_closed_detect', 'args': {}}
    #     # FIXME: put SimpleRPC call here, and return the result JSON
    #     return {"success": False, "result": {}}

    def read_adc(self, pin_number, sample_num=1, sample_rate=1):
        """ Read an ADC pin
        - This is a BLOCKING function
        - result is raw ADC value, client needs to scale to VREF (3.3V)

        :param pin_number: (0 - 41)
        :param sample_num: Number of samples to average over
        :param sample_rate: Millisecond delay between samples
        :return: success = True/False, method = read_adc, result = reading = *
        """
        answer = self.rpc.call_method('read_adc', pin_number, sample_num, sample_rate)
        return json.loads(answer)

    def init_gpio(self, pin_number, mode):
        """ Init GPIO
        :param pin_number: (0 - 41)
        :param mode: Teensy4.MODE_*
        :return: success = True/False, method = init_gpio, result = init = Set pin (pin_number) to (mode)
        """
        if mode not in self.GPIO_MODE_LIST:
            err = "Invalid mode {} not in {}".format(mode, self.GPIO_MODE_LIST)
            self.logger.error(err)
            return {'success': False, 'value': {'err': err}}

        mode_b = mode.encode()
        answer = self.rpc.call_method('init_gpio', pin_number, mode_b)
        return json.loads(answer)

    def read_gpio(self, pin_number):
        """ Get GPIO
        :param pin_number: (0 - 41)
        :return: success = True/False, method = read_gpio, result = state = 1/0
        """
        answer = self.rpc.call_method('read_gpio', pin_number)
        return json.loads(answer)

    def write_gpio(self, pin_number, state):
        """ Set GPIO
        :param pin_number: (0 - 41)
        :param state: 1/0
        :return: success = True/False, method = write_gpio, result = state = 1/0
        """
        answer = self.rpc.call_method('write_gpio', pin_number, state)
        return json.loads(answer)

    # ---------------------------------------------------------------------------------------------
    # Prism Player functions
    #

    def jig_closed_detect(self):
        # TODO: add jig closed detect, see IBA01.py for example
        #       this method will be different than the others as Prism Player logic
        #       expects to see a simple True|False return, not a dict or success, etc...
        #       so do the usual rpc, but then validate and return the response
        #       make it so the GPIO used on the server can be easily changed, like its a define at the
        #       top of the server code.  This driver doesn't need to know the GPIO number.
        #       You might want code that if someone tried to init/set the same GPIO you
        #       throw an error... as if the GPIO is dedicated to jig closed, its not allowed to to anything else
        return False

    def show_pass_fail(self, p=False, f=False, other=False):
        """ Set pass/fail indicator

        :param p: <True|False>  set the Pass LED
        :param f: <True|False>  set the Fail LED
        :param o: <True|False>  "other" is set
        :return: None
        """
        # TODO: here again we take 2-3 GPIOs from Teensy and dedicate them to a visual
        #       (usually LED) indication of test result.
        #       see IBA01.py for example
        pass

    #
    # Prism Player functions
    # ---------------------------------------------------------------------------------------------


