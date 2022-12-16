from smbus2 import SMBus
import bme280
from service_utils import createService, SimpleService


class BME280Service(SimpleService):
    def _init_service(self, conn):
        with SMBus(self.i2cBus) as bus:
            self.calibrationParams = bme280.load_calibration_params(bus, self.i2cAddr)
        self.serviceType = "temperature"
        self.deviceName = "BME280"
        self.service = createService(conn, self.serviceType, self.i2cBus, self.i2cAddr,
            __file__, self.deviceName)
        self.service.add_path("/Temperature", None)
        # default type is battery
        self.add_settable_path("/TemperatureType", 0, 0, 2)
        self.add_settable_path("/CustomName", "", "", "")
        self.service.add_path("/Pressure", None)
        self.service.add_path("/Humidity", None)

    def update(self):
        with SMBus(self.i2cBus) as bus:
            data = bme280.sample(bus, self.i2cAddr, self.calibrationParams)
        self.service["/Temperature"] = round(data.temperature, 1)
        self.service["/Pressure"] = round(data.pressure, 1)
        self.service["/Humidity"] = round(data.humidity, 1)
