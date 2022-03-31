import board
import busio
import digitalio
from urp import *

uart = busio.UART(tx=board.D8, rx=board.D7, baudrate=115200)

led = digitalio.DigitalInOut(board.D0)
led.switch_to_output()

led.value=True

from time import sleep
i=0
uart.timeout=1/115200
# while True:
# 	i+=1
# 	print(i)
# 	uart.write(bytes([0x90,0x3c,0x40]))
# 	# print(b"GOO"+uart.read(),gtoc())
# 	sleep(.5)
# 	led.value=not led.value














#Please use the antennae! it makes it much better.
"""
Simple example of using the RF24 class.
"""
import time
import struct
import board
import digitalio
from urp import *

# if running this on a ATSAMD21 M0 based board
# from circuitpython_nrf24l01.rf24_lite import RF24
from circuitpython_nrf24l01.rf24 import RF24

# change these (digital output) pins accordingly
LIGHTBOARD=False
if LIGHTBOARD:
	ce = digitalio.DigitalInOut(board.D21)
	csn = digitalio.DigitalInOut(board.D20)
else:
	ce = digitalio.DigitalInOut(board.D9)
	csn = digitalio.DigitalInOut(board.D14)

# using board.SPI() automatically selects the MCU's
# available SPI pins, board.SCK, board.MOSI, board.MISO
spi = board.SPI()  # init spi bus object

# we'll be using the dynamic payload size feature (enabled by default)
# initialize the nRF24L01 on the spi bus object
nrf = RF24(spi, csn, ce)

# set the Power Amplifier level to -12 dBm since this test example is
# usually run with nRF24L01 transceivers in close proximity
nrf.pa_level = 0

nrf.data_rate=1#1:1mbps, 2:2mbps, 250:250kbps

# addresses needs to be in a buffer protocol object (bytearray)
address = [b"1Node", b"2Node"]

# to use different addresses on a pair of radios, we need a variable to
# uniquely identify which address this radio will use to transmit
# 0 uses address[0] to transmit, 1 uses address[1] to transmit
radio_number = LIGHTBOARD

# set TX address of RX node into the TX pipe
nrf.open_tx_pipe(address[radio_number])  # always uses pipe 0

# set RX address of TX node into an RX pipe
nrf.open_rx_pipe(1, address[not radio_number])  # using pipe 1


def master():  # count = 5 will only transmit 5 packets
	"""Transmits an incrementing integer every second"""
	nrf.listen = False  # ensures the nRF24L01 is in TX mode
	while True:
		msg=str(gtoc())
		result=nrf.send(msg.encode())
		print(result,msg)


def slave():
	nrf.listen = True  # put radio into RX mode and power up
	while True:
		if nrf.available():
			led.value=True
			# grab information about the received payload
			payload_size, pipe_number = (nrf.any(), nrf.pipe)
			# fetch 1 payload from RX FIFO
			buffer = nrf.read()  # also clears nrf.irq_dr status flag
			uart.write(buffer)
			try:
				print(buffer)
			except UnicodeError:
				print("(Cant print)")
			led.value=False


if LIGHTBOARD:
	master()
else:
	slave()

