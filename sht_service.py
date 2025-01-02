from service_utils import SimpleI2CService
from sensirion_driver_adapters.i2c_adapter.i2c_channel import I2cChannel
from sensirion_driver_adapters.transfer import Transfer, execute_transfer
from sensirion_driver_adapters.rx_tx_data import TxData, RxData
from sensirion_i2c_driver import LinuxI2cTransceiver, I2cConnection, CrcCalculator
from sensirion_i2c_sht3x import Sht3xDevice
from sensirion_i2c_sht3x.commands import Repeatability

class SHT3xService(SimpleI2CService):
    def __init__(self, conn, i2cBus, i2cAddr):
        super().__init__(conn, i2cBus, i2cAddr, 'temperature', 'SHT3x')

    def _configure_service(self):
        with LinuxI2cTransceiver(f"/dev/i2c-{self.i2cBus}") as bus:
            channel = I2cChannel(I2cConnection(bus), slave_address=self.i2cAddr, crc=CrcCalculator(8, 0x31, 0xff, 0x0))
            serial_number = execute_transfer(channel, ReadSerialCommand())
        self.service.add_path("/Temperature", None)
        # default type is battery
        self.add_settable_path("/TemperatureType", 0, 0, 2)
        self.service.add_path("/Humidity", None)
        self.service.add_path("/Serial", serial_number)

    def update(self):
        with LinuxI2cTransceiver(f"/dev/i2c-{self.i2cBus}") as bus:
            channel = I2cChannel(I2cConnection(bus), slave_address=self.i2cAddr, crc=CrcCalculator(8, 0x31, 0xff, 0x0))
            device = Sht3xDevice(channel)
            result = device.measure_single_shot(Repeatability.HIGH, True)
        self.service["/Temperature"] = round(result[0].value, 1)
        self.service["/Humidity"] = round(result[1].value, 1)


class ReadSerialCommand(Transfer):
    CMD_ID = 0x3780

    def pack(self):
        return self.tx_data.pack([])

    tx = TxData(CMD_ID, '>H', device_busy_delay=0.01, slave_address=None, ignore_ack=False)
    rx = RxData('>2H')
