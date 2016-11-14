import threading, serial, glob, time, random


class serial_thread(threading.Thread):

	def __init__(self, my_baud, my_ser_timeout, my_sample_freq, my_speed_ref, my_torque_ref, my_time_ref):

		super().__init__(name="serial thread")

		# keep track of when thread it active
		self.active = threading.Event()

		# store passed in parameters
		self.baud = my_baud
		self.ser_timeout = my_ser_timeout
		self.sample_freq = my_sample_freq # Hz
		self.sample_period = 1/my_sample_freq # s
		self.speed_ref = my_speed_ref
		self.torque_ref = my_torque_ref
		self.time_ref = my_time_ref

		# intialization of some variables (will be defined later)
		self.ser_port = None
		self.init_time = 0
		self.curr_time = 0

		# Arduino data rate
		self.arduino_data_rate = 5 # Hz
		self.arduino_data_period = 1/self.arduino_data_rate


	def start(self):

		print(super().getName() + " is starting.")
		self.active.set()
		super().start()


	def run(self):

		f = open('out.csv', 'w')
		self.init_time = time.time()
		self.curr_time = 0

		# loop forever until thread is terminated
		while self.active.isSet():

			# find a serial port if one hasn't been found yet
			if self.ser_port == None:
				port_name = self.find_serial_ports()
				if not(port_name == None):
					self.ser_port = serial.Serial(port_name, self.baud, timeout=self.ser_timeout)
					print("Initialized car's communication serial port at " + self.ser_port.name)

			# only proceed if a serial port has been found
			else:
				# Read a line and convert it from b'xxx\r\n' to xxx
				line = self.ser_port.readline().decode('utf-8')[:-1]
				#print("Raw Serial: ", line)

				# timestamp
				self.curr_time = time.time()-self.init_time

				formated = self.parse_data(line)
				if not len(formated) <= 0:
					left_flywheel_rpm = formated[0]/168*60/self.arduino_data_period

					self.speed_ref.put(left_flywheel_rpm)
					self.torque_ref.put(random.uniform(0,50))
					self.time_ref.put(self.curr_time)

					"""if formated:  # If it isn't a blank line
						for num in formated:
							print("RPM: {:.0f}".format((num/168*60)/.2))
						#print("RPM: %.1f" % (num/168*60)/.2)
						f.write("{}, {}\n".format(formated[0],formated[1]))"""

		f.close()


	def join(self):

		print(super().getName() + " thread is terminating.")
		self.active.clear()
		# close serial port, if one is active
		if not(self.ser_port == None):
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

		process_serial = None
		serial_port = None
		ports_avail = glob.glob('/dev/tty[A-Za-z]*')
		ser_port = None

		for port in ports_avail:
			try:
				serial_port = serial.Serial(port)
				serial_port.close()
				print("Serial port found: %s" % port)
				# we only want one serial port, so break if one is found
				ser_port = port
				break										
			#except (OSError, serial.SerialException):
			except:
				pass   

		return ser_port


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