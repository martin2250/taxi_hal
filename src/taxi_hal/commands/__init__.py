import argparse
from typing import Any

from taxi_hal.hal.taxi_fanout import TaxiFanoutBoard

from . import udaq_prog

commands: dict[str, Any] = {
    'udaq_power': udaq_prog.CmdUdaqPower,
    'udaq_prog': udaq_prog.CmdUdaqProg,
}
