#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corp, copyright, all rights reserved, 2019

Notes:
1)
"""
import pyb
import machine
from upyb_INA220 import INA220
from time import sleep
from upyb_i2c import UPYB_I2C, UPYB_I2C_HW_I2C1

CHANNELS = ["V1", "V2", "V3"]
LDOS = [
    {"name": "V1", "control_addr": 0x18, },
    {"name": "V2", "control_addr": 0x19, },
]
LDOS_V3 = {"name": "V3", "control_addr": 0x1e, }

GPIO_COMMAND_INPUT = 0x00
GPIO_COMMAND_OUTPUT = 0x01
GPIO_COMMAND_POLARITY = 0x02
GPIO_COMMAND_CONFIG = 0x03

SAMPLES_1 = 8
SAMPLES_2 = 9
SAMPLES_4 = 10
SAMPLES_8 = 11
SAMPLES_16 = 12
SAMPLES_32 = 13

PG_GOOD = "PG_GOOD"
PG_BAD = "PG_BAD"
PG_UNSUPPORTED = "PG_UNSUPPORTED"


class SupplyStats(object):
    """

    This code uses the two INA220s on the board to make current and voltage
    measures on one of the supplies.

    """
    V1_RELAY_SHIFT = 0
    V2_RELAY_SHIFT = 2
    V3_RELAY_SHIFT = 4

    GPIO_CONFIG_ALL_INPUT = 0x3f   # has the effect of setting p0-p5 to high
    GPIO_LATCH_SET_MASK = 0X02     # b10
    GPIO_LATCH_RESET_MASK = 0x01   # b01
    GPIO_LATCH_CLEAR_MASK = 0x03   # b11

    GPIO_RELAY_ADDR = 30

    INA220_LOW_ADDR = 64
    INA220_HIGH_ADDR = 65

    INA220_RSENSE_0R6 = 0.6
    INA220_RSENSE_75 = 75
    samples = SAMPLES_1

    # etc... from your code...

    def __init__(self, i2c):

        self._i2c = i2c
        self.INA220_LOW = INA220(self._i2c, self.INA220_LOW_ADDR,  self.INA220_RSENSE_75, "LOW", self.samples)
        self.INA220_HIGH = INA220(self._i2c, self.INA220_HIGH_ADDR, self.INA220_RSENSE_0R6, "HIGH", self.samples)

        # set all outputs to low
        self._GPIO_write(GPIO_COMMAND_OUTPUT, 0x00)

        self.bypass()

    def _GPIO_write(self, command, value):
        bytes_write = [(command) & 0xFF, (value) & 0xFF]
        bytes_write = bytes(bytearray(bytes_write))
        # self._i2c.acquire()
        self._i2c.writeto(self.GPIO_RELAY_ADDR, bytes_write)
       #  self._i2c.release()

    def _GPIO_read(self, command):
        # self._i2c.acquire()
        self._i2c.writeto(self.GPIO_RELAY_ADDR, bytes(bytearray([command & 0xff])))
        read = self._i2c.readfrom(self.GPIO_RELAY_ADDR, 1)
        # self._i2c.release()
        # print("register: {}".format(read))
        return ord(read)

    def _set_ina_channel(self, channel):

        reg_cache = self._GPIO_read(GPIO_COMMAND_CONFIG)
        if channel == CHANNELS[0]:   # v1
            _reg_cache = reg_cache & ~(self.GPIO_LATCH_CLEAR_MASK << self.V1_RELAY_SHIFT)
            set_channel = self.GPIO_LATCH_SET_MASK << self.V1_RELAY_SHIFT

        elif channel == CHANNELS[1]:  # v2
            _reg_cache = reg_cache & ~(self.GPIO_LATCH_CLEAR_MASK << self.V2_RELAY_SHIFT)
            set_channel = self.GPIO_LATCH_SET_MASK << self.V2_RELAY_SHIFT

        elif channel == CHANNELS[2]:  # v3
            _reg_cache = reg_cache & ~(self.GPIO_LATCH_CLEAR_MASK << self.V3_RELAY_SHIFT)
            set_channel = self.GPIO_LATCH_SET_MASK << self.V3_RELAY_SHIFT

        else:
            print("_set_ina_channel: unknown supply channel")
            return False

        set_channel |= _reg_cache
        print("set_channel: {}".format(set_channel))
        self._GPIO_write(GPIO_COMMAND_CONFIG, set_channel)
        sleep(0.1)

        config_register_p67 = reg_cache & 0xc0
        config_reg = config_register_p67 | self.GPIO_CONFIG_ALL_INPUT
        print("_set_ina_channel: reseting back to all input {}".format(config_reg))
        self._GPIO_write(GPIO_COMMAND_CONFIG, config_reg)
        return True

    def bypass(self):
        """ Set the INA circuit bypassed

        :return: success
        """
        config_reg_cache = self._GPIO_read(GPIO_COMMAND_CONFIG)
        config_reg = self.GPIO_LATCH_RESET_MASK << self.V1_RELAY_SHIFT | \
                     self.GPIO_LATCH_RESET_MASK << self.V2_RELAY_SHIFT | \
                     self.GPIO_LATCH_RESET_MASK << self.V3_RELAY_SHIFT

        config_register_p67 = config_reg_cache & 0xc0
        config_reg |= config_register_p67
        print("config_reg RESET: {}".format(config_reg))

        self._GPIO_write(GPIO_COMMAND_CONFIG, config_reg)
        sleep(0.5)
        # config = self._GPIO_read(GPIO_COMMAND_CONFIG)
        # print("read_config: {}".format(config))
        config_reg = config_register_p67 | self.GPIO_CONFIG_ALL_INPUT
        print("config_reg INPUT: {}".format(config_reg))
        self._GPIO_write(GPIO_COMMAND_CONFIG, config_reg)
        return True, None

    def get_stats(self, ldo_obj):
        """

        :param name:
        :return: success, voltage, current
        """
        name = ldo_obj._name
        # switch the relays as required...

        # on error, return False, {}

        # make the measurements...
        voltage_mv = 1
        current_ua = 1
        pg = supply.power_good()
        return True, {"v_mv": voltage_mv, "c_ua": current_ua, "pg": pg}


class V3(object):
    """ V3 Class
    - V3 is not like the other LDOs, so need a different class to handle it
    - V3 only has enable

    """

    OUTPUT_VOLTAGE_MV = 12000
    FEEDBACK_RESISTANCE = 10000

    def __init__(self, i2c, addr, name="V3"):
        # disable on init
        pass

    def _state(self):
        # for debugging, print everything
        pass

    def enable(self, enable=True):
        # set the V3 enable pin via the I2C GPIO mux
        pass

    def get_feedback_resistance(self):
        """ return the feedback path resistance

        :return: success, ohms
        """
        # this will be a set value on the PCB
        return True, self.FEEDBACK_RESISTANCE

    def voltage_mv(self, voltage_mv):
        """ Set the LDO voltage

        :param voltage_mv:
        :return: success, voltage_mv
        """
        if voltage_mv == self.OUTPUT_VOLTAGE_MV:
            return True, voltage_mv
        return False, voltage_mv

    def power_good(self):
        """ Return the PG pin status

        :return: success, PG pin value (True = good)
        """
        return True, PG_UNSUPPORTED


class LDO(object):

    LDO_ENABLE_SHIFT = 6

    def __init__(self, i2c, addr, name):
        self._name = name
        self._i2c = i2c
        self._addr = addr
        self._voltage_mv = 0

        # set potenial outputs to their default state of all 0
        # LDO is conrolled by the GPIO expander
        self._GPIO_write(GPIO_COMMAND_OUTPUT, 0x00)

        # set polarity to its default value
        self._GPIO_write(GPIO_COMMAND_POLARITY, 0x70)

        # set all GPIO pins 0-5 and 7 to input, p6 must be set to an output
        # LDO is disable and set to lowest output value
        self._GPIO_write(GPIO_COMMAND_CONFIG, 0xb7)

    def _GPIO_write(self, command, value):
        # intakes the command bits and the value, creates one byte and writes to GPIO
        bytes_write = [(command) & 0xFF, (value) & 0xFF]
        bytes_write = bytes(bytearray(bytes_write))
        # self._i2c.acquire()
        self._i2c.writeto(self._addr, bytes_write)
        # self._i2c.release()

    def _GPIO_read(self, command):
        # intakes the command bits and reads that register on the GPIO
        # self._i2c.acquire()
        self._i2c.writeto(self._addr, bytes(bytearray([command & 0xff])))
        read = self._i2c.readfrom(self._addr, 1)
        # self._i2c.release()
        # print("register: {}".format(read))
        return ord(read)

    def _state(self):
        # for debugging, print everything
        pass

    def enable(self, enable=True):
        """ Enable/Disable the LDO

        :param enable: True/False
        :return: success, enable
        """
        # set the LDO control pins via the I2C GPIO mux
        # config pins 0-5 to be outputs
        _register = self._GPIO_read(GPIO_COMMAND_CONFIG)

        if enable:
            register = _register | (0x01 << self.LDO_ENABLE_SHIFT)

        else:
            register = _register & ~(0x01 << self.LDO_ENABLE_SHIFT)

        self._GPIO_write(GPIO_COMMAND_CONFIG, register)
        print("{} enable: register: {} -> {}".format(self._name, _register, register))
        return True, enable

    def get_feedback_resistance(self):
        """ return the feedback path resistance

        :return: success, ohms
        """
        # probably need to use the current voltage setting to compute resistance
        return True, 10000

    def voltage_mv(self, voltage_mv):
        """ Set the LDO voltage

        :param voltage_mv:
        :return: success, voltage_mv
        """

        # validate voltage_mv, check range, and divisible by 50 mV
        # set the LDO control pins via the I2C GPIO mux

        self._voltage = voltage_mv
        return True, voltage_mv

    def power_good(self):
        """ Return the PG pin status

        :return: success, PG pin value (True = good)
        """
        # check the pin via the I2C GPIO mux
        return True, PG_GOOD


class Supplies(object):

    def __init__(self, i2c):
        self.i2c = i2c
        self.ctx = {
            "supplies": {},  # supply objects, key'd on name
        }

        # init LDOs
        for ldo in LDOS:
            name = ldo["name"]
            i2c_addr = ldo["control_addr"]
            self.ctx["supplies"][name] = LDO(self.i2c, i2c_addr, name)

        # init special V3 case
        self.ctx["supplies"]["V3"] = V3(self.i2c, LDOS_V3["name"], LDOS_V3["control_addr"])

        self.stats = SupplyStats(self.i2c)

    def _get_supply_obj(self, name):
        return self.ctx["supplies"].get(name, None)

    def set_voltage_mv(self, name, voltage_mv):
        """ Set an LDO to a voltage

        :param name:
        :param voltage_mv:
        :return: success, voltage_mv
        """
        supply = self._get_supply_obj(name)
        if supply is None: return False, "unknown supply"

        return supply.voltage_mv(voltage_mv)

    def get_stats(self, name):
        """ Get data (voltage, current, PG, ...) for the supply

        :param name:
        :return: success, {"v_mv": <int>, "c_ua": <int>, ["pg": <bool>]}
        """
        supply = self._get_supply_obj(name)
        if supply is None: return False, {}

        return self.stats.get_stats(supply)

    def bypass_stats(self):
        """ Set the INA circuit to be bypassed

        :return: success, None
        """
        return self.stats.bypass()


# Test code
if True:

    i2c = machine.I2C("X", freq=400000)
    # i2c = UPYB_I2C()
    # i2c.init(UPYB_I2C_HW_I2C1)
    supplies = Supplies(i2c)
    supplies_stats = SupplyStats(i2c)
    supplies.ctx["supplies"]["V1"].enable()
    for i in range(4):
        supplies.ctx["supplies"]["V1"].enable()
        success, n = supplies.stats.INA220_LOW.read_bus_voltage()
        print(success, n)
        supplies.stats._set_ina_channel("V1")
        sleep(2)
        supplies.stats.bypass()
        supplies.ctx["supplies"]["V1"].enable(False)
        sleep(1)

if False :

    i2c = UPYB_I2C()
    success, message = i2c.init(UPYB_I2C_HW_I2C1)
    print(success, message)
    supplies = Supplies(i2c)
    supplies.ctx["supplies"]["V1"].enable()
    for i in range(100):
        supplies.stats._set_ina_channel("V1")
        sleep(2)
        supplies.stats.bypass()
        sleep(1)





