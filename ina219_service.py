from ina219 import INA219
from service_utils import createService, SimpleService
from collections import namedtuple
import time

SHUNT_OHMS = 0.1
MAX_EXPECTED_AMPS = 2

PowerSample = namedtuple('PowerSample', ['power', 'timestamp'])


def toKWh(joules):
    return joules/3600/1000


class INA219Service(SimpleService):
    def __init__(self, conn, i2cBus, i2cAddr, serviceType):
        super().__init__(conn, i2cBus, i2cAddr, serviceType, 'INA219')

    def _configure_service(self):
        self.device = INA219(SHUNT_OHMS, busnum=self.i2cBus, address=self.i2cAddr, max_expected_amps=MAX_EXPECTED_AMPS)
        self.device.configure(voltage_range=INA219.RANGE_16V)
        self.device.sleep()
        self.service.add_path("/Dc/0/Voltage", None, gettextcallback=lambda path,value: "{:.2f}V".format(value))
        self.service.add_path("/Dc/0/Current", None, gettextcallback=lambda path,value: "{:.3f}A".format(value))
        self._configure_energy_history()
        self.service.add_path("/Alarms/LowVoltage", 0)
        self.service.add_path("/Alarms/HighVoltage", 0)
        self.service.add_path("/Alarms/LowTemperature", 0)
        self.service.add_path("/Alarms/HighTemperature", 0)
        self.add_settable_path("/CustomName", "", "", "")
        self.service.add_path("/Dc/0/Power", None, gettextcallback=lambda path,value: "{:.2f}W".format(value))
        self.lastPower = None

    def update(self):
        self.device.wake()
        self.service["/Dc/0/Voltage"] = round(self.device.voltage(), 3)
        self.service["/Dc/0/Current"] = round(self.device.current()/1000, 3)
        power = self.device.power()/1000
        now = time.perf_counter()
        self.service["/Dc/0/Power"] = round(power, 3)
        self.device.sleep()

        if self.lastPower is not None:
            # trapezium integration
            self._increment_energy_usage(round(toKWh((self.lastPower.power + power)/2 * (now - self.lastPower.timestamp)), 6))
        self.lastPower = PowerSample(power, now)


class INA219DCLoadService(INA219Service):
    def __init__(self, conn, i2cBus, i2cAddr):
        super().__init__(conn, i2cBus, i2cAddr, 'dcload')

    def _configure_energy_history(self):
        self.service.add_path('/History/EnergyIn', 0, gettextcallback=lambda path,value: "{:.6f}kWh".format(value))

    def _increment_energy_usage(self, change):
        self.service['/History/EnergyIn'] += change


class INA219DCSourceService(INA219Service):
    def __init__(self, conn, i2cBus, i2cAddr):
        super().__init__(conn, i2cBus, i2cAddr, 'dcsource')

    def _configure_energy_history(self):
        self.service.add_path('/History/EnergyOut', 0, gettextcallback=lambda path,value: "{:.6f}kWh".format(value))

    def _increment_energy_usage(self, change):
        self.service['/History/EnergyOut'] += change
