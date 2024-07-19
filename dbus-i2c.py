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
import device_utils
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dbus-i2c")


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


def createUpdateWrapper(device):
    def updateWrapper():
        try:
            device.update()
            return True
        except:
            device.logger.exception("Failed to update")
            return False
    return updateWrapper


def createPublishWrapper(device):
    def publishWrapper():
        try:
            device.publish()
            return True
        except:
            device.logger.exception("Failed to publish")
            return False
    return publishWrapper


def initDBusServices():
    setupOptions = Path("/data/setupOptions/dbus-i2c")
    for devicePath in setupOptions.glob("device-*"):
        logger.info(f"Found I2C device file {devicePath}")
        try:
            with devicePath.open() as f:
                deviceConfig = json.load(f)
            updateInterval = deviceConfig.pop('updateInterval')
            publishInterval = deviceConfig.pop('publishInterval', 1000)
            device = device_utils.createDevice(dbusConnection(), deviceConfig)
            updater = createUpdateWrapper(device)
            updater()
            if updateInterval <= 1000:
                GLib.timeout_add(updateInterval, updater)
                if hasattr(device, 'publish'):
                    publisher = createPublishWrapper(device)
                    publisher()
                    GLib.timeout_add_seconds(max(publishInterval//1000, 1), publisher)
            else:
                GLib.timeout_add_seconds(updateInterval//1000, updater)
            device.logger.info("Registered")
        except json.JSONDecodeError:
            logger.warning("Ignoring invalid JSON file")


def main():
    DBusGMainLoop(set_as_default=True)
    initDBusServices()
    mainloop = GLib.MainLoop()
    mainloop.run()


if __name__ == "__main__":
    main()
