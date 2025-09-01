from smbus2 import SMBus
import DPS
from service_utils import SimpleI2CService


def _safe_min(newValue, currentValue):
    return min(newValue, currentValue) if currentValue else newValue


def _safe_max(newValue, currentValue):
    return max(newValue, currentValue) if currentValue else newValue


class DPS310Service(SimpleI2CService):
    def __init__(self, conn, i2cBus, i2cAddr):
        super().__init__(conn, i2cBus, i2cAddr, 'temperature', 'DPS310')

    def _configure_service(self):
        self.service.add_path("/Temperature", None)
        # default type is battery
        self.add_settable_path("/TemperatureType", 0, 0, 2)
        self.service.add_path("/Pressure", None)
        self.service.add_path("/History/MinimumTemperature", None)
        self.service.add_path("/History/MaximumTemperature", None)

    def update(self):
        with SMBus(self.i2cBus) as bus:
            dps310 = DPS(bus, self.i2cAddr)
            scaled_p = dps310.calcScaledPressure()
            scaled_t = dps310.calcScaledTemperature()
            p = dps310.calcCompPressure(scaled_p, scaled_t)
            t = dps310.calcCompTemperature(scaled_t)    

        temp = round(t, 1)
        self.service["/Temperature"] = temp
        self.service["/Pressure"] = round(p, 1)
        self.service["/History/MinimumTemperature"] = _safe_min(temp, self.service["/History/MinimumTemperature"])
        self.service["/History/MaximumTemperature"] = _safe_max(temp, self.service["/History/MaximumTemperature"])
