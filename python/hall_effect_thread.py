import threading, serial, glob, time, random
import numpy as np

class hall_effect_thread(threading.Thread):

	def __init__(self, my_baud, my_ser_timeout, my_sample_freq_ref, my_speed_ref, my_torque_ref, my_time_ref):

		super().__init__(name="hall effect thread")

		# keep track of when thread it active
		self.active = threading.Event()

		# store passed in parameters
		self.baud = my_baud
		self.ser_timeout = my_ser_timeout
		self.sample_freq_ref = my_sample_freq_ref # Hz
		self.sample_freq = self.sample_freq_ref.get()
		self.sample_period = 1/self.sample_freq # s
		self.speed_ref = my_speed_ref
		self.torque_ref = my_torque_ref
		self.time_ref = my_time_ref

		# intialization of important variables
		self.ser_port = None
		self.init_time = 0
		self.handshake_wait_interval = 2 # seconds

		# Data rate
		self.arduino_data_rate = 200 # Hz
		self.arduino_data_period = 1/self.arduino_data_rate
		self.decimation_factor = int(self.arduino_data_rate/self.sample_freq)


	def start(self):

		print(super().getName() + " is starting.\n")
		self.active.set()
		super().start()


	def run(self):

		f = open('out.csv', 'w')
		self.init_time = time.time()
		self.time_ref.put(self.init_time)
		self.speed_ref.put(0)
		self.torque_ref.put(0)
		left_flywheel_rpm_vector = np.zeros(self.decimation_factor)

		"""
		while True:
			self.speed_ref.put(random.uniform(0,1400))
			self.torque_ref.put(random.uniform(0,50))
			self.time_ref.put(time.time()-self.init_time)
			time.sleep(20E-3)"""

		# loop forever until thread is terminated
		while self.active.isSet():

			# IMPORTANT: update time shared reference before reading serial so flotchart plotting isn't choppy
			self.time_ref.put(time.time()-self.init_time)

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
							ser_in = self.ser_port.readline().decode('ascii')[:-2]
							#print('serial from arduino ', ser_in)
							# check to see if the correct Arduino responded 
							if ser_in == 'hall_effect':
								# if it did, keep this serial port and stop looking at the others
								print('Successful handshake with hall effect arduino.')
								handshake_success = True
								break

						if handshake_success:
							print("Initialized hall effect arduino serial port at " + self.ser_port.name)
							self.ser_port.write('handshake_ok'.encode('ascii'))
							break
						else:
							self.ser_port.close()
							self.ser_port = None

			# only proceed if a serial port has been found
			else:

				# Read a line and 
				line_in = self.ser_port.readline()

				# only continue if the serial port did not timeout and successfully read a line
				if not line_in == b'' and not line_in == b'\n':
					#convert line from b'xxx\r\n' to xxx
					line = line_in.decode('utf-8')[:-1]
					#print("Raw Serial: ", line)

					formatted = self.parse_data(line)
					if not len(formatted) == 0:
						left_flywheel_rpm_vector[0] = formatted[0]/168*60/self.arduino_data_period
						# perform decimation with a moving average filter
						curr_rpm = (1/self.decimation_factor)*np.sum(left_flywheel_rpm_vector)
						self.speed_ref.put(curr_rpm)
						self.torque_ref.put(random.uniform(0,50))
						left_flywheel_rpm_vector[1:] = left_flywheel_rpm_vector[0:len(left_flywheel_rpm_vector)-1]

				else: 
					continue
				
		f.close()


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