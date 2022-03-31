_E='pipe number must be in range [0, 5]'
_D='pipe_number must be in range [0, 5]'
_C=True
_B=False
_A=None
import time
from micropython import const
from adafruit_bus_device.spi_device import SPIDevice
CONFIGURE=const(0)
AUTO_ACK=const(1)
OPEN_PIPES=const(2)
SETUP_RETR=const(4)
RF_PA_RATE=const(6)
RX_ADDR_P0=const(10)
TX_ADDRESS=const(16)
RX_PL_LENG=const(17)
DYN_PL_LEN=const(28)
TX_FEATURE=const(29)
def address_repr(addr):
	A=addr;B=''
	for C in range(len(A)-1,-1,-1):B+=(''if A[C]>15 else'0')+hex(A[C])[2:]
	return B
class RF24:
	def __init__(A,spi,csn,ce_pin,spi_frequency=10000000):
		A._spi=SPIDevice(spi,chip_select=csn,baudrate=spi_frequency,extra_clocks=8);A.ce_pin=ce_pin;A.ce_pin.switch_to_output(value=_B);A._status=0;A._config=14;A._reg_write(CONFIGURE,A._config)
		if A._reg_read(CONFIGURE)&3!=2:raise RuntimeError('nRF24L01 Hardware not responding')
		A._pipes=[bytearray(5),bytearray(5),195,196,197,198];A._open_pipes=0
		for B in range(6):
			if B<2:A._pipes[B]=A._reg_read_bytes(RX_ADDR_P0+B)
			else:A._pipes[B]=A._reg_read(RX_ADDR_P0+B)
		A._is_plus_variant=_B;D=A._reg_read(TX_FEATURE);A._reg_write(80,115);C=A._reg_read(TX_FEATURE)
		if D==C:A._is_plus_variant=_C
		if not C:A._reg_write(80,115)
		A._pipe0_read_addr=_A;A._tx_address=A._reg_read_bytes(TX_ADDRESS);A._retry_setup=83;A._rf_setup=7;A._dyn_pl=63;A._aa=63;A._features=5;A._channel=76;A._addr_len=5;A._pl_len=[32]*6
		with A:A.flush_rx();A.flush_tx();A.clear_status_flags()
	def __enter__(A):
		A.ce_pin.value=_B;A._reg_write(CONFIGURE,A._config&124);A._reg_write(RF_PA_RATE,A._rf_setup);A._reg_write(OPEN_PIPES,A._open_pipes);A._reg_write(DYN_PL_LEN,A._dyn_pl);A._reg_write(AUTO_ACK,A._aa);A._reg_write(TX_FEATURE,A._features);A._reg_write(SETUP_RETR,A._retry_setup)
		for (B,C) in enumerate(A._pipes):
			if B<2:A._reg_write_bytes(RX_ADDR_P0+B,C)
			else:A._reg_write(RX_ADDR_P0+B,C)
		A._reg_write_bytes(TX_ADDRESS,A._tx_address);A._reg_write(5,A._channel);A._reg_write(3,A._addr_len-2)
		for (B,D) in enumerate(A._pl_len):A.set_payload_length(D,B)
		return A
	def __exit__(A,*B):A.ce_pin.value=_B;A.power=_B;return _B
	def _reg_read(B,reg):
		C=bytes([reg,0]);A=bytearray([0,0])
		with B._spi as D:D.write_readinto(C,A)
		B._status=A[0];return A[1]
	def _reg_read_bytes(B,reg,buf_len=5):
		C=buf_len;A=bytearray(C+1);D=bytes([reg])+b'\x00'*C
		with B._spi as E:E.write_readinto(D,A)
		B._status=A[0];return A[1:]
	def _reg_write_bytes(B,reg,out_buf):
		A=out_buf;A=bytes([32|reg])+A;C=bytearray(len(A))
		with B._spi as D:D.write_readinto(A,C)
		B._status=C[0]
	def _reg_write(B,reg,value=_A):
		C=value;A=bytes([reg])
		if C is not _A:A=bytes([32|reg,C])
		D=bytearray(len(A))
		with B._spi as E:E.write_readinto(A,D)
		B._status=D[0]
	@property
	def address_length(self):return self._reg_read(3)+2
	@address_length.setter
	def address_length(self,length):
		A=length
		if not 3<=A<=5:raise ValueError('address_length can only be set in range [3, 5] bytes')
		self._addr_len=int(A);self._reg_write(3,A-2)
	def open_tx_pipe(A,address):
		B=address
		if A._aa&1:
			for (C,D) in enumerate(B):A._pipes[0][C]=D
			A._reg_write_bytes(RX_ADDR_P0,B)
		for (C,D) in enumerate(B):A._tx_address[C]=D
		A._reg_write_bytes(TX_ADDRESS,B)
	def close_rx_pipe(A,pipe_number):
		B=pipe_number
		if B<0 or B>5:raise IndexError(_E)
		A._open_pipes=A._reg_read(OPEN_PIPES)
		if not B:A._pipe0_read_addr=_A
		if A._open_pipes&1<<B:A._open_pipes=A._open_pipes&~(1<<B);A._reg_write(OPEN_PIPES,A._open_pipes)
	def open_rx_pipe(A,pipe_number,address):
		C=address;B=pipe_number
		if not 0<=B<=5:raise IndexError(_E)
		if not C:raise ValueError('address length cannot be 0')
		if B<2:
			if not B:A._pipe0_read_addr=C
			for (D,E) in enumerate(C):A._pipes[B][D]=E
			A._reg_write_bytes(RX_ADDR_P0+B,C)
		else:A._pipes[B]=C[0];A._reg_write(RX_ADDR_P0+B,C[0])
		A._open_pipes=A._reg_read(OPEN_PIPES)|1<<B;A._reg_write(OPEN_PIPES,A._open_pipes)
	@property
	def listen(self):return self.power and bool(self._config&1)
	@listen.setter
	def listen(self,is_rx):
		A=self;A.ce_pin.value=0
		if is_rx:
			if A._pipe0_read_addr is not _A and A._aa&1:
				for (B,C) in enumerate(A._pipe0_read_addr):A._pipes[0][B]=C
				A._reg_write_bytes(RX_ADDR_P0,A._pipe0_read_addr)
			elif A._pipe0_read_addr is _A:A.close_rx_pipe(0)
			A._config=A._config&252|3;A._reg_write(CONFIGURE,A._config);time.sleep(0.00015);A.clear_status_flags();A.ce_pin.value=1;time.sleep(0.00013)
		else:
			if A._features&6==6 and A._aa&A._dyn_pl&1:A.flush_tx()
			if A._aa&1:A._open_pipes|=1;A._reg_write(OPEN_PIPES,A._open_pipes)
			A._config=A._config&254|2;A._reg_write(CONFIGURE,A._config);time.sleep(0.00016)
	def available(A):return A.update()and A.pipe is not _A
	def any(A):
		if A.available():
			if A._features&4:return A._reg_read(96)
			return A._pl_len[A.pipe]
		return 0
	def read(A,length=_A):
		B=length;C=B if B is not _A else A.any()
		if not C:return _A
		D=A._reg_read_bytes(97,C);A.clear_status_flags(_C,_B,_B);return D
	def send(A,buf,ask_no_ack=_B,force_retry=0,send_only=_B):
		F=force_retry;E=ask_no_ack;D=buf;C=send_only;A.ce_pin.value=0
		if isinstance(D,(list,tuple)):
			B=[]
			for G in D:B.append(A.send(G,E,F,C))
			return B
		A.flush_tx()
		if not C and A.pipe is not _A:A.flush_rx()
		A.write(D,E)
		while not A._status&48:A.update()
		A.ce_pin.value=0;B=A.irq_ds
		if A.irq_df:
			for H in range(F):
				B=A.resend(C)
				if B is _A or B:break
		if A._status&96==96 and not C:B=A.read()
		return B
	@property
	def tx_full(self):return bool(self._status&1)
	@property
	def pipe(self):
		A=(self._status&14)>>1
		if A<=5:return A
		return _A
	@property
	def irq_dr(self):return bool(self._status&64)
	@property
	def irq_ds(self):return bool(self._status&32)
	@property
	def irq_df(self):return bool(self._status&16)
	def clear_status_flags(A,data_recv=_C,data_sent=_C,data_fail=_C):B=bool(data_recv)<<6|bool(data_sent)<<5|bool(data_fail)<<4;A._reg_write(7,B)
	def interrupt_config(A,data_recv=_C,data_sent=_C,data_fail=_C):A._config=A._reg_read(CONFIGURE)&15|(not data_recv)<<6;A._config|=(not data_fail)<<4|(not data_sent)<<5;A._reg_write(CONFIGURE,A._config)
	def _dump_pipes(A):
		print('TX address____________','0x'+address_repr(A.address()));A._open_pipes=A._reg_read(OPEN_PIPES)
		for B in range(6):
			C=A._open_pipes&1<<B;print('Pipe {} ({}) bound: {}'.format(B,' open 'if C else'closed','0x'+address_repr(A.address(B))))
			if C:print('\t\texpecting',A._pl_len[B],'byte static payloads')
	@property
	def is_plus_variant(self):return self._is_plus_variant
	@property
	def dynamic_payloads(self):A=self;A._dyn_pl=A._reg_read(DYN_PL_LEN);return A._dyn_pl
	@dynamic_payloads.setter
	def dynamic_payloads(self,enable):
		B=enable;A=self;A._features=A._reg_read(TX_FEATURE)
		if isinstance(B,bool):A._dyn_pl=63 if B else 0
		elif isinstance(B,int):A._dyn_pl=63&B
		elif isinstance(B,(list,tuple)):
			A._dyn_pl=A._reg_read(DYN_PL_LEN)
			for (C,D) in enumerate(B):
				if C<6 and D>=0:A._dyn_pl=A._dyn_pl&~(1<<C)|bool(D)<<C
		else:raise ValueError('dynamic_payloads: {} is an invalid input'%B)
		if A._dyn_pl:A._features=A._features&3|bool(A._dyn_pl)<<2;A._reg_write(TX_FEATURE,A._features)
		A._reg_write(DYN_PL_LEN,A._dyn_pl)
	def set_dynamic_payloads(A,enable,pipe_number=_A):
		C=enable;B=pipe_number
		if B is _A:A.dynamic_payloads=bool(C)
		elif 0<=B<=5:A._dyn_pl=A._reg_read(DYN_PL_LEN)&~(1<<B);A.dynamic_payloads=A._dyn_pl|bool(C)<<B
		else:raise IndexError(_D)
	def get_dynamic_payloads(B,pipe_number=0):
		A=pipe_number
		if 0<=A<=5:return bool(B.dynamic_payloads&1<<A)
		raise IndexError(_D)
	@property
	def payload_length(self):return self._pl_len[0]
	@payload_length.setter
	def payload_length(self,length):
		C=self;A=length
		if isinstance(A,int):A=[max(1,A)]*6
		elif not isinstance(A,(list,tuple)):raise ValueError('length {} is not a valid input'.format(A))
		for (B,D) in enumerate(A):
			if B<6 and D>0:C._pl_len[B]=min(32,D);C._reg_write(RX_PL_LENG+B,C._pl_len[B])
	def set_payload_length(A,length,pipe_number=_A):
		C=pipe_number;B=length
		if C is _A:A.payload_length=B
		else:A._pl_len[C]=max(1,min(32,B));A._reg_write(RX_PL_LENG+C,B)
	def get_payload_length(A,pipe_number=0):B=pipe_number;A._pl_len[B]=A._reg_read(RX_PL_LENG+B);return A._pl_len[B]
	@property
	def arc(self):A=self;A._retry_setup=A._reg_read(SETUP_RETR);return A._retry_setup&15
	@arc.setter
	def arc(self,count):B=count;A=self;B=max(0,min(int(B),15));A._retry_setup=A._retry_setup&240|B;A._reg_write(SETUP_RETR,A._retry_setup)
	@property
	def ard(self):A=self;A._retry_setup=A._reg_read(SETUP_RETR);return((A._retry_setup&240)>>4)*250+250
	@ard.setter
	def ard(self,delta):B=delta;A=self;B=max(250,min(B,4000));A._retry_setup=A._retry_setup&15|int((B-250)/250)<<4;A._reg_write(SETUP_RETR,A._retry_setup)
	def set_auto_retries(A,delay,count):B=delay;B=int((max(250,min(B,4000))-250)/250)<<4;A._retry_setup=B|max(0,min(int(count),15));A._reg_write(SETUP_RETR,A._retry_setup)
	def get_auto_retries(A):return A.ard,A._retry_setup&15
	@property
	def last_tx_arc(self):return self._reg_read(8)&15
	@property
	def auto_ack(self):A=self;A._aa=A._reg_read(AUTO_ACK);return A._aa
	@auto_ack.setter
	def auto_ack(self,enable):
		B=enable;A=self
		if isinstance(B,bool):A._aa=63 if B else 0
		elif isinstance(B,int):A._aa=63&B
		elif isinstance(B,(list,tuple)):
			for (C,D) in enumerate(B):
				A._aa=A._reg_read(AUTO_ACK)
				if C<6 and D>=0:A._aa=A._aa&~(1<<C)|bool(D)<<C
		else:raise ValueError('auto_ack: {} is not a valid input'%B)
		if bool(A._aa&1)!=bool(A._aa&62)and A._aa&62:A._aa|=1
		A._reg_write(AUTO_ACK,A._aa)
	def set_auto_ack(A,enable,pipe_number=_A):
		C=enable;B=pipe_number
		if B is _A:A.auto_ack=bool(C)
		elif 0<=B<=5:A._aa=A._reg_read(AUTO_ACK)&~(1<<B);A.auto_ack=A._aa|bool(C)<<B
		else:raise IndexError(_D)
	def get_auto_ack(A,pipe_number=0):
		B=pipe_number
		if 0<=B<=5:A._aa=A._reg_read(AUTO_ACK);return bool(A._aa&1<<B)
		raise IndexError(_D)
	@property
	def ack(self):A=self;A._aa=A._reg_read(AUTO_ACK);A._dyn_pl=A._reg_read(DYN_PL_LEN);A._features=A._reg_read(TX_FEATURE);return bool(A._features&6==6 and A._aa&A._dyn_pl&1)
	@ack.setter
	def ack(self,enable):
		B=enable;A=self
		if bool(B):A.set_auto_ack(_C,0);A._dyn_pl=A._dyn_pl&62|1;A._reg_write(DYN_PL_LEN,A._dyn_pl);A._features=A._features|4
		A._features=A._features&5|bool(B)<<1;A._reg_write(TX_FEATURE,A._features)
	def load_ack(A,buf,pipe_number):
		C=pipe_number;B=buf
		if C<0 or C>5:raise IndexError(_D)
		if not B or len(B)>32:raise ValueError('payload must have a byte length in range [1, 32]')
		if not bool(A._features&6==6 and A._aa&A._dyn_pl&1):A.ack=_C
		if not A.tx_full:A._reg_write_bytes(168|C,B);return _C
		return _B
	@property
	def allow_ask_no_ack(self):A=self;A._features=A._reg_read(TX_FEATURE);return bool(A._features&1)
	@allow_ask_no_ack.setter
	def allow_ask_no_ack(self,enable):A=self;A._features=A._features&6|bool(enable);A._reg_write(TX_FEATURE,A._features)
	@property
	def data_rate(self):A=self;A._rf_setup=A._reg_read(RF_PA_RATE);B=A._rf_setup&40;return(2 if B==8 else 250)if B else 1
	@data_rate.setter
	def data_rate(self,speed):
		B=self;A=speed
		if not A in(1,2,250):raise ValueError('data_rate must be 1 (Mbps), 2 (Mbps), or 250 (kbps)')
		if B.is_plus_variant and A==250:raise NotImplementedError('250 kbps data rate is not available for the non-plus variants of the nRF24L01 transceivers.')
		if B.data_rate!=A:A=0 if A==1 else 32 if A!=2 else 8;B._rf_setup=B._rf_setup&215|A;B._reg_write(RF_PA_RATE,B._rf_setup)
	@property
	def channel(self):return self._reg_read(5)
	@channel.setter
	def channel(self,channel):
		B=channel;A=self
		if not 0<=int(B)<=125:raise ValueError('channel can only be set in range [0, 125]')
		A._channel=int(B);A._reg_write(5,A._channel)
	@property
	def crc(self):
		A=self;A._config=A._reg_read(CONFIGURE);A._aa=A._reg_read(AUTO_ACK)
		if A._aa:return 2 if A._config&4 else 1
		return max(0,((A._config&12)>>2)-1)
	@crc.setter
	def crc(self,length):B=self;A=length;A=min(2,abs(int(A)));A=A+1<<2 if A else 0;B._config=B._config&115|A;B._reg_write(0,B._config)
	@property
	def power(self):A=self;A._config=A._reg_read(CONFIGURE);return bool(A._config&2)
	@power.setter
	def power(self,is_on):
		B=is_on;A=self;A._config=A._reg_read(CONFIGURE)
		if A.power!=bool(B):A._config=A._config&125|bool(B)<<1;A._reg_write(CONFIGURE,A._config);time.sleep(0.00016)
	@property
	def pa_level(self):A=self;A._rf_setup=A._reg_read(RF_PA_RATE);return(3-((A._rf_setup&6)>>1))*-6
	@pa_level.setter
	def pa_level(self,power):
		B=self;A=power;C=_C
		if isinstance(A,(list,tuple))and len(A)>1:C,A=bool(A[1]),int(A[0])
		if A not in(-18,-12,-6,0):raise ValueError('pa_level must be -18, -12, -6, or 0 (in dBm)')
		A=(3-int(A/-6))*2;B._rf_setup=B._rf_setup&248|A|C;B._reg_write(RF_PA_RATE,B._rf_setup)
	@property
	def is_lna_enabled(self):A=self;A._rf_setup=A._reg_read(RF_PA_RATE);return bool(A._rf_setup&1)
	def update(A):A._reg_write(255);return _C
	def resend(A,send_only=_B):
		C=send_only;B=_B
		if not A.fifo(_C,_C):
			A.ce_pin.value=0
			if not C and A.pipe is not _A:A.flush_rx()
			A.clear_status_flags();A._reg_write(227);A.ce_pin.value=1
			while not A._status&112:A.update()
			A.ce_pin.value=0;B=A.irq_ds
			if A._status&96==96 and not C:B=A.read()
		return B
	def write(A,buf,ask_no_ack=_B,write_only=_B):
		C=ask_no_ack;B=buf
		if not B or len(B)>32:raise ValueError('buffer must have a length in range [1, 32]')
		A.clear_status_flags()
		if A.tx_full:return _B
		if A._config&3!=2:A._config=A._reg_read(CONFIGURE)&124|2;A._reg_write(CONFIGURE,A._config);time.sleep(0.00016)
		if not bool(A._dyn_pl&1 and A._features&4):
			if len(B)<A._pl_len[0]:B+=b'\x00'*(A._pl_len[0]-len(B))
			elif len(B)>A._pl_len[0]:B=B[:A._pl_len[0]]
		if C and A._features&1==0:A._features=A._features&254|1;A._reg_write(TX_FEATURE,A._features)
		A._reg_write_bytes(160|bool(C)<<4,B)
		if not write_only:A.ce_pin.value=1
		return _C
	def flush_rx(A):A._reg_write(226)
	def flush_tx(A):A._reg_write(225)
	def fifo(D,about_tx=_B,check_empty=_A):
		B=check_empty;A=about_tx;C,A=D._reg_read(23),bool(A)
		if B is _A:return(C&(48 if A else 3))>>4*A
		return bool(C&2-bool(B)<<4*A)
	def address(B,index=-1):
		A=index
		if A>5:raise IndexError('index {} is out of bounds [0,5]'.format(A))
		if A<0:return B._tx_address
		if A<=1:return B._pipes[A]
		return bytes([B._pipes[A]])+B._pipes[1][1:]
	@property
	def rpd(self):return bool(self._reg_read(9))
	def start_carrier_wave(A):
		A.power=0;A.ce_pin.value=0;A.power=1;A.listen=0;A._rf_setup|=144;A._reg_write(RF_PA_RATE,A._rf_setup)
		if not A.is_plus_variant:
			A.auto_ack=_B;A._retry_setup=0;A._reg_write(SETUP_RETR,A._retry_setup);A._tx_address=bytearray([255]*5);A._reg_write_bytes(TX_ADDRESS,A._tx_address);A._reg_write_bytes(160,b'\xff'*32);A.crc=0;A.ce_pin.value=1;time.sleep(0.001);A.ce_pin.value=0
			while A._status&112:A.update()
			A._reg_write(23,64)
		A.ce_pin.value=1
	def stop_carrier_wave(A):A.ce_pin.value=0;A.power=0;A._rf_setup&=~ 144;A._reg_write(RF_PA_RATE,A._rf_setup)