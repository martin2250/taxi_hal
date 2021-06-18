from dataclasses import dataclass, field

# from cobs import cobs
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
