from smbus2 import SMBus
import bme280
from service_utils import TemperatureService


class BME280Service(TemperatureService):
    def __init__(self, conn, i2cBus, i2cAddr):
        super().__init__(conn, i2cBus, i2cAddr, 'temperature', 'BME280')

    def _configure_service(self):
        with SMBus(self.i2cBus) as bus:
            self.calibrationParams = bme280.load_calibration_params(bus, self.i2cAddr)
        super()._configure_service()
        self.service.add_path("/Pressure", None)
        self.service.add_path("/Humidity", None)

    def update(self):
        with SMBus(self.i2cBus) as bus:
            data = bme280.sample(bus, self.i2cAddr, self.calibrationParams)
        self._update(data.temperature, data.humidity, data.pressure)
