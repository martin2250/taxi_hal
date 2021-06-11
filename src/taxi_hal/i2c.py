from . import smc
import time

_I2C_WORD_0 = 0x1500
_I2C_WORD_1 = 0x1502
_I2C_WORD_2 = 0x1504
_I2C_START = 0x1506
_I2C_READ = 0x1508
_I2C_IDLE = 0x150a

# register reverse engineering:
# - first byte: command
#   - bit 7-5: should be set to "100"
#   - bit 4-3: number of bytes to read - 1 (????) (excluding address and subaddress)
#   - bit 2-1: number of bytes to write - 1 (excluding address and subaddress)
#   - bit 0: 0=write, 1=read
# - second byte: i2c address
# - third byte: i2c 'subaddress'
# - fourth byte...: i2c data

def write(i2c_addr: int, sub_addr: int, data: bytes):
    """Write one to three bytes to I2C client"""
    if len(data) > 3 or len(data) < 1:
        raise ValueError('data length not in between 1 and 3')
    command = 0x80 | ((len(data) - 1) << 1)
    # mask away R/W bit
    smc.write_16(_I2C_WORD_0, (command << 8) | (i2c_addr & 0xfe))
    smc.write_16(_I2C_WORD_1, ((sub_addr & 0xff) << 8) | data[0])
    if len(data) > 1:
        word_2 = data[1] << 8
        if len(data) > 2:
            word_2 |= data[2]
        smc.write_16(_I2C_WORD_2, word_2)
    smc.write_16(_I2C_START, 0x1)

def read(i2c_addr: int, sub_addr: int, count: int):
    """Read one or two bytes from I2C client"""
    if count < 1 or count > 2:
        raise ValueError('invalid count')
    command = 0x81 | ((count - 1) << 3)
    # set R/W bit
    smc.write_16(_I2C_WORD_0, (command << 8) | (i2c_addr & 0xfe) | 0x1)
    smc.write_16(_I2C_WORD_1, ((sub_addr & 0xff) << 8) | 0x00)
    smc.write_16(_I2C_START, 0x1)
    # wait for transaction to finish
    while smc.read_16(_I2C_IDLE) == 0:
        time.sleep(1e-4)
    data_reg = smc.read_16(_I2C_READ)
    print(f'data reg 0x{data_reg:04X}')
    if count == 1:
        return bytes([data_reg & 0xff])
    elif count == 2:
        return bytes([data_reg >> 8, data_reg & 0xff])