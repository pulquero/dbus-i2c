
# About

A set of DBus services for I2C devices.


# Install

Install [SetupHelper](https://github.com/kwindrem/SetupHelper), use [this version](https://github.com/pulquero/SetupHelper) if you want this package
to be available by default, else manually add it.


# Supported devices

#### BME280

Temperature service, including humidity and pressure.
Use with DVCC Shared Temperature Sense (STS) for battery temperature compensation.


#### INA219

DC load/source service.
Use with [DC System Aggregator](https://github.com/pulquero/DCSystemAggregator) to monitor all your loads/sources.
