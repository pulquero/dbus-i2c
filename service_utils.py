from script_utils import VERSION
from vedbus import VeDbusService
from settingsdevice import SettingsDevice
from settableservice import SettableService
from collections import namedtuple
import logging

BASE_DEVICE_INSTANCE_ID = 1024
PRODUCT_ID = 0
FIRMWARE_VERSION = 0
HARDWARE_VERSION = 0
CONNECTED = 1


PowerSample = namedtuple('PowerSample', ['power', 'timestamp'])


def toKWh(joules):
    return joules/3600/1000


VOLTAGE_TEXT = lambda path,value: "{:.2f}V".format(value)
CURRENT_TEXT = lambda path,value: "{:.3f}A".format(value)
POWER_TEXT = lambda path,value: "{:.2f}W".format(value)
ENERGY_TEXT = lambda path,value: "{:.6f}kWh".format(value)


def getServiceName(serviceType, i2cBusNum, i2cAddr):
    return f"com.victronenergy.{serviceType}.{getDeviceAddress(i2cBusNum, i2cAddr)}"


def getDeviceAddress(i2cBusNum, i2cAddr):
    return f"i2c_bus{i2cBusNum}_addr{i2cAddr}"


def getDeviceInstance(i2cBusNum, i2cAddr):
    return BASE_DEVICE_INSTANCE_ID + i2cBusNum * 128 + i2cAddr


class SimpleI2CService(SettableService):
    def __init__(self, conn, i2cBus, i2cAddr, serviceType, deviceName, **kwargs):
        super().__init__()
        self.logger = logging.getLogger(f"dbus-i2c.{i2cBus}.{i2cAddr:#04x}.{deviceName}")
        self.serviceType = serviceType
        self.i2cBus = i2cBus
        self.i2cAddr = i2cAddr
        self.deviceName = deviceName
        self.service = VeDbusService(getServiceName(serviceType, i2cBus, i2cAddr), conn, register=False)
        self.add_settable_path("/CustomName", "", 0, 0)
        self._configure_service(**kwargs)
        self._init_settings(conn)
        di = self.register_device_instance(serviceType, getDeviceAddress(i2cBus, i2cAddr), getDeviceInstance(i2cBus, i2cAddr))
        self.service.add_mandatory_paths(__file__, VERSION, 'I2C',
                di, PRODUCT_ID, deviceName, FIRMWARE_VERSION, HARDWARE_VERSION, CONNECTED)
        self.service.add_path("/I2C/Bus", i2cBus)
        self.service.add_path("/I2C/Address", "{:#04x}".format(i2cAddr))
        self.service.register()

    def __str__(self):
        return "{}@{}/{:#04x}".format(self.deviceName, self.i2cBus, self.i2cAddr)


class DCI2CService(SimpleI2CService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _configure_service(self):
        self.service.add_path("/Dc/0/Voltage", None, gettextcallback=VOLTAGE_TEXT)
        self.service.add_path("/Dc/0/Current", None, gettextcallback=CURRENT_TEXT)
        self._configure_energy_history()
        self.service.add_path("/Alarms/LowVoltage", 0)
        self.service.add_path("/Alarms/HighVoltage", 0)
        self.service.add_path("/Alarms/LowTemperature", 0)
        self.service.add_path("/Alarms/HighTemperature", 0)
        self.service.add_path("/Dc/0/Power", None, gettextcallback=POWER_TEXT)
        self.service.add_path("/History/MaximumVoltage", 0, gettextcallback=VOLTAGE_TEXT)
        self.service.add_path("/History/MaximumCurrent", 0, gettextcallback=CURRENT_TEXT)
        self.service.add_path("/History/MaximumPower", 0, gettextcallback=POWER_TEXT)
        self._local_values = {}
        for path, dbusobj in self.service._dbusobjects.items():
            if not dbusobj._writeable:
                self._local_values[path] = self.service[path]
        self.lastPower = None

    def _update(self, voltage, current, power, now):
        self._local_values["/Dc/0/Voltage"] = voltage
        self._local_values["/Dc/0/Current"] = current
        self._local_values["/Dc/0/Power"] = power
        self._local_values["/History/MaximumVoltage"] = max(voltage, self._local_values["/History/MaximumVoltage"])
        self._local_values["/History/MaximumCurrent"] = max(current, self._local_values["/History/MaximumCurrent"])
        self._local_values["/History/MaximumPower"] = max(power, self._local_values["/History/MaximumPower"])

        if self.lastPower is not None:
            # trapezium integration
            self._increment_energy_usage(toKWh((self.lastPower.power + power)/2 * (now - self.lastPower.timestamp)))
        self.lastPower = PowerSample(power, now)

    def publish(self):
        for k,v in self._local_values.items():
            self.service[k] = v


class DCLoadServiceMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _configure_energy_history(self):
        self.service.add_path('/History/EnergyIn', 0, gettextcallback=ENERGY_TEXT)

    def _increment_energy_usage(self, change):
        self._local_values['/History/EnergyIn'] += change


class DCSourceServiceMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _configure_energy_history(self):
        self.service.add_path('/History/EnergyOut', 0, gettextcallback=ENERGY_TEXT)

    def _increment_energy_usage(self, change):
        self._local_values['/History/EnergyOut'] += change
