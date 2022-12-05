import bme280
from service_utils import createService, getSettingsPath
import dbus
from settingsdevice import SettingsDevice


class BME280Service():
    def __init__(self, conn, i2cBus):
        self.i2cBus = i2cBus
        self.i2cAddr = 0x76
        self.calibrationParams = bme280.load_calibration_params(self.i2cBus, self.i2cAddr)
        self.serviceType = "temperature"
        self.supportedSettings = {}
        self.settablePaths = {}
        self.service = createService(conn, self.serviceType, self.i2cBus.id, self.i2cAddr,
            __file__, "BME280")
        self.service.add_path("/Temperature", None)
        # default type is battery
        self.add_settable_path("/TemperatureType", 0, 0, 2)
        self.add_settable_path("/CustomName", "", "", "")
        self.service.add_path("/Pressure", None)
        self.service.add_path("/Humidity", None)
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
            getSettingsPath(self.serviceType, self.i2cBus.id, self.i2cAddr, subPath),
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

    def update(self):
        data = bme280.sample(self.i2cBus, self.i2cAddr, self.calibrationParams)
        self.service["/Temperature"] = data.temperature
        self.service["/Pressure"] = data.pressure
        self.service["/Humidity"] = data.humidity
