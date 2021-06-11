from . import i2c

class PCA9555A:
    '''Wrapper for PCA9555A I2C port expander

    16 bit access convention: (port_0) << 8 | port_1

    details: https://www.nxp.com/part/PCA9555APW#/
    '''

    PORT_0 = 0
    PORT_1 = 1
    PORT_BOTH = -1 # access in 16 bit mode

    def __init__(self, address: int):
        '''PCA9555A, address = 8 bit address (with RW bit)'''
        self.address = address
    
    def _write(self, reg: int, port: int, value: int):
        if port == PCA9555A.PORT_BOTH:
            i2c.write(self.address, reg, value.to_bytes(2, 'big'))
        else:
            reg |= port & 0x01
            i2c.write(self.address, reg, bytes([value & 0xff]))
        
    def _read(self, reg: int, port: int) -> int:
        if port == PCA9555A.PORT_BOTH:
            data = i2c.read(self.address, reg, 2)
            return int.from_bytes(data, 'big')
        else:
            reg |= port & 0x01
            data = i2c.read(self.address, reg, 1)
            return data[0]

    def set_direction(self, port: int, mask: int):
        '''Set ports to inputs / outputs
        
        @param port PORT_0/1/BOTH
        @param mask I/O setting for every GPIO. 1=input, 0=output
        '''
        self._write(0x06, port, mask)

    def get_direction(self, port: int) -> int:
        '''Set ports to inputs / outputs
        
        @param port PORT_0/1/BOTH
        @return I/O setting for every GPIO. 1=input, 0=output
        '''
        return self._read(0x06, port)

    def set_output(self, port: int, value: int):
        '''Set output port state
        
        @param port PORT_0/1/BOTH
        @param output value for every GPIO. 1=high, 0=low
        '''
        self._write(0x02, port, value)

    def get_output(self, port: int) -> int:
        '''Get output port state
        
        @param port PORT_0/1/BOTH
        @return output value for every GPIO. 1=high, 0=low
        '''
        return self._read(0x02, port)

    def get_input(self, port: int) -> int:
        '''Get output port state
        
        @param port PORT_0/1/BOTH
        @return input value for every GPIO. 1=high, 0=low
        '''
        return self._read(0x00, port)
