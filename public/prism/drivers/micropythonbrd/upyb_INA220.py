#! /usr/bin/env python
# -*- coding: utf-8 -*-

import upyb_i2c
import machine
from time import sleep
DEBUG = False

class INA220(object):

    # self.INA220_LOW = INA220(self.i2c, self.INA220_LOW_ADDR, self.INA220_RSENSE_75, "LOW", self.samples)
    INA220_CONFIG_RESET_VALUE = 0x399F
    INA220_SHUNT_CONVERSION_FACTOR = 0.000010

    def __init__(self, i2c, i2c_addr, rsense, name, samples):
        self.pin = machine.Pin("X3", machine.Pin.OUT)
        self.pin.value(0)

        self.INA220_ADDRESS = i2c_addr
        self.rsense = rsense
        self.name = name
        self.SAMPLES = samples

        self.INA220_I2C = i2c   # i2c should be at a higher level

        self.INA220_CONFIG = 0x00
        self.INA220_SV = 0x01
        self.INA220_BV = 0x02
        self.INA220_PW = 0x03
        self.INA220_CU = 0x04
        self.INA220_CAL = 0x05

        # config register configurations
        self.INA220_CONFIG_RESET = (0x8000)  # Reset Bit

        self.INA220_CONVERSON_READY = (0X0002)  # Checking the CNVR bit
        self.INA220_CONFIG_BVOLTAGERANGE_MASK = (0x2000)  # Bus Voltage Range Mask
        self.INA220_CONFIG_BVOLTAGERANGE_16V = (0x0000)  # 0-16V Range
        self.INA220_CONFIG_BVOLTAGERANGE_32V = (0x2000)  # 0-32V Range
        self.INA220_VBUS_CONVERSION_FACTOR = (0.004)  # LSB = 4mV

        self.INA220_CONFIG_GAIN_MASK = (0x1800)  # Gain Mask
        self.INA220_CONFIG_GAIN_1_40MV = (0x0000)  # Gain 1, 40mV Range
        self.INA220_CONFIG_GAIN_2_80MV = (0x0800)  # Gain 2, 80mV Range
        self.INA220_CONFIG_GAIN_4_160MV = (0x1000)  # Gain 4, 160mV Range
        self.INA220_CONFIG_GAIN_8_320MV = (0x1800)  # Gain 8, 320mV Range

        self.INA220_CONFIG_BADCRES_MASK = (0x0780)  # Bus ADC Resolution Mask
        self.INA220_CONFIG_BADCRES_9BIT = (0x0080)  # 9-bit bus res = 0..511
        self.INA220_CONFIG_BADCRES_10BIT = (0x0100)  # 10-bit bus res = 0..1023
        self.INA220_CONFIG_BADCRES_11BIT = (0x0200)  # 11-bit bus res = 0..2047
        self.INA220_CONFIG_BADCRES_12BIT = (0x0400)  # 12-bit bus res = 0..4097

        self.INA220_CONFIG_SADCRES_MASK = (0x0078)  # Shunt ADC Resolution and Averaging Mask
        self.INA220_CONFIG_SADCRES_9BIT_1S_84US = (0x0000)  # 1 x 9-bit shunt sample
        self.INA220_CONFIG_SADCRES_10BIT_1S_148US = (0x0008)  # 1 x 10-bit shunt sample
        self.INA220_CONFIG_SADCRES_11BIT_1S_276US = (0x0010)  # 1 x 11-bit shunt sample
        self.INA220_CONFIG_SADCRES_12BIT_1S_532US = (0x0018)  # 1 x 12-bit shunt sample
        self.INA220_CONFIG_SADCRES_12BIT_2S_1060US = (0x0048)  # 2 x 12-bit shunt samples averaged together
        self.INA220_CONFIG_SADCRES_12BIT_4S_2130US = (0x0050)  # 4 x 12-bit shunt samples averaged together
        self.INA220_CONFIG_SADCRES_12BIT_8S_4260US = (0x0058)  # 8 x 12-bit shunt samples averaged together
        self.INA220_CONFIG_SADCRES_12BIT_16S_8510US = (0x0060)  # 16 x 12-bit shunt samples averaged together
        self.INA220_CONFIG_SADCRES_12BIT_32S_17MS = (0x0068)  # 32 x 12-bit shunt samples averaged together
        self.INA220_CONFIG_SADCRES_12BIT_64S_34MS = (0x0070)  # 64 x 12-bit shunt samples averaged together
        self.INA220_CONFIG_SADCRES_12BIT_128S_69MS = (0x0078)  # 128 x 12-bit shunt samples averaged together

        self.INA220_CONFIG_MODE_MASK = (0x0007)  # Operating Mode Mask
        self.INA220_CONFIG_MODE_POWERDOWN = (0x0000)
        self.INA220_CONFIG_MODE_SVOLT_TRIGGERED = (0x0001)
        self.INA220_CONFIG_MODE_BVOLT_TRIGGERED = (0x0002)
        self.INA220_CONFIG_MODE_SANDBVOLT_TRIGGERED = (0x0003)
        self.INA220_CONFIG_MODE_ADCOFF = (0x0004)
        self.INA220_CONFIG_MODE_SVOLT_CONTINUOUS = (0x0005)
        self.INA220_CONFIG_MODE_BVOLT_CONTINUOUS = (0x0006)
        self.INA220_CONFIG_MODE_SANDBVOLT_CONTINUOUS = (0x0007)

        self.INA220_SVOLT_SIGN = 0x8000  # bit that determines if vshunt is negative or positive
        self.INA220_SVOLT_SIGN_2BYTES = 0xFFFF

        # the config register is made up of 5 categories to select the correct mode for the INA220
        # modes: vbus range (BRNG), vshunt range and gain (PG), bus ADC (BAD), Shunt ADC (SAD), operating mode (MODE)
        self.config_register = self.INA220_CONFIG_MODE_SANDBVOLT_CONTINUOUS | \
                               (samples << 3) | \
                               self.INA220_CONFIG_BADCRES_12BIT | \
                               self.INA220_CONFIG_GAIN_8_320MV | \
                               self.INA220_CONFIG_BVOLTAGERANGE_32V

        self.reset()
        self.set_config(self.config_register)
        config_value = self.read_config()
        self.config_explain(config_value)

    def set_config(self, val):
        self.write_word(self.INA220_CONFIG, val)
        config_mode = self.read_config()
        if config_mode == self.config_register:
            if DEBUG: print("{}: Successfully Configured".format(self.name))
            return True

        if DEBUG: print("set_config: error failed to set correct config: {}".format(config_mode))
        return False

    def write_word(self, reg_addr, val):

        """ write data to INA220

        example usage: self.write_word(self.INA220_CONFIG, bytearray(b'\xB9\x9F'))

        :param reg_addr:
        :param data:
        :return: success (True/False)
        """
        n = [(val >> 8) & 0xFF, (val) & 0xFF]
        bytes_sent = self.INA220_I2C.writeto_mem(self.INA220_ADDRESS, reg_addr, bytes(bytearray(n)))

        return True
        # TODO: use write that returns the num of bytes sent
        # if bytes_sent == len(data):
        #   return True
        # print("write_word: Error sending data. bytes sent:{}".format(bytes_sent))
        # return False

    def read_config(self):
        return self.read_word(self.INA220_CONFIG)

    def read_word(self, reg_addr):
        value = self.INA220_I2C.readfrom_mem(self.INA220_ADDRESS, reg_addr, 2)
        output = value[0] << 8 | value[1]
        return output

    def config_explain(self, read_config):
        # print("read_config: {:04X}".format(read_config))
        mode = read_config & self.INA220_CONFIG_MODE_MASK
        if mode == self.INA220_CONFIG_MODE_SANDBVOLT_CONTINUOUS:
            if DEBUG: print("{}: Set to continuous mode shunt and voltage mode".format(self.name))
        elif mode == self.INA220_CONFIG_MODE_SANDBVOLT_TRIGGERED:
            if DEBUG: print("{}: Set to triggered shunt and voltage mode".format(self.name))
        elif mode == self.INA220_CONFIG_MODE_SVOLT_TRIGGERED:
            if DEBUG: print("{}: Set to triggered shunt voltage mode".format(self.name))
        else:
            if DEBUG: print("{}: unknown mode: {}".format(self.name, mode))

    def reset(self):
        success = self.write_word(self.INA220_CONFIG, 0xB99F)
        val = None
        if success:
            val = self.read_config()
            if val == self.INA220_CONFIG_RESET_VALUE:
                return True
        if DEBUG: print("reset: error failed to reset: {}".format(val))
        return False

    def read_bus_voltage(self):
        """

        :return: success, vbus_value
        """
        self._trigger()
        success, val = self._conversion_ready()
        if success:
            return success, val
        return False, 0

    def _trigger(self):
        self.write_word(self.INA220_CONFIG, self.config_register)
        # self.write_word(self.INA220_CONFIG, 0x399f)
        # print("MODE: {:08x}".format(self.read_config()))

    def _conversion_ready(self):
        for count in range(10):
            sleep(0.1)
            vbus_reg = self.read_word(self.INA220_BV)
            if vbus_reg & 0x2:
                volt = (vbus_reg >> 3) * self.INA220_VBUS_CONVERSION_FACTOR
            return True, volt
        if DEBUG: print("_conversion_ready: exceeded retry count")
        return False, 0

    def read_shunt_voltage(self):
        self._trigger()
        success, _ = self._conversion_ready()
        if success:
            self.pin.value(1)
            _vshunt = self.read_word(self.INA220_SV)
            self.pin.value(0)
            # print("_vshunt:{:04x}".format(_vshunt))
            vshunt = (_vshunt & 0x7FFF)
            if DEBUG: print("vshunt before equation, no sign bit:{}".format(vshunt))
            if _vshunt & self.INA220_SVOLT_SIGN:
                # print("hello")
                vshunt = (self.INA220_SVOLT_SIGN_2BYTES - _vshunt) + 1
                if DEBUG: print("{}: vshunt after equation: {}".format(self.name, vshunt))

            vshunt = (vshunt * self.INA220_SHUNT_CONVERSION_FACTOR)
            # print("read_shunt_voltage: MODE: {:08x}".format(self.read_config()))
            if DEBUG: print("{} : the shunt voltage:{:10.6f}".format(self.name, vshunt))
            return True, vshunt

        return False, 0

    def measure_current(self):
        success, voltage = self.read_shunt_voltage()
        current = (voltage / self.rsense)
        # print("measure_current: MODE: {:08x}".format(self.read_config()))
        if DEBUG: print("{} : the current:{:10.6f}".format(self.name, current))
        return success, current
