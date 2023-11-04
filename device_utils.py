import importlib
import inspect


def createDevice(conn, deviceConfig):
    deviceModule = importlib.import_module(deviceConfig.pop('module'))
    constructor = getattr(deviceModule, deviceConfig.pop('class'))
    i2cBus = deviceConfig.pop('bus')
    i2cAddr = deviceConfig.pop('address')
    updateInterval = deviceConfig.pop('updateInterval')
    if len(inspect.signature(constructor).parameters) > 3:
        device = constructor(conn, i2cBus, i2cAddr, **deviceConfig)
    else:
        device = constructor(conn, i2cBus, i2cAddr)
    return device
