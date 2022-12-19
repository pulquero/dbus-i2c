from service_utils import SimpleService
from sensirion_i2c_driver.linux_i2c_transceiver import LinuxI2cTransceiver
from sensirion_i2c_driver.connection import I2cConnection
from sensirion_i2c_sht.sht3x import Sht3xI2cDevice


class SHT3xService(SimpleService):
    def __init__(self, conn, i2cBus, i2cAddr):
        super().__init__(conn, i2cBus, i2cAddr, 'temperature', 'SHT3x')

    def _configure_service(self):
        with LinuxI2cTransceiver(f"/dev/i2c-{self.i2cBus}") as bus:
            device = Sht3xI2cDevice(I2cConnection(bus), self.i2cAddr)
            serial_number = device.read_serial_number()
        self.service.add_path("/Temperature", None)
        # default type is battery
        self.add_settable_path("/TemperatureType", 0, 0, 2)
        self.add_settable_path("/CustomName", "", "", "")
        self.service.add_path("/Humidity", None)
        self.service.add_path("/Serial", serial_number)

    def update(self):
        with LinuxI2cTransceiver(f"/dev/i2c-{self.i2cBus}") as bus:
            device = Sht3xI2cDevice(I2cConnection(bus), self.i2cAddr)
            result = device.single_shot_measurement()
        self.service["/Temperature"] = round(result[0].degrees_celsius, 1)
        self.service["/Humidity"] = round(result[1].percent_rh, 1)
