# bme280.py - BME280 sensor library for Raspberry Pi Pico with MicroPython

import time
from machine import I2C

class BME280:
    def __init__(self, i2c, address=0x76):
        self.i2c = i2c
        self.address = address
        self.dig_T1 = 0
        self.dig_T2 = 0
        self.dig_T3 = 0
        self.dig_P1 = 0
        self.dig_P2 = 0
        self.dig_P3 = 0
        self.dig_P4 = 0
        self.dig_P5 = 0
        self.dig_P6 = 0
        self.dig_P7 = 0
        self.dig_P8 = 0
        self.dig_P9 = 0
        self.dig_H1 = 0
        self.dig_H2 = 0
        self.dig_H3 = 0
        self.dig_H4 = 0
        self.dig_H5 = 0
        self.dig_H6 = 0

    def _read_registers(self, start_addr, length):
        return self.i2c.readfrom_mem(self.address, start_addr, length)

    def _write_register_byte(self, reg_addr, data):
        self.i2c.writeto_mem(self.address, reg_addr, bytes([data]))

    def _read_calibration_data(self):
        cal_data = self._read_registers(0x88, 24)
        self.dig_T1 = int.from_bytes(cal_data[0:2], 'little')
        self.dig_T2 = int.from_bytes(cal_data[2:4], 'little', signed=True)
        self.dig_T3 = int.from_bytes(cal_data[4:6], 'little', signed=True)
        self.dig_P1 = int.from_bytes(cal_data[6:8], 'little')
        self.dig_P2 = int.from_bytes(cal_data[8:10], 'little', signed=True)
        self.dig_P3 = int.from_bytes(cal_data[10:12], 'little', signed=True)
        self.dig_P4 = int.from_bytes(cal_data[12:14], 'little', signed=True)
        self.dig_P5 = int.from_bytes(cal_data[14:16], 'little', signed=True)
        self.dig_P6 = int.from_bytes(cal_data[16:18], 'little', signed=True)
        self.dig_P7 = int.from_bytes(cal_data[18:20], 'little', signed=True)
        self.dig_P8 = int.from_bytes(cal_data[20:22], 'little', signed=True)
        self.dig_P9 = int.from_bytes(cal_data[22:24], 'little', signed=True)

        # Read humidity calibration data
        cal_data = self._read_registers(0xA1, 1)
        self.dig_H1 = int.from_bytes(cal_data, 'little')
        cal_data = self._read_registers(0xE1, 7)
        self.dig_H2 = int.from_bytes(cal_data[0:2], 'little', signed=True)
        self.dig_H3 = int.from_bytes([cal_data[2]], 'little')
        self.dig_H4 = (int.from_bytes([cal_data[3]], 'little') << 4) | (int.from_bytes([cal_data[4]], 'little') & 0xF)
        self.dig_H5 = (int.from_bytes([cal_data[5]], 'little') << 4) | ((int.from_bytes([cal_data[4]], 'little') >> 4) & 0xF)
        self.dig_H6 = int.from_bytes([cal_data[6]], 'little', signed=True)

    def _read_raw_data(self):
        data = self._read_registers(0xF7, 8)
        raw_pressure = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        raw_temperature = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        raw_humidity = (data[6] << 8) | data[7]
        return raw_pressure, raw_temperature, raw_humidity

    def _compensate_temperature(self, raw_temperature):
        var1 = ((((raw_temperature >> 3) - (self.dig_T1 << 1))) * self.dig_T2) >> 11
        var2 = (((((raw_temperature >> 4) - self.dig_T1) * ((raw_temperature >> 4) - self.dig_T1)) >> 12) * self.dig_T3) >> 14
        t_fine = var1 + var2
        temperature = ((t_fine * 5 + 128) >> 8) / 100.0
        return temperature

    def _compensate_pressure(self, raw_pressure, t_fine):
        var1 = t_fine - 128000
        var2 = var1 * var1 * self.dig_P6
        var2 = var2 + ((var1 * self.dig_P5) << 17)
        var2 = var2 + (self.dig_P4 << 35)
        var1 = ((var1 * var1 * self.dig_P3) >> 8) + ((var1 * self.dig_P2) << 12)
        var1 = (((1 << 47) + var1) * self.dig_P1) >> 33
        if var1 == 0:
            return 0
        pressure = 1048576 - raw_pressure
        pressure = (((pressure << 31) - var2) * 3125) // var1
        var1 = (self.dig_P9 * (pressure >> 13) * (pressure >> 13)) >> 25
        var2 = (self.dig_P8 * pressure) >> 19
        pressure = ((pressure + var1 + var2) >> 8) + (self.dig_P7 << 4)
        return pressure / 256.0

    def _compensate_humidity(self, raw_humidity, t_fine):
        var1 = t_fine - 76800
        var2 = (self.dig_H4 << 24) + (self.dig_H5 * var1) // 1024
        var3 = (var2 >> 12) & 0xFF
        var4 = ((var2 & 0xFF) << 12) | (raw_humidity & 0xFFF)
        var5 = ((self.dig_H6 * var1) // 1024) * ((var1 * self.dig_H3) // 2048)
        var6 = (var5 >> 11) + 0x8000
        var7 = ((var4 * var6) // 16384) + 0x4000
        var6 = ((var3 * var4) // 1024) * self.dig_H2
        var3 = (var6 >> 14) * (var6 >> 14)
        var4 = ((var7 * var3) // 2048) * self.dig_H1
        humidity = ((var7 + var4) >> 15) & 0xFF
        return min(100, max(0, humidity))

    def read(self):
        self._write_register_byte(0xF2, 0x01)  # Humidity oversampling x1
        self._write_register_byte(0xF4, 0x27)  # Pressure oversampling x1, Temperature oversampling x1, Normal mode
        self._write_register_byte(0xF5, 0xA0)  # Standby time 1000ms

        self._read_calibration_data()

        raw_pressure, raw_temperature, raw_humidity = self._read_raw_data()
        t_fine = self._compensate_temperature(raw_temperature)
        temperature = self._compensate_temperature(raw_temperature)
        pressure = self._compensate_pressure(raw_pressure, t_fine)
        humidity = self._compensate_humidity(raw_humidity, t_fine)

        return temperature, humidity, pressure
