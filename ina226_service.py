import logging
from ina226 import INA226
from service_utils import DCI2CService, DCLoadServiceMixin, DCSourceServiceMixin
from ina226 import DeviceRangeError
import logging
import time


class INA226Service(DCI2CService):
    def __init__(self, conn, i2cBus, i2cAddr, serviceType, maxExpectedCurrent, shuntResistance):
        super().__init__(conn, i2cBus, i2cAddr, serviceType, 'INA226', maxExpectedCurrent=maxExpectedCurrent, shuntResistance=shuntResistance)

    def _configure_service(self, maxExpectedCurrent, shuntResistance):
        self.device = INA226(busnum=self.i2cBus, address=self.i2cAddr, max_expected_amps=maxExpectedCurrent, shunt_ohms=shuntResistance, log_level=logging.INFO)
        self.device.configure(avg_mode=INA226.AVG_4BIT, bus_ct=INA226.VCT_2116us_BIT, shunt_ct=INA226.VCT_2116us_BIT)
        self.device.sleep()
        super()._configure_service()
        
    def update(self):
        self.device.wake()
        try:
        # attendre la fin de conversion
            while self.device.is_conversion_ready() == 0:
                time.sleep(0.01)
            voltage = round(self._voltage(), 3)
            current = round(self.device.current() / 1000, 3)
            power = round(self.device.power() / 1000, 3)
            now = time.perf_counter()
        except DeviceRangeError:
            logging.warning(
                "INA226 overflow (current or shunt voltage out of range), skipping update"
            )
            self.device.sleep()
            return
        self.device.sleep()
        super()._update(voltage, current, power, now)


class INA226DCLoadService(DCLoadServiceMixin,INA226Service):
    def __init__(self, conn, i2cBus, i2cAddr, **kwargs):
        super().__init__(conn, i2cBus, i2cAddr, 'dcload', **kwargs)

    def _voltage(self):
        return self.device.supply_voltage()


class INA226DCSourceService(DCSourceServiceMixin,INA226Service):
    def __init__(self, conn, i2cBus, i2cAddr, **kwargs):
        super().__init__(conn, i2cBus, i2cAddr, 'dcsource', **kwargs)

    def _voltage(self):
        return self.device.voltage()
