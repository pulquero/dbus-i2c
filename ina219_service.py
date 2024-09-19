from ina219 import INA219
from service_utils import DCI2CService, DCLoadServiceMixin, DCSourceServiceMixin
import time

SHUNT_OHMS = 0.1
MAX_EXPECTED_AMPS = 2


class INA219Service(DCI2CService):
    def __init__(self, conn, i2cBus, i2cAddr, serviceType, maxExpectedCurrent=MAX_EXPECTED_AMPS, shuntResistance=SHUNT_OHMS, invertCurrent=False):
        super().__init__(conn, i2cBus, i2cAddr, serviceType, 'INA219', maxExpectedCurrent=maxExpectedCurrent, shuntResistance=shuntResistance, invertCurrent=invertCurrent)

    def _configure_service(self, maxExpectedCurrent, shuntResistance, invertCurrent):
        self.device = INA219(shuntResistance, busnum=self.i2cBus, address=self.i2cAddr, max_expected_amps=maxExpectedCurrent)
        self.device.configure(voltage_range=INA219.RANGE_16V)
        self.device.sleep()
        self.current_direction = -1 if invertCurrent else 1
        super()._configure_service()

    def update(self):
        self.device.wake()
        voltage = round(self._voltage(), 3)
        current = self.current_direction * round(self.device.current()/1000, 3)
        power = round(self.device.power()/1000, 3)
        now = time.perf_counter()  # record the time as close to measurement-taking as possible
        self.device.sleep()
        super()._update(voltage, current, power, now)


class INA219DCLoadService(DCLoadServiceMixin,INA219Service):
    def __init__(self, conn, i2cBus, i2cAddr, **kwargs):
        super().__init__(conn, i2cBus, i2cAddr, 'dcload', **kwargs)

    def _voltage(self):
        return self.device.supply_voltage()


class INA219DCSourceService(DCSourceServiceMixin,INA219Service):
    def __init__(self, conn, i2cBus, i2cAddr, **kwargs):
        super().__init__(conn, i2cBus, i2cAddr, 'dcsource', **kwargs)

    def _voltage(self):
        return self.device.voltage()
