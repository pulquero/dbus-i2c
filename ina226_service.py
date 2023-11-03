import logging
from ina226 import INA226
from service_utils import SimpleI2CService
from collections import namedtuple
import time

PowerSample = namedtuple('PowerSample', ['power', 'timestamp'])


def toKWh(joules):
    return joules/3600/1000


VOLTAGE_TEXT = lambda path,value: "{:.2f}V".format(value)
CURRENT_TEXT = lambda path,value: "{:.3f}A".format(value)
POWER_TEXT = lambda path,value: "{:.2f}W".format(value)
ENERGY_TEXT = lambda path,value: "{:.6f}kWh".format(value)


class INA226Service(SimpleI2CService):
    def __init__(self, conn, i2cBus, i2cAddr, serviceType, shuntRes, maxExpCur):
        self.shuntRes = shuntRes
        self.maxExpCur = maxExpCur
        super().__init__(conn, i2cBus, i2cAddr, serviceType, 'INA226')

    def _configure_service(self):
        self.device = INA226(busnum=self.i2cBus, address=self.i2cAddr, max_expected_amps=self.maxExpCur, shunt_ohms=self.shuntRes, log_level=logging.INFO)
        self.device.configure(avg_mode=INA226.AVG_4BIT, bus_ct=INA226.VCT_2116us_BIT, shunt_ct=INA226.VCT_2116us_BIT)
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
        # With the parameters 4 samples and 2.116ms conversion time the conversion needs around 8.5ms per channel
        # As there are two channels (supply voltage and current) the overall time is around 17ms
        while self.device.is_conversion_ready() == 0:
            # Sleep 10ms
            time.sleep(0.01)
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


class INA226DCLoadService(INA226Service):
    def __init__(self, conn, i2cBus, i2cAddr, shuntRes, maxExpCur):
        super().__init__(conn, i2cBus, i2cAddr, 'dcload', shuntRes, maxExpCur)

    def _configure_energy_history(self):
        self.service.add_path('/History/EnergyIn', 0, gettextcallback=ENERGY_TEXT)

    def _voltage(self):
        return self.device.supply_voltage()

    def _increment_energy_usage(self, change):
        self._local_values['/History/EnergyIn'] += change


class INA226DCSourceService(INA226Service):
    def __init__(self, conn, i2cBus, i2cAddr, shuntRes, maxExpCur):
        super().__init__(conn, i2cBus, i2cAddr, 'dcsource', shuntRes, maxExpCur)

    def _configure_energy_history(self):
        self.service.add_path('/History/EnergyOut', 0, gettextcallback=ENERGY_TEXT)

    def _voltage(self):
        return self.device.voltage()

    def _increment_energy_usage(self, change):
        self._local_values['/History/EnergyOut'] += change
