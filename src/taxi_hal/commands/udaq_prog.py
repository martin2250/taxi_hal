import argparse
import logging
import time

import stm32loader.bootloader
import stm32loader.uart

from ..hal import taxi_fanout

logger = logging.getLogger(__name__)


def udaq_channel(desc: str) -> list[str]:
    channels = set()
    for part in desc.split(','):
        if '-' in part:
            start, _, stop = part.partition('-')
            for i in range(int(start), int(stop) + 1):
                if i not in range(8):
                    raise ValueError(f'channel {i} is out of range')
                channels.add(i)
        else:
            i = int(part)
            if i not in range(7):
                raise ValueError(f'channel {i} is out of range')
            channels.add(i)
    channels = list(channels)
    channels.sort()
    return channels


def build_bitmask(channels: list[int]) -> int:
    mask = 0
    for chan in channels:
        mask |= 1 << chan
    return mask

def decode_bitmask(mask: int) -> list[int]:
    channels = []
    for i in range(7):
        if (mask & 0x01) != 0:
            channels.append(str(i))
        mask >>= 1
    return channels

FLASH_ADDR = 0x08000000


class CmdUdaqPower:
    def build_parser(parser: argparse.ArgumentParser):
        parser.add_argument('task',
                            choices=('on', 'off', 'read', 'check'))
        parser.add_argument('--channels',
                            help='uDAQs channels, eg. "0-3,7"',
                            type=udaq_channel)

    def run(task: str, channels: list[int] = None, **kwargs) -> bool:
        fan = taxi_fanout.TaxiFanoutBoard()
        fan.setup()
        # check current status
        power = fan.get_udaq_power()
        # read? print status and exit
        if task == 'read' or task == 'check':
            if power == 0:
                print('no channels are currently powered on')
                return True
            channels = ','.join(decode_bitmask(power))
            s = 's' if len(channels) > 1 else ''
            are = 'are' if len(channels) > 1 else 'is'
            print(f'channel{s} {channels} {are} currently powered on')
            # also check the power status
            if task == 'check':
                pwr_ok = fan.get_power_mon()
                pwr_fail = power & (~pwr_ok)
                if pwr_fail == 0:
                    print('no overcurrent')
                else:
                    channels = ','.join(decode_bitmask(pwr_fail))
                    s = 's' if len(channels) > 1 else ''
                    print(f'overcurrent on channel{s} {channels}')
            return True
        # check --channels
        if not channels:
            print('you need to provide the --channel argument')
            return False
        # power off all channels (to reboot uDAQs)
        mask = build_bitmask(channels)
        if (power & mask) != 0:
            logger.info(f'powering off selected uDAQs')
            power &= ~mask
            fan.set_udaq_power(power)
            if task != 'off':
                logger.info('waiting for capacitors to discharge...')
                time.sleep(6)
        # we're done here
        if task == 'off':
            return
        logger.info(f'powering on selected uDAQs')
        power |= mask
        fan.set_udaq_power(power)
        # bootloader connections
        serial_connection = stm32loader.uart.SerialConnection(
            '/dev/ttyS2', 115200)
        serial_connection.connect()
        # booting microcontrollers
        ok = True
        for channel in channels:
            logger.info(f'channel {channel} - resetting uDAQ')
            # enable duplex communication
            fan.set_udaq_prog(True, channel)
            time.sleep(0.1)
            # boot STM
            serial_connection.serial_connection.flush()
            stm32 = stm32loader.bootloader.Stm32Bootloader(serial_connection)
            try:
                stm32.reset_from_system_memory()
                stm32.go(FLASH_ADDR)
            except:
                logger.error(
                    f'channel {channel} - could not reach STM32 bootloader, powering off')
                power &= ~(1 << channel)
                fan.set_udaq_power(power)
                ok = False
            fan.set_udaq_prog(False, 0)
            # todo: clear fifo in FPGA
            del stm32
        return ok


class CmdUdaqProg:
    def build_parser(parser: argparse.ArgumentParser):
        parser.add_argument('--channels',
                            help='uDAQs channels, eg. "0-3,7"',
                            type=udaq_channel,
                            required=True)
        parser.add_argument('--firmware',
                            help='path to uDAQ firmware',
                            required=True)

    def run(channels: list[int], firmware: str, **kwargs):
        # read firmware file
        with open(firmware, 'rb') as f_fw:
            firmware = bytearray(f_fw.read())
        fan = taxi_fanout.TaxiFanoutBoard()
        fan.setup()
        # check current status
        power = fan.get_udaq_power()
        # power off all channels (to reboot uDAQs)
        mask = build_bitmask(channels)
        if (power & mask) != 0:
            logger.info(f'powering off selected uDAQs')
            power &= ~mask
            fan.set_udaq_power(power)
            logger.info('waiting for capacitors to discharge...')
            time.sleep(6)
        logger.info(f'powering on selected uDAQs')
        power |= mask
        fan.set_udaq_power(power)
        # bootloader connections
        serial_connection = stm32loader.uart.SerialConnection(
            '/dev/ttyS2', 115200)
        serial_connection.connect()
        # program microcontroller

        def program_channel(channel: int) -> bool:
            nonlocal fan, firmware, serial_connection
            logger.info(f'channel {channel} - resetting uDAQ')
            # enable duplex communication
            fan.set_udaq_prog(True, channel)
            time.sleep(0.05)
            # boot STM
            serial_connection.serial_connection.flush()
            stm32 = stm32loader.bootloader.Stm32Bootloader(serial_connection)
            stm32.verbosity = 0
            try:
                stm32.reset_from_system_memory()
            except:
                logger.error(
                    f'channel {channel} - could not reach STM32 bootloader, powering off')
                return False
            try:
                stm32.get()
                logger.info(f'channel {channel} - erasing flash')
                stm32.erase_memory()
                logger.info(f'channel {channel} - writing flash')
                stm32.write_memory_data(FLASH_ADDR, firmware)
                logger.info(f'channel {channel} - verifying flash')
                firmware_read = stm32.read_memory_data(
                    FLASH_ADDR, len(firmware))
                stm32loader.bootloader.Stm32Bootloader.verify_data(
                    firmware_read, firmware)
                logger.info(f'channel {channel} - flash verified, booting')
                stm32.go(FLASH_ADDR)
            except Exception as e:
                logger.error(
                    f'channel {channel} - error while programming, powering off: {e}')
                return False
            # todo: clear fifo in FPGA
            return True
        # program all channels and handle errors
        ok = True
        for channel in channels:
            chan_ok = program_channel(channel)
            fan.set_udaq_prog(False, 0)
            if not chan_ok:
                ok = False
                power &= ~(1 << channel)
                fan.set_udaq_power(power)
        # done
        return ok
