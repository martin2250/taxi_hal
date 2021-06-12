from dataclasses import dataclass, field
# from cobs import cobs
from .pca9555a import PCA9555A
from . import smc

@dataclass
class UDaqAdcConfig:
    timer_delay: float = field(default=18e-6)  # ADC sample delay (s)
    recording_thresholds: tuple[int, int] = field(
        default=(0, 0))  # TODO: what does this do?


@dataclass
class UDaqConfig:
    def _default_adc_config() -> dict[int, UDaqAdcConfig]:
        return {
            0: UDaqAdcConfig(),
            2: UDaqAdcConfig(),
            12: UDaqAdcConfig(),
        }
    adc_configuration: dict[int, UDaqAdcConfig] = field(
        default_factory=_default_adc_config)
    frame_write_delay: float = field(default=1e-3)  # time between frames (s)
    bias_voltage: float = field(default=57.0)  # SiPM bias voltage (AUXDAC 1)
    trigger_threshold: int = field(default=1650)  # trigger threshold (DAC 1)


@dataclass
class UDaqHitBufferConfig(UDaqConfig):
    pass


class UDaq:
    def __init__(self):
        pass

    def send_line(self, line: str):
        data_raw = line.encode('ascii')
        # data_cobs = b'\0' + cobs.encode(data_raw) + b'\0'

    def set_bias_voltage(self, bias_voltage: float):
        auxdac = int(bias_voltage * 2740 / 56.0)
        self.send_line(f'AUXDAC 1 {auxdac}')

    def set_threshold(self, threshold: int):
        self.send_line(f'DAC 1 {threshold}')

    def set_adc_config(self, channel: int, config: UDaqAdcConfig):
        delay = int(config.timer_delay * 1e6)
        self.send_line(f'ADC_TIMER_DELAY {channel} {delay}')
        self.send_line(
            f'ADC_RECORDING_THRESHOLDS {channel} {config.recording_thresholds[0]} {config.recording_thresholds[1]}')
        self.send_line(f'ADC_ENABLE {channel} 1')

    def set_frame_write_delay(self, frame_write_delay: float):
        delay = int(frame_write_delay * 1e6)
        self.send_line(f'FRAME_WRITE_DELAY {delay}')

    def configure_hitbuffer(self, config: UDaqHitBufferConfig):
        self.send_line('STOP_RUN')
        self.send_line('RESET_SCHEDULE')
        self.send_line('ADC_RESET_THRESHOLDS')
        self.send_line('GETMON')
        self.send_line('TIMESTAMP_MODE 4')
        self.send_line('DISC_OPM 1')
        self.send_line('ADC_HIST_ENABLE 0')
        self.set_bias_voltage(config.bias_voltage)
        for adc in config.adc_configuration.items():
            self.set_adc_config(*adc)
        self.send_line('SET_LIVETIME_ENABLE 1')

class Taxi:
    def get_buildinfo(self) -> str:
        year = smc.read_16(8)
        month = smc.read_16(10)
        day = smc.read_16(12)
        version = smc.read_16(14)
        return f'{year:04X}-{month:02X}-{day:02X} v{version:04X}'

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
        if enable:
            # set ~prog_en low to enable programming
            self.ic9.set_output(PCA9555A.PORT_0, port & 0b0111)
        else:
            # set ~prog_en high to disable programming
            self.ic9.set_output(PCA9555A.PORT_0, 0b1000)

    def get_power_mon(self) -> int:
        return self.ic9.get_input(PCA9555A.PORT_1) >> 6

    def get_udaq_fault(self) -> int:
        return self.ic6.get_input(PCA9555A.PORT_1)
    
    def set_udaq_power(self, mask: int):
        self.ic6.set_output(PCA9555A.PORT_0, mask & 0xff)
    
    def get_udaq_power(self) -> int:
        return self.ic6.get_output(PCA9555A.PORT_0)
