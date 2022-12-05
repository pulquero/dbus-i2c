from script_utils import VERSION
from vedbus import VeDbusService

BASE_DEVICE_INSTANCE_ID = 1000


def createService(conn, serviceType, i2cBusNum, i2cAddr, file, deviceName):
    service = VeDbusService(getServiceName(serviceType, i2cBusNum, i2cAddr), conn)
    service.add_mandatory_paths(file, VERSION, 'I2C',
            getDeviceInstance(i2cBusNum, i2cAddr), 0, deviceName, 0, 0, 1)
    return service


def getSettingsPath(serviceType, i2cBusNum, i2cAddr, subPath):
    return f"/Settings/{serviceType.capitalize()}/{getDeviceAddress(i2cBusNum, i2cAddr)}{subPath}"


def getServiceName(serviceType, i2cBusNum, i2cAddr):
    return f"com.victronenergy.{serviceType}.{getDeviceAddress(i2cBusNum, i2cAddr)}"


def getDeviceAddress(i2cBusNum, i2cAddr):
    return f"i2c_bus{i2cBusNum}_addr{i2cAddr}"


def getDeviceInstance(i2cBusNum, i2cAddr):
    return BASE_DEVICE_INSTANCE_ID + i2cBusNum * 128 + i2cAddr

