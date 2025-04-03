
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


# Home Assistant MQTT integration

### Example YAML

	- sensor:
	    unique_id: "pv_power"
	    object_id: "solar_charger_power"
	    name: "PV power"
	    device_class: power
	    unit_of_measurement: "W"
	    state_topic: "N/xxxxxxxxxxxx/solarcharger/xxx/Yield/Power"
	    value_template: "{{ value_json.value | float(0) | round(2) }}"
	    force_update: true
	    availability_topic: "N/xxxxxxxxxxxx/solarcharger/xxx/Connected"
	    availability_template: "{{ value_json.value }}"
	    payload_available: 1
	    payload_not_available: 0
	    device:
	      identifiers: "com.victronenergy.solarcharger.ttyUSB0"
	      name: "Solar charger"
	      model: "SmartSolar Charger MPPT 100/30"
