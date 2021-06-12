import ctypes
import logging

logger = logging.getLogger(__name__)

_smc = ctypes.cdll.LoadLibrary('/opt/taxi/lib/libsmcdrv.so')
_smc.smc_open(None)

def read_16(offset: int) -> int:
    value = _smc.smc_rd16(offset)
    logger.debug(f'read [0x{offset:04X}] = 0x{value:04X}')
    return value

def write_16(offset: int, value: int):
    logger.debug(f'write [0x{offset:04X}] = 0x{value:04X}')
    _smc.smc_wr16(offset, value)
