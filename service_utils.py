from script_utils import VERSION
from vedbus import VeDbusService
from settingsdevice import SettingsDevice

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


def getSettingsPath(serviceType, i2cBusNum, i2cAddr, subPath):
    return f"/Settings/{serviceType.capitalize()}/{getDeviceAddress(i2cBusNum, i2cAddr)}{subPath}"


def getServiceName(serviceType, i2cBusNum, i2cAddr):
    return f"com.victronenergy.{serviceType}.{getDeviceAddress(i2cBusNum, i2cAddr)}"


def getDeviceAddress(i2cBusNum, i2cAddr):
    return f"i2c_bus{i2cBusNum}_addr{i2cAddr}"


def getDeviceInstance(i2cBusNum, i2cAddr):
    return BASE_DEVICE_INSTANCE_ID + i2cBusNum * 128 + i2cAddr


class SimpleService:
    def __init__(self, conn, i2cBus, i2cAddr):
        self.i2cBus = i2cBus
        self.i2cAddr = i2cAddr
        self.supportedSettings = {}
        self.settablePaths = {}
        self._init_service(conn)
        self.settings = SettingsDevice(conn, self.supportedSettings, self._setting_changed)
        self.initializingSettings = True
        for settingName in self.supportedSettings.keys():
            path = self.settablePaths[settingName]
            self.service[path] = self.settings[settingName]
        self.initializingSettings = False

    def add_settable_path(self, subPath, initialValue, minValue, maxValue):
        settingName = subPath[1:].lower()
        self.service.add_path(subPath, initialValue, writeable=True, onchangecallback=lambda path, newValue: self._value_changed(settingName, newValue))
        self.supportedSettings[settingName] = [
            getSettingsPath(self.serviceType, self.i2cBus, self.i2cAddr, subPath),
            initialValue,
            minValue,
            maxValue
        ]
        self.settablePaths[settingName] = subPath

    def _value_changed(self, settingName, newValue):
        # ignore events generated during initialization
        if not self.initializingSettings:
            # this should trigger a _setting_changed() call
            self.settings[settingName] = newValue

    def _setting_changed(self, settingName, oldValue, newValue):
        path = self.settablePaths[settingName]
        self.service[path] = newValue

    def __str__(self):
        return "{}@{}/{:#04x}".format(self.deviceName, self.i2cBus, self.i2cAddr)
