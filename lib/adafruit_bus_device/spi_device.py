'\n`adafruit_bus_device.spi_device` - SPI Bus Device\n====================================================\n'
__version__='0.0.0-auto.0'
__repo__='https://github.com/adafruit/Adafruit_CircuitPython_BusDevice.git'
class SPIDevice:
	'\n    Represents a single SPI device and manages locking the bus and the device\n    address.\n\n    :param ~busio.SPI spi: The SPI bus the device is on\n    :param ~digitalio.DigitalInOut chip_select: The chip select pin object that implements the\n        DigitalInOut API.\n    :param int extra_clocks: The minimum number of clock cycles to cycle the bus after CS is high.\n        (Used for SD cards.)\n\n    .. note:: This class is **NOT** built into CircuitPython. See\n      :ref:`here for install instructions <bus_device_installation>`.\n\n    Example:\n\n    .. code-block:: python\n\n        import busio\n        import digitalio\n        from board import *\n        from adafruit_bus_device.spi_device import SPIDevice\n\n        with busio.SPI(SCK, MOSI, MISO) as spi_bus:\n            cs = digitalio.DigitalInOut(D10)\n            device = SPIDevice(spi_bus, cs)\n            bytes_read = bytearray(4)\n            # The object assigned to spi in the with statements below\n            # is the original spi_bus object. We are using the busio.SPI\n            # operations busio.SPI.readinto() and busio.SPI.write().\n            with device as spi:\n                spi.readinto(bytes_read)\n            # A second transaction\n            with device as spi:\n                spi.write(bytes_read)\n    '
	def __init__(A,spi,chip_select=None,*,baudrate=100000,polarity=0,phase=0,extra_clocks=0):
		A.spi=spi;A.baudrate=baudrate;A.polarity=polarity;A.phase=phase;A.extra_clocks=extra_clocks;A.chip_select=chip_select
		if A.chip_select:A.chip_select.switch_to_output(value=True)
	def __enter__(A):
		while not A.spi.try_lock():0
		A.spi.configure(baudrate=A.baudrate,polarity=A.polarity,phase=A.phase)
		if A.chip_select:A.chip_select.value=False
		return A.spi
	def __exit__(A,exc_type,exc_val,exc_tb):
		if A.chip_select:A.chip_select.value=True
		if A.extra_clocks>0:
			B=bytearray(1);B[0]=255;C=A.extra_clocks//8
			if A.extra_clocks%8!=0:C+=1
			for D in range(C):A.spi.write(B)
		A.spi.unlock();return False