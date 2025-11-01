from smbus2 import SMBus
from service_utils import SimpleI2CService

ALARM_OK = 0
ALARM_WARNING = 1
ALARM_ALARM = 2

DISTRIBUTOR_STATE_NOT_AVAILABLE = 0
DISTRIBUTOR_STATE_CONNECTED = 1
DISTRIBUTOR_STATE_NO_BUS_POWER = 2
DISTRIBUTOR_STATE_COMMS_LOST = 3

FUSE_STATE_NOT_AVAILABLE = 0
FUSE_STATE_NOT_USED = 1
FUSE_STATE_OK = 2
FUSE_STATE_BLOWN = 3


class LynxDistributorService():
    """
    See https://github.com/twam/dbus-lynx-distributor.
    """

    def __init__(self, conn, i2cBus, i2cAddr):
        super().__init__(conn, i2cBus, i2cAddr, 'battery', 'LynxDistributor')
        self.distributors = [
            ("A", [0, 1, 2, 3]),
            ("B", [0, 1, 2, 3]),
            ("C", [0, 1, 2, 3]),
            ("D", [0, 1, 2, 3])
        ]

    def _configure_service(self):
        self.service.add_path("/NrOfDistributors", len(self.distributors))
        for dinfo in self.distributors:
            distributor = dinfo[0]
            fuses = dinfo[1]
            self.service.add_path(f"/Distributor/{distributor}/Status", None)
            self.service.add_path(f"/Distributor/{distributor}/Alarms/ConnectionLost", None)
            for fuse in fuses:
                self.add_settable_path(f"/Distributor/{distributor}/Fuse/{fuse}/Name", None)
                self.service.add_path(f"/Distributor/{distributor}/Fuse/{fuse}/Status", None)
                self.service.add_path(f"/Distributor/{distributor}/Fuse/{fuse}/Alarms/Blown", None)

    def update(self):
        for i, dinfo in enumerate(self.distributors):
            distributor = dinfo[0]
            fuses = dinfo[1]
            addr = self.i2cAddr + i

            with SMBus(self.i2cBus) as bus:
                state = bus.read_byte(addr)

            no_bus_power = (state & 0b00000010)
            self.service[f"/Distributor/{distributor}/Status"] = DISTRIBUTOR_STATE_NO_BUS_POWER if no_bus_power else DISTRIBUTOR_STATE_CONNECTED
            self.service[f"/Distributor/{distributor}/Alarms/ConnectionLost"] = ALARM_OK
            for fuse in fuses:
                if no_bus_power:
                    fuse_state = FUSE_STATE_NOT_AVAILABLE
                    fuse_alarm = ALARM_OK
                else:
                    fuse_blown = (state & (0b00010000 << fuse))
                    if fuse_blown:
                        fuse_state = FUSE_STATE_BLOWN
                        fuse_alarm = ALARM_ALARM
                    else:
                        fuse_state = FUSE_STATE_OK
                        fuse_alarm = ALARM_OK

                self.service[f"/Distributor/{distributor}/Fuse/{fuse}/Status"] = fuse_state
                self.service[f"/Distributor/{distributor}/Fuse/{fuse}/Alarms/Blown"] = fuse_alarm
