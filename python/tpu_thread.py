import threading, serial, glob, time, random

class tpu_thread(threading.Thread):

	def __init__(self, my_baud, my_ser_timeout, my_rpm_unfilt_q):

		super().__init__(name="hall effect thread")

		# keep track of when thread it active
		self.active = threading.Event()

		# store passed in parameters
		self.baud = my_baud
		self.ser_timeout = my_ser_timeout
		self.rpm_unfilt_q = my_rpm_unfilt_q

		# intialization of important variables
		self.ser_port = None
		self.init_time = 0
		self.handshake_wait_interval = 2 # seconds

		# mechanical information
		self.revs_per_tooth = 1/168 # 168 teeth on flywheel


	def start(self):

		print(super().getName() + " is starting.")
		self.active.set()
		super().start()


	def run(self):

		self.init_time = time.time()
		self.rpm_unfilt_q.put(0)
		curr_rpm = 0
		prev_rpm = 0
		curr_time = 0
		prev_time = 0

		# loop forever until thread is terminated
		while self.active.isSet():
			
			# find a serial port if one hasn't been found yet
			if self.ser_port == None:
				# find all available serial ports in the file system
				port_names = self.find_serial_ports()
				if not(port_names == None):
					for port in port_names:
						print('Initializing',super().getName(), 'serial port at', port)
						# open the serial port under consideration
						self.ser_port = serial.Serial(port, self.baud, timeout=self.ser_timeout)
						# wait for Arduino to initialize its Serial stuff before handshaking
						time.sleep(2000E-3)
						# begin the handshake process with the Arduino
						self.ser_port.write('handshake_type\n'.encode('ascii'))
						print('Handshaking with hall effect arduino.')
						# wait for the Arduino to send back its type (eg, "hall_effect" or "peripheral_can")
						handshake_success = False
						handshake_wait_init = time.time()
						# only wait for handshaking to complete for a couple seconds 
						while time.time() - handshake_wait_init < self.handshake_wait_interval:
							ser_in = None
							try:
								ser_in = self.ser_port.readline().decode('ascii')[:-2]
							except:
								pass
							#print('serial from arduino ', ser_in)
							# check to see if the correct Arduino responded 
							if ser_in == 'hall_effect':
								# if it did, keep this serial port and stop looking at the others
								print('Successful handshake with hall effect arduino at '+self.ser_port.name)
								handshake_success = True
								break

						if handshake_success:
							self.ser_port.write('handshake_ok'.encode('ascii'))
							break
						else:
							self.ser_port.close()
							self.ser_port = None

			# only proceed if a serial port has been found
			else:

				# Read a line and 
				line_in = self.ser_port.readline()[:-1]

				# only continue if the serial port did not timeout and successfully read a line
				if not line_in == b'':
					# determine how many bytes were sent out from the TPU
					num_bytes = len(line_in)
					time_between_teeth_us = None
					# if one byte is sent, the value is < 256
					if num_bytes == 1:
						time_between_teeth_us = line_in[0]
					# if 2 bytes are sent, the value is 256 <= x < 65536
					elif num_bytes == 2:
						# bytes are sent big-endian, so large places come later
						time_between_teeth_us = (2**8)*line_in[0] + line_in[1]
					# if 2 bytes are sent, the value is 65536 <= x < 16,777,216
					elif num_bytes == 3:
						# bytes are sent big-endian, so large places come later
						time_between_teeth_us = (2**16)*line_in[0] + (2**8)*line_in[1] + line_in[2]

					# convert microseconds to seconds
					time_between_teeth_s = time_between_teeth_us/1E6
					# convert time between teeth to rpm
					curr_rpm = self.revs_per_tooth/time_between_teeth_s*60
					# update thread resources 
					self.rpm_unfilt_q.put(curr_rpm)
				# if the serial port expired before reading a line, assume current RPM is 0
				else: 
					self.rpm_unfilt_q.put(0)
					continue
				

	def join(self):

		print(super().getName() + " is terminating.")
		self.active.clear()

		if not(self.ser_port == None):
			# send out a message to the hall effect arduino to reboot itself
			self.ser_port.write('reboot_now\n'.encode('ascii'))
			print('Rebooting hall effect arduino.')
			# close serial port, if one is active
			self.ser_port.close()

		super().join(timeout=None)



	def scan_all(self):
		"""scan for available ports. prints out list, and returns a list of tuples (num, name)"""
		available = []
		for i in range(256):
			try:
				s = serial.Serial(i)
				available.append( (i, s.portstr))
				print ("(%d) %s" % (i, s.portstr))
				s.close()   # explicit close 'cause of delayed GC in java
			except serial.SerialException:
				pass
		return available


	def find_serial_ports(self):

		serial_port = None
		ports_avail = glob.glob('/dev/ttyA*')
		return ports_avail


	def is_int(self, num):
		try:
			int(num)
			return True
		except ValueError:
			return False
	  

	def parse_data(self, data):
		arr = data.split(";")
		if (len(arr) >= 2):
			if (len(arr[0]) > 1 and len(arr[1]) > 1):
				if ("L" == arr[0][0] and "R" == arr[1][0]):
					num1 = arr[0][1:]
					num2 = arr[1][1:]
					try:
						return [int(num1), int(num2)]
					except ValueError:
						pass
		return []