
# About

A set of DBus services for I2C devices.


# Install

Install [SetupHelper](https://github.com/kwindrem/SetupHelper),
you can find this package listed in the available packages to install.
Then, run `/data/dbus-i2c/setup`.

# Supported devices

#### BME280

Temperature service, including humidity and pressure.
Use with DVCC Shared Temperature Sense (STS) for battery temperature compensation.

#### SHT3x

Temperature service, including humidity.
Use with DVCC Shared Temperature Sense (STS) for battery temperature compensation.

#### INA219

DC load/source service.
Use with [DC System Aggregator](https://github.com/pulquero/DCSystemAggregator) to monitor all your loads/sources.

#### INA226

DC load/source service.
Use with [DC System Aggregator](https://github.com/pulquero/DCSystemAggregator) to monitor all your loads/sources.
