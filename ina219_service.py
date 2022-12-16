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
    def _init_service(self, conn):
        self.device = INA219(SHUNT_OHMS, busnum=self.i2cBus, address=self.i2cAddr, max_expected_amps=MAX_EXPECTED_AMPS)
        self.device.configure(voltage_range=INA219.RANGE_16V)
        self.device.sleep()
        self.serviceType = "dcload"
        self.deviceName = "INA219"
        self.service = createService(conn, self.serviceType, self.i2cBus, self.i2cAddr,
            __file__, self.deviceName)
        self.service.add_path("/Dc/0/Voltage", None)
        self.service.add_path("/Dc/0/Current", None)
        self.service.add_path("/History/EnergyIn", 0)
        self.service.add_path("/Alarms/LowVoltage", 0)
        self.service.add_path("/Alarms/HighVoltage", 0)
        self.service.add_path("/Alarms/LowTemperature", 0)
        self.service.add_path("/Alarms/HighTemperature", 0)
        self.add_settable_path("/CustomName", "", "", "")
        self.service.add_path("/Dc/0/Power", None)
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
            self.service["/History/EnergyIn"] += toKWh((self.lastPower.power + power)/2 * (now - self.lastPower.timestamp))
        self.lastPower = PowerSample(power, now)
