from smbus2 import SMBus
import bme280
from service_utils import SimpleI2CService

BATTERY_TYPE_BATTERY = 0
BATTERY_TYPE_FRIDGE = 1
BATTERY_TYPE_GENERIC = 2
BATTERY_TYPE_ROOM = 3
BATTERY_TYPE_OUTDOOR = 4
BATTERY_TYPE_WATER_HEATER = 5
BATTERY_TYPE_FREEZER = 6


def _safe_min(newValue, currentValue):
    return min(newValue, currentValue) if currentValue else newValue


def _safe_max(newValue, currentValue):
    return max(newValue, currentValue) if currentValue else newValue


class BME280Service(SimpleI2CService):
    def __init__(self, conn, i2cBus, i2cAddr):
        super().__init__(conn, i2cBus, i2cAddr, 'temperature', 'BME280')

    def _configure_service(self):
        with SMBus(self.i2cBus) as bus:
            self.calibrationParams = bme280.load_calibration_params(bus, self.i2cAddr)
        self.service.add_path("/Temperature", None)
        # default type is battery
        self.add_settable_path("/TemperatureType", BATTERY_TYPE_BATTERY, 0, 6)
        self.service.add_path("/Pressure", None)
        self.service.add_path("/Humidity", None)
        self.service.add_path("/History/MinimumTemperature", None)
        self.service.add_path("/History/MaximumTemperature", None)

    def update(self):
        with SMBus(self.i2cBus) as bus:
            data = bme280.sample(bus, self.i2cAddr, self.calibrationParams)
        temp = round(data.temperature, 1)
        self.service["/Temperature"] = temp
        self.service["/Pressure"] = round(data.pressure, 1)
        self.service["/Humidity"] = round(data.humidity, 1)
        self.service["/History/MinimumTemperature"] = _safe_min(temp, self.service["/History/MinimumTemperature"])
        self.service["/History/MaximumTemperature"] = _safe_max(temp, self.service["/History/MaximumTemperature"])
