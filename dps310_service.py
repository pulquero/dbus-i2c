from smbus2 import SMBus
import DPS
from service_utils import TemperatureService


class DPS310Service(TemperatureService):
    def __init__(self, conn, i2cBus, i2cAddr):
        super().__init__(conn, i2cBus, i2cAddr, 'temperature', 'DPS310')

    def _configure_service(self):
        super()._configure_service()
        self.service.add_path("/Pressure", None)

    def update(self):
        with SMBus(self.i2cBus) as bus:
            dps310 = DPS.DPS(bus, self.i2cAddr)
            scaled_p = dps310.calcScaledPressure()
            scaled_t = dps310.calcScaledTemperature()
            p = dps310.calcCompPressure(scaled_p, scaled_t)
            t = dps310.calcCompTemperature(scaled_t)
        self._update(t, None, p)
