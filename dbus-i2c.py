#!/usr/bin/env python

import os
import sys
from script_utils import SCRIPT_HOME
sys.path.insert(1, os.path.join(os.path.dirname(__file__), f"{SCRIPT_HOME}/ext"))

import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
from pathlib import Path
import json
import importlib
import logging
import smbus2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dbus-i2c")

i2cDevices = []


class SystemBus(dbus.bus.BusConnection):
    def __new__(cls):
        return dbus.bus.BusConnection.__new__(cls, dbus.bus.BusConnection.TYPE_SYSTEM)


class SessionBus(dbus.bus.BusConnection):
    def __new__(cls):
        return dbus.bus.BusConnection.__new__(cls, dbus.bus.BusConnection.TYPE_SESSION)


def dbusConnection():
    return SessionBus() if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else SystemBus()


def update():
    for i2cDevice in i2cDevices:
        i2cDevice.update()
    return True


def initDBusServices():
    setupOptions = Path("/data/setupOptions/dbus-i2c")
    buses = {}
    for busPath in setupOptions.glob("bus-*"):
        logger.info(f"Found I2C bus file {busPath}")
        busId = int(busPath.name[len("bus-"):])
        i2cBus = smbus2.SMBus(busId)
        i2cBus.id = busId
        buses[busId] = i2cBus
        logger.info(f"Registered I2C bus {i2cBus.id}")

    if not buses:
        raise Exception("No I2C buses configured!")

    conn = dbusConnection()
    for devicePath in setupOptions.glob("device-*"):
        logger.info(f"Found I2C device file {devicePath}")
        with devicePath.open() as f:
            deviceConfig = json.load(f)
        deviceModule = importlib.import_module(deviceConfig['module'])
        constructor = getattr(deviceModule, deviceConfig['class'])
        i2cBus = buses[deviceConfig['bus']]
        addr = deviceConfig['address']
        device = constructor(conn, i2cBus, addr)
        i2cDevices.append(device)
        logger.info("Registered {} on bus {} at address {:#04x}".format(device, i2cBus.id, addr))

    if not i2cDevices:
        raise Exception("No I2C devices configured!")


def main():
    DBusGMainLoop(set_as_default=True)
    initDBusServices()
    update()
    GLib.timeout_add(10000, update)
    mainloop = GLib.MainLoop()
    mainloop.run()


if __name__ == "__main__":
    main()
