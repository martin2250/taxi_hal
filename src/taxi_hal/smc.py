import ctypes

_smc = ctypes.cdll.LoadLibrary('/opt/taxi/lib/libsmcdrv.so')
_smc.smc_open(None)

def read_16(offset: int) -> int:
    return _smc.smc_rd16(offset)

def write_16(offset: int, value: int):
    _smc.smc_wr16(offset, value)
