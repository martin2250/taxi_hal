from .pca9555a import PCA9555A

class TaxiFanoutBoard:
    def __init__(self):
        # port 0: pwr_en, port 1: pwr_fault
        self.ic6 = PCA9555A(0x40)
        # port 0: [prog_en : 1, prog_addr : 3], port 1: [pwr_mon : 2]
        self.ic9 = PCA9555A(0x42)
    
    def setup(self):
        self.ic6.set_direction(PCA9555A.PORT_0, 0x00) # pwr en
        self.ic6.set_direction(PCA9555A.PORT_1, 0xff) # pwr fault
        self.ic9.set_direction(PCA9555A.PORT_0, 0xf0) # prog addr, en
        self.ic9.set_direction(PCA9555A.PORT_1, 0xff) # pwr mon (24V redundant inputs)

    def set_udaq_prog(self, enable: bool, port: int = 0):
        mask = port & 0b0111
        # prog en is low active
        if not enable:
            mask |= 0b1000
        self.ic9.set_output(PCA9555A.PORT_0, port & mask)

    def get_power_mon(self) -> int:
        return self.ic9.get_input(PCA9555A.PORT_1) >> 6

    def get_udaq_fault(self) -> int:
        return self.ic6.get_input(PCA9555A.PORT_1)
    
    def set_udaq_power(self, mask: int):
        self.ic6.set_output(PCA9555A.PORT_0, mask & 0xff)
    
    def get_udaq_power(self) -> int:
        return self.ic6.get_output(PCA9555A.PORT_0)


