import pytest
import device_utils


@pytest.fixture
def mock_conn():
    return None


@pytest.fixture
def simple_device_config():
    return {
        "module": "test_device",
        "class": "SimpleDevice",
        "bus": 0,
        "address": 0,
        "updateInterval": 10,
    }


def test_simple_device(mock_conn, simple_device_config):
    dev = device_utils.createDevice(mock_conn, simple_device_config)
    assert dev.address == 0


@pytest.fixture
def param_device_config():
    return {
        "module": "test_device",
        "class": "ParamDevice",
        "bus": 0,
        "address": 1,
        "updateInterval": 10,
        "extraParam": "foobar",
    }


def test_device_with_params(mock_conn, param_device_config):
    dev = device_utils.createDevice(mock_conn, param_device_config)
    assert dev.address == 1
    assert dev.extraParam == "foobar"


class SimpleDevice():
    def __init__(self, conn, i2cBus, i2cAddr):
        self.conn = conn
        self.bus = i2cBus
        self.address = i2cAddr


class ParamDevice(SimpleDevice):
    def __init__(self, conn, i2cBus, i2cAddr, extraParam):
        super().__init__(conn, i2cBus, i2cAddr)
        self.extraParam = extraParam
