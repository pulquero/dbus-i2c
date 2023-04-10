from smbus2 import SMBus
import bme280
from service_utils import SimpleI2CService


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
        self.add_settable_path("/TemperatureType", 0, 0, 2)
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
