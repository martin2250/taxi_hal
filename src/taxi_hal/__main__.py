from . import taxi_fanout
import time
import serial
import stm32loader.bootloader
import stm32loader.uart

fan = taxi_fanout.TaxiFanoutBoard()
# turn off all uDAQs
fan.set_udaq_power(0x00)
fan.set_udaq_prog(False, 0)
print('sleeping')
time.sleep(10) # wait for capacitors to discharge
fan.set_udaq_prog(True, 0)
time.sleep(0.5)
fan.set_udaq_power(0x01)
time.sleep(1)

serial_connection = stm32loader.uart.SerialConnection('/dev/ttyS2', 115200)
serial_connection.connect()
stm32 = stm32loader.bootloader.Stm32Bootloader(serial_connection)

print(stm32.get_id())
