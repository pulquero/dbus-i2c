from ina219 import INA219
from service_utils import SimpleI2CService
from collections import namedtuple
import time

SHUNT_OHMS = 0.1
MAX_EXPECTED_AMPS = 2

PowerSample = namedtuple('PowerSample', ['power', 'timestamp'])


def toKWh(joules):
    return joules/3600/1000


VOLTAGE_TEXT = lambda path,value: "{:.2f}V".format(value)
CURRENT_TEXT = lambda path,value: "{:.3f}A".format(value)
POWER_TEXT = lambda path,value: "{:.2f}W".format(value)
ENERGY_TEXT = lambda path,value: "{:.6f}kWh".format(value)


class INA219Service(SimpleI2CService):
    def __init__(self, conn, i2cBus, i2cAddr, serviceType, maxExpectedCurrent=MAX_EXPECTED_AMPS, shuntResistance=SHUNT_OHMS):
        super().__init__(conn, i2cBus, i2cAddr, serviceType, 'INA219', maxExpectedCurrent=maxExpectedCurrent, shuntResistance=shuntResistance)

    def _configure_service(self, maxExpectedCurrent, shuntResistance):
        self.device = INA219(shuntResistance, busnum=self.i2cBus, address=self.i2cAddr, max_expected_amps=maxExpectedCurrent)
        self.device.configure(voltage_range=INA219.RANGE_16V)
        self.device.sleep()
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

    def update(self):
        self.device.wake()
        voltage = round(self._voltage(), 3)
        current = round(self.device.current()/1000, 3)
        power = round(self.device.power()/1000, 3)
        now = time.perf_counter()
        self.device.sleep()

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


class INA219DCLoadService(INA219Service):
    def __init__(self, conn, i2cBus, i2cAddr, **kwargs):
        super().__init__(conn, i2cBus, i2cAddr, 'dcload', **kwargs)

    def _configure_energy_history(self):
        self.service.add_path('/History/EnergyIn', 0, gettextcallback=ENERGY_TEXT)

    def _voltage(self):
        return self.device.supply_voltage()

    def _increment_energy_usage(self, change):
        self._local_values['/History/EnergyIn'] += change


class INA219DCSourceService(INA219Service):
    def __init__(self, conn, i2cBus, i2cAddr, **kwargs):
        super().__init__(conn, i2cBus, i2cAddr, 'dcsource', **kwargs)

    def _configure_energy_history(self):
        self.service.add_path('/History/EnergyOut', 0, gettextcallback=ENERGY_TEXT)

    def _voltage(self):
        return self.device.voltage()

    def _increment_energy_usage(self, change):
        self._local_values['/History/EnergyOut'] += change
