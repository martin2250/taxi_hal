import logging
import sys
import time

import stm32loader.bootloader
import stm32loader.uart

from . import taxi_fanout

logger = logging.getLogger(__name__)

def activate_udaqs(udaqs: str):
    udaqs = udaqs.split(',')
    mask = 0
    for udaq in udaqs:
        if '-' in udaq:
            start, _, stop = udaq.partition('-')
            for i in range(int(start), int(stop) + 1):
                mask |= (1 << i)
        else:
            mask |= 1 << int(udaq)
    mask &= 0xff

    if mask == 0:
        logger.error(f'no uDAQs selected!')
        exit(1)

    logger.info(f'mask: {mask:08b}')

    fan = taxi_fanout.TaxiFanoutBoard()
    fan.setup()

    logger.info(f'turning off selected uDAQs')
    power = fan.get_udaq_power()
    fan.set_udaq_power(power & (~mask))

    logger.info('waiting for capacitors to discharge...')
    time.sleep(6)

    logger.info(f'turning on selected uDAQs')
    fan.set_udaq_power(power | mask)

    serial_connection = stm32loader.uart.SerialConnection('/dev/ttyS2', 115200)
    serial_connection.connect()

    device_family = 'F4'

    for i in range(8):
        if ((mask >> i) & 0x01) == 0:
            continue
        logger.info(f'booting uDAQ on channel {i}')
        fan.set_udaq_prog(True, i)
        time.sleep(0.1)

        serial_connection.serial_connection.flush()
        stm32 = stm32loader.bootloader.Stm32Bootloader(serial_connection)
        stm32.reset_from_system_memory()

        stm32.go(0x08000000)

        fan.set_udaq_prog(False, i)

        # todo: clear fifo

        del stm32
    
    logger.info('done')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    commands = {
        'activate_udaqs': activate_udaqs,
    }

    if len(sys.argv) < 2:
        print('usage: python -m taxi_hal <command> (args)')
        print('available commands:')
        for c in commands:
            print('> ', c)
        exit(1)
    
    commands[sys.argv[1]](*sys.argv[2:])
