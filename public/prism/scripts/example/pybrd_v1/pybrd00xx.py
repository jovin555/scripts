#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2019
Martin Guthrie

"""
import logging
import time
from core.test_item import TestItem
from public.prism.api import ResultAPI
#import ampy.files as files  # see this for file stuff

# file and class name must match
class pybrd00xx(TestItem):

    DEMO_TIME_DELAY = 1.0
    DEMO_TIME_RND_ENABLE = 1

    def __init__(self, controller, chan, shared_state):
        super().__init__(controller, chan, shared_state)
        self.logger = logging.getLogger("SC.pybrd00xx.{}".format(self.chan))

        self.pyb = None
        self.pyb_port = None

    def PYBRD0xxSETUP(self):
        ctx = self.item_start()  # always first line of test

        # drivers are stored in the shared_state and are retrieved as,
        drivers = self.shared_state.get_drivers(self.chan, type="MicroPyBrd")
        if len(drivers) > 1:
            self.logger.error("Unexpected number of drivers: {}".format(drivers))
            self.log_bullet("Unexpected number of drivers")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return
        driver = drivers[0]

        self.logger.info("Found pybrd: {}".format(driver))
        self.pyb_port = driver["obj"]["port"]
        id = driver["obj"]["id"]

        if self.pyb_port is None:
            self.logger.error("Could not find pyboard driver")
            self.item_end(ResultAPI.RECORD_RESULT_FAIL)
            return

        # save the id of the pyboard for the record
        _, _, _bullet = ctx.record.measurement("pyboard_id", id, ResultAPI.UNIT_INT)
        self.log_bullet(_bullet)

        self.pyb = driver["obj"]["pyb"]

        self.item_end()  # always last line of test

    def PYBRD0xxTRDN(self):
        ctx = self.item_start()  # always first line of test
        self.pyb.close()
        self.item_end()  # always last line of test

    def PYBRD0010_LedToggle(self):
        """ In this test the user confirms if the LED under test blinked
        (this is also an example of one test item being run multiple times
        with different arguments)

        {"id": "PYBRD0010_LedToggle",     "enable": true, "lednum": 2, "ontime_ms": 300 },

        where,
           lednum: 1=red, 2=green, 3=yellow, 4=blue

        """
        ctx = self.item_start()  # always first line of test

        # 1=red, 2=green, 3=yellow, 4=blue
        LED_COLORS = ["Red", "Green", "Yellow", "Blue"]

        ontime_ms = ctx.item.get("ontime_ms", 300)
        lednum = ctx.item.get("lednum", 1)

        self.log_bullet("Watch which color Led blinks...")

        success, result = self.pyb.led_toggle(lednum, ontime_ms)
        if not success:
            self.logger.error(result)
            _result = ResultAPI.RECORD_RESULT_FAIL
            self.log_bullet("UNKNOWN PYBOARD ERROR")
            self.item_end(_result)  # always last line of test
            return

        buttons = ["{}".format(LED_COLORS[lednum-1]), "None", "Other"]
        user_select = self.input_button(buttons)

        if user_select["success"]:
            b_idx = user_select["button"]
            self.log_bullet("{} was pressed!".format(buttons[b_idx]))
            _, _result, _bullet = ctx.record.measurement("button", b_idx, ResultAPI.UNIT_INT, min=0, max=0)
            self.log_bullet(_bullet)

        else:
            _result = ResultAPI.RECORD_RESULT_FAIL
            self.log_bullet(user_select.get("err", "UNKNOWN ERROR"))

        # turn off blinky led
        self.pyb.led_toggle(lednum, 0)
        self.item_end(_result)  # always last line of test

    def PYBRD0020_adc_read(self):
        """ Read ADC channel.

        {"id": "PYBRD0020_adc_read",      "enable": true,  "pin": "TEMP", "samples": 2, "delay_s": 0, "name": "MyKnob",
                                          "min": 18, "max": 26, "gain": 1, "unit": "UNIT_CELCIUS" },

        background: https://github.com/micropython/micropython/pull/3656
        http://docs.micropython.org/en/v1.9.4/pyboard/library/pyb.ADC.html#pyb-adc
        https://forum.micropython.org/viewtopic.php?f=6&t=4540&hilit=%27module%27+object+has+no+attribute+%27ADC%27&start=10
        """
        ctx = self.item_start()  # always first line of test

        pin = ctx.item.get("pin", None)
        samples = ctx.item.get("samples", 1)
        unit = getattr(ResultAPI, ctx.item.get("unit", ResultAPI.UNIT_NONE), ResultAPI.UNIT_NONE)
        min = ctx.item.get("min", None)
        max = ctx.item.get("max", None)
        delay_ms = ctx.item.get("delay_s", 0)
        name = ctx.item.get("name", pin)  # if no name supplied use channel
        scale = ctx.item.get("scale", 1.0)

        success, result = self.pyb.adc_read(pin, samples, delay_ms) # adc_read(self, pin, samples=1, samples_ms=1):
        self.logger.info("{} {}".format(success, result))

        if not success:
            self.log_bullet("ADC pin {}: Failed".format(pin))
            self.item_end(ResultAPI.RECORD_RESULT_FAIL)  # always last line of test
            return

        self.log_bullet("ADC pin {}: {}".format(pin, result["value"]))

        _, _result, _bullet = ctx.record.measurement("{}".format(name), result["value"], unit, min, max)
        self.log_bullet(_bullet)

        self.item_end(_result)  # always last line of test

