from script_utils import VERSION
from vedbus import VeDbusService
from settingsdevice import SettingsDevice
from settableservice import SettableService
import logging

BASE_DEVICE_INSTANCE_ID = 1024
PRODUCT_ID = 0
FIRMWARE_VERSION = 0
HARDWARE_VERSION = 0
CONNECTED = 1


def createService(conn, serviceType, i2cBusNum, i2cAddr, file, deviceName):
    service = VeDbusService(getServiceName(serviceType, i2cBusNum, i2cAddr), conn)
    service.add_mandatory_paths(file, VERSION, 'I2C',
            getDeviceInstance(i2cBusNum, i2cAddr), PRODUCT_ID, deviceName, FIRMWARE_VERSION, HARDWARE_VERSION, CONNECTED)
    service.add_path("/I2C/Bus", i2cBusNum)
    service.add_path("/I2C/Address", "{:#04x}".format(i2cAddr))
    return service


def getServiceName(serviceType, i2cBusNum, i2cAddr):
    return f"com.victronenergy.{serviceType}.{getDeviceAddress(i2cBusNum, i2cAddr)}"


def getDeviceAddress(i2cBusNum, i2cAddr):
    return f"i2c_bus{i2cBusNum}_addr{i2cAddr}"


def getDeviceInstance(i2cBusNum, i2cAddr):
    return BASE_DEVICE_INSTANCE_ID + i2cBusNum * 128 + i2cAddr


class SimpleI2CService(SettableService):
    def __init__(self, conn, i2cBus, i2cAddr, serviceType, deviceName):
        super().__init__()
        self.logger = logging.getLogger(f"dbus-i2c.{i2cBus}.{i2cAddr:#04x}.{deviceName}")
        self.serviceType = serviceType
        self.i2cBus = i2cBus
        self.i2cAddr = i2cAddr
        self.deviceName = deviceName
        self.service = createService(conn, self.serviceType, self.i2cBus, self.i2cAddr,
            __file__, self.deviceName)
        self.add_settable_path("/CustomName", "", 0, 0)
        self._configure_service()
        self._init_settings(conn)

    def __str__(self):
        return "{}@{}/{:#04x}".format(self.deviceName, self.i2cBus, self.i2cAddr)
